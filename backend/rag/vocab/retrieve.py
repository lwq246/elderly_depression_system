"""Per-turn culture vocabulary retrieval for the companion.

Two lanes, unioned:
  * literal — exact alias match against the resident's utterance via an Aho-Corasick
    automaton built once per locale from the Chroma records. Finds all aliases in a single
    left-to-right pass: O(utterance length + matches), independent of glossary size. A
    word-boundary post-check keeps ``Asian`` from matching ``sian``. Deterministic;
    guarantees known dialect tokens are never ranked out.
  * semantic — cosine search over the locale slice for paraphrases with no shared token.
    OFF by default (``RAG_VOCAB_SEMANTIC``); on an English companion model it mostly
    re-teaches meanings the model already knows and adds noise.

Literal hits are always kept; when the semantic lane is enabled it fills the remainder up
to ``rag_vocab_top_k``. The result is formatted into a compact block injected at the END of
the companion prompt each turn, so the vocabulary stays salient regardless of session length.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from backend.app.config import settings
from backend.rag.query import query_collection
from backend.rag.store import get_vocab_collection


@dataclass(frozen=True)
class VocabTerm:
    canonical: str
    meaning: str


class Automaton:
    """Minimal Aho-Corasick multi-pattern matcher over lowercased alias strings.

    Patterns are added, then ``build()`` wires the failure/output links. ``iter(text)``
    yields ``(start, end, term)`` spans (end exclusive) for every alias occurrence,
    including overlaps — callers apply their own boundary / dedupe rules.
    """

    def __init__(self) -> None:
        self._goto: list[dict[str, int]] = [{}]
        self._fail: list[int] = [0]
        self._out: list[list[tuple[int, VocabTerm]]] = [[]]

    def _new_node(self) -> int:
        self._goto.append({})
        self._fail.append(0)
        self._out.append([])
        return len(self._goto) - 1

    def add(self, pattern: str, term: VocabTerm) -> None:
        if not pattern:
            return
        node = 0
        for ch in pattern:
            nxt = self._goto[node].get(ch)
            if nxt is None:
                nxt = self._new_node()
                self._goto[node][ch] = nxt
            node = nxt
        self._out[node].append((len(pattern), term))

    def build(self) -> None:
        q: deque[int] = deque()
        for nxt in self._goto[0].values():
            self._fail[nxt] = 0
            q.append(nxt)
        while q:
            r = q.popleft()
            for ch, u in self._goto[r].items():
                q.append(u)
                state = self._fail[r]
                while state and ch not in self._goto[state]:
                    state = self._fail[state]
                fail = self._goto[state].get(ch, 0)
                self._fail[u] = 0 if fail == u else fail
                self._out[u] = self._out[u] + self._out[self._fail[u]]

    def iter(self, text: str):
        node = 0
        for i, ch in enumerate(text):
            while node and ch not in self._goto[node]:
                node = self._fail[node]
            node = self._goto[node].get(ch, 0)
            for length, term in self._out[node]:
                yield i - length + 1, i + 1, term


@dataclass
class _LocaleIndex:
    automaton: Automaton | None


# Cache the literal index per locale for the process lifetime (rebuilt only on restart /
# re-ingest). Small and cheap; avoids re-reading the collection every turn.
_locale_index_cache: dict[str, _LocaleIndex] = {}


def _build_automaton(alias_to_term: dict[str, VocabTerm]) -> Automaton | None:
    if not alias_to_term:
        return None
    automaton = Automaton()
    for alias, term in alias_to_term.items():
        automaton.add(alias, term)
    automaton.build()
    return automaton


def _build_locale_index(locale: str) -> _LocaleIndex:
    collection = get_vocab_collection()
    try:
        if collection.count() == 0:
            return _LocaleIndex(automaton=None)
        result = collection.get(where={"locale": locale}, include=["metadatas"])
    except Exception:
        return _LocaleIndex(automaton=None)

    alias_to_term: dict[str, VocabTerm] = {}
    for meta in result.get("metadatas", []) or []:
        meta = meta or {}
        canonical = (meta.get("canonical") or "").strip()
        meaning = (meta.get("meaning") or "").strip()
        if not canonical:
            continue
        term = VocabTerm(canonical=canonical, meaning=meaning)
        aliases = [a for a in (meta.get("aliases") or "").split("|") if a.strip()]
        for alias in {canonical.lower(), *[a.lower() for a in aliases]}:
            alias_to_term.setdefault(alias, term)

    return _LocaleIndex(automaton=_build_automaton(alias_to_term))


def _get_locale_index(locale: str) -> _LocaleIndex:
    index = _locale_index_cache.get(locale)
    if index is None:
        index = _build_locale_index(locale)
        _locale_index_cache[locale] = index
    return index


def clear_cache() -> None:
    """Drop the cached literal indexes (call after re-ingesting vocabulary)."""
    _locale_index_cache.clear()


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _has_word_boundaries(text: str, start: int, end: int) -> bool:
    """Mirror the regex ``(?<!\\w) … (?!\\w)`` guard so ``Asian`` never matches ``sian``."""
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    return not (before and _is_word_char(before)) and not (after and _is_word_char(after))


def _literal_matches(locale: str, utterance: str) -> list[VocabTerm]:
    index = _get_locale_index(locale)
    if not index.automaton or not utterance.strip():
        return []
    text = utterance.lower()
    found: list[VocabTerm] = []
    seen: set[str] = set()
    for start, end, term in index.automaton.iter(text):
        if term.canonical in seen:
            continue
        if _has_word_boundaries(text, start, end):
            seen.add(term.canonical)
            found.append(term)
    return found


def _semantic_matches(locale: str, utterance: str, top_k: int) -> list[VocabTerm]:
    if not utterance.strip() or top_k <= 0:
        return []
    try:
        rows = query_collection(
            utterance,
            doc_type="culture_vocabulary",
            locale=locale,
            top_k=top_k,
        )
    except Exception:
        return []
    terms: list[VocabTerm] = []
    for row in rows:
        meta = row.get("metadata") or {}
        canonical = (meta.get("canonical") or "").strip()
        if not canonical:
            continue
        terms.append(VocabTerm(canonical=canonical, meaning=(meta.get("meaning") or "").strip()))
    return terms


def retrieve_relevant_vocab(
    locale: str,
    utterance: str,
    *,
    top_k: int | None = None,
) -> list[VocabTerm]:
    """Literal alias matches unioned with semantic matches, deduped by canonical term."""
    k = top_k if top_k is not None else settings.rag_vocab_top_k
    literal = _literal_matches(locale, utterance)

    merged: list[VocabTerm] = []
    seen: set[str] = set()
    for term in literal:  # literal always kept, even if it exceeds k
        if term.canonical not in seen:
            seen.add(term.canonical)
            merged.append(term)

    remaining = max(k - len(merged), 0)
    if remaining and settings.rag_vocab_semantic:
        for term in _semantic_matches(locale, utterance, remaining + len(seen)):
            if term.canonical in seen:
                continue
            seen.add(term.canonical)
            merged.append(term)
            if len(merged) >= k:
                break
    return merged


def retrieve_vocab_for_analyst(locale: str, transcript_text: str) -> list[VocabTerm]:
    """Literal-only vocab retrieval over the full transcript for the analyst-exit pass.

    Runs a single Aho-Corasick pass over the concatenated resident text and returns every
    known alias that was actually spoken, deduped by canonical term. Intentionally excludes
    the semantic lane and applies no ``top_k`` cap: the analyst wants complete coverage of the
    terms the resident used (to interpret them), not paraphrase expansion. Cheap and stateless
    — no embeddings, no network — so there is nothing worth caching from the companion.
    """
    return _literal_matches(locale, transcript_text)


def format_vocab_block(terms: list[VocabTerm]) -> str:
    if not terms:
        return ""
    lines = ["Local terms the resident may be using right now (understand, do not force):"]
    for term in terms:
        lines.append(f"- {term.canonical} — {term.meaning}" if term.meaning else f"- {term.canonical}")
    return "\n".join(lines)
