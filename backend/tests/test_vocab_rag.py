import unittest

from backend.rag.vocab import retrieve as vocab_retrieve
from backend.rag.vocab.parse import parse_vocabulary_markdown
from backend.rag.vocab.retrieve import (
    VocabTerm,
    _LocaleIndex,
    format_vocab_block,
    retrieve_relevant_vocab,
    retrieve_vocab_for_analyst,
)

SAMPLE_MD = """# Local vocabulary — test

## Policy: mirror-first

| Mode | When | Behaviour |
|------|------|-----------|
| standard | default | plain English |

## Words residents often use (wellbeing screening)

| They may say | Meaning | You reflect |
|--------------|---------|-------------|
| **crook** | unwell, low | "You've been feeling crook." |
| **knackered** / **worn out** / **buggered** (mild) | exhausted | "You feel worn out." |
| **she'll be right** | minimising | Reflect without arguing |

## Respectful address

| Term | Use |
|------|-----|
| **Mate** | avoid unless used first |
"""


class TestVocabParser(unittest.TestCase):
    def setUp(self):
        self.records = parse_vocabulary_markdown(SAMPLE_MD, "en-AU")
        self.by_canonical = {r.canonical: r for r in self.records}

    def test_only_glossary_sections_parsed(self):
        # Policy/address tables are skipped; only the 3 glossary rows are records.
        self.assertEqual(len(self.records), 3)
        self.assertIn("crook", self.by_canonical)
        self.assertNotIn("standard", self.by_canonical)
        self.assertNotIn("Mate", self.by_canonical)

    def test_alias_splitting_and_parenthetical_strip(self):
        rec = self.by_canonical["knackered"]
        self.assertEqual(rec.aliases, ["knackered", "worn out", "buggered"])
        self.assertEqual(rec.meaning, "exhausted")

    def test_metadata_and_ids(self):
        rec = self.by_canonical["crook"]
        meta = rec.metadata()
        self.assertEqual(meta["locale"], "en-AU")
        self.assertEqual(meta["canonical"], "crook")
        self.assertEqual(meta["aliases"], "crook")
        self.assertTrue(rec.id.startswith("en-AU::"))
        # embed_text carries canonical + aliases + meaning for semantic recall.
        self.assertIn("exhausted", self.by_canonical["knackered"].embed_text)


class TestLiteralMatching(unittest.TestCase):
    def _install_index(self):
        crook = VocabTerm("crook", "unwell, low")
        worn = VocabTerm("knackered", "exhausted")
        alias_to_term = {
            "crook": crook,
            "knackered": worn,
            "worn out": worn,
            "she'll be right": VocabTerm("she'll be right", "minimising"),
        }
        vocab_retrieve._locale_index_cache.clear()
        index = _LocaleIndex(automaton=vocab_retrieve._build_automaton(alias_to_term))
        vocab_retrieve._locale_index_cache["en-AU"] = index

    def test_word_boundary_no_false_positive(self):
        self._install_index()
        # "crook" must not match inside "crooked".
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", "the path is crooked"), [])
        # "sian"-style substring guard: alias inside a longer word must not fire.
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", "crookery aside"), [])

    def test_multiword_and_alias_resolution(self):
        self._install_index()
        got = vocab_retrieve._literal_matches("en-AU", "I'm a bit crook and worn out")
        # "worn out" resolves to canonical "knackered"; deduped by canonical.
        self.assertEqual({t.canonical for t in got}, {"crook", "knackered"})

    def test_apostrophe_multiword_alias(self):
        self._install_index()
        got = vocab_retrieve._literal_matches("en-AU", "no worries, she'll be right mate")
        self.assertEqual([t.canonical for t in got], ["she'll be right"])


class TestAhoCorasickEdgeCases(unittest.TestCase):
    """Boundary / overlap / normalisation behaviour of the literal automaton."""

    def _install(self, alias_to_term):
        vocab_retrieve._locale_index_cache.clear()
        index = _LocaleIndex(automaton=vocab_retrieve._build_automaton(alias_to_term))
        vocab_retrieve._locale_index_cache["en-AU"] = index

    def test_suffix_overlap_she_does_not_emit_he(self):
        # "he" is a suffix of "she"; the automaton's output link surfaces both, but the
        # word-boundary guard must drop the embedded "he".
        self._install({"he": VocabTerm("he", "m"), "she": VocabTerm("she", "f")})
        self.assertEqual(
            [t.canonical for t in vocab_retrieve._literal_matches("en-AU", "she is tired")],
            ["she"],
        )
        # A real standalone "he" still matches.
        self.assertEqual(
            [t.canonical for t in vocab_retrieve._literal_matches("en-AU", "he is here")],
            ["he"],
        )

    def test_case_insensitive(self):
        self._install({"crook": VocabTerm("crook", "unwell")})
        self.assertEqual(
            [t.canonical for t in vocab_retrieve._literal_matches("en-AU", "Feeling CROOK today")],
            ["crook"],
        )

    def test_punctuation_is_a_boundary(self):
        self._install({"crook": VocabTerm("crook", "unwell")})
        for utt in ("i feel crook.", "crook, really", "(crook)", "crook"):
            self.assertEqual(
                [t.canonical for t in vocab_retrieve._literal_matches("en-AU", utt)],
                ["crook"],
                msg=utt,
            )

    def test_start_and_end_of_string(self):
        self._install({"crook": VocabTerm("crook", "unwell")})
        self.assertEqual(
            [t.canonical for t in vocab_retrieve._literal_matches("en-AU", "crook")], ["crook"]
        )

    def test_repeated_occurrences_deduped(self):
        self._install({"crook": VocabTerm("crook", "unwell")})
        self.assertEqual(
            [t.canonical for t in vocab_retrieve._literal_matches("en-AU", "crook crook crook")],
            ["crook"],
        )

    def test_embedded_substring_rejected(self):
        self._install({"sian": VocabTerm("sian", "low mood")})
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", "an Asian meal"), [])

    def test_empty_and_whitespace(self):
        self._install({"crook": VocabTerm("crook", "unwell")})
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", ""), [])
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", "   "), [])

    def test_no_automaton_returns_empty(self):
        vocab_retrieve._locale_index_cache.clear()
        vocab_retrieve._locale_index_cache["en-AU"] = _LocaleIndex(automaton=None)
        self.assertEqual(vocab_retrieve._literal_matches("en-AU", "feeling crook"), [])


class TestAnalystTranscriptRetrieval(unittest.TestCase):
    """retrieve_vocab_for_analyst: literal-only, whole-transcript, semantic never invoked."""

    def _install(self, alias_to_term):
        vocab_retrieve._locale_index_cache.clear()
        index = _LocaleIndex(automaton=vocab_retrieve._build_automaton(alias_to_term))
        vocab_retrieve._locale_index_cache["en-AU"] = index

    def test_collects_all_spoken_terms_across_transcript(self):
        worn = VocabTerm("knackered", "exhausted")
        self._install(
            {
                "crook": VocabTerm("crook", "unwell"),
                "knackered": worn,
                "worn out": worn,
                "sian": VocabTerm("sian", "low mood"),
            }
        )
        transcript_text = "I feel crook today\nreally worn out\nand a bit crook again"
        got = retrieve_vocab_for_analyst("en-AU", transcript_text)
        self.assertEqual({t.canonical for t in got}, {"crook", "knackered"})

    def test_semantic_lane_never_invoked_even_when_flag_on(self):
        self._install({"crook": VocabTerm("crook", "unwell")})

        def _boom(*a, **k):  # pragma: no cover - must never run
            raise AssertionError("semantic lane must not run for the analyst pass")

        orig_sem = vocab_retrieve._semantic_matches
        orig_flag = vocab_retrieve.settings.rag_vocab_semantic
        vocab_retrieve._semantic_matches = _boom
        vocab_retrieve.settings.rag_vocab_semantic = True
        try:
            got = retrieve_vocab_for_analyst("en-AU", "feeling crook")
        finally:
            vocab_retrieve._semantic_matches = orig_sem
            vocab_retrieve.settings.rag_vocab_semantic = orig_flag
        self.assertEqual([t.canonical for t in got], ["crook"])


class TestMergeAndFormat(unittest.TestCase):
    def _patch_lanes(self, lit, sem):
        self._orig_lit = vocab_retrieve._literal_matches
        self._orig_sem = vocab_retrieve._semantic_matches
        vocab_retrieve._literal_matches = lambda loc, utt: lit
        vocab_retrieve._semantic_matches = lambda loc, utt, k: sem

    def _restore_lanes(self):
        vocab_retrieve._literal_matches = self._orig_lit
        vocab_retrieve._semantic_matches = self._orig_sem

    def test_literal_always_kept_semantic_fills_remainder_when_enabled(self):
        vocab_retrieve._locale_index_cache.clear()
        lit = [VocabTerm("crook", "unwell")]
        sem = [VocabTerm("crook", "unwell"), VocabTerm("flat", "low mood"), VocabTerm("yarn", "chat")]
        self._patch_lanes(lit, sem)
        orig_flag = vocab_retrieve.settings.rag_vocab_semantic
        vocab_retrieve.settings.rag_vocab_semantic = True
        try:
            terms = retrieve_relevant_vocab("en-AU", "feeling crook", top_k=2)
        finally:
            vocab_retrieve.settings.rag_vocab_semantic = orig_flag
            self._restore_lanes()
        canon = [t.canonical for t in terms]
        self.assertEqual(canon[0], "crook")  # literal first
        self.assertNotIn("crook", canon[1:])  # deduped
        self.assertEqual(len(terms), 2)  # capped at top_k

    def test_semantic_off_returns_literal_only(self):
        vocab_retrieve._locale_index_cache.clear()
        lit = [VocabTerm("crook", "unwell")]
        sem = [VocabTerm("flat", "low mood"), VocabTerm("yarn", "chat")]
        self._patch_lanes(lit, sem)
        orig_flag = vocab_retrieve.settings.rag_vocab_semantic
        vocab_retrieve.settings.rag_vocab_semantic = False
        try:
            terms = retrieve_relevant_vocab("en-AU", "feeling crook", top_k=5)
        finally:
            vocab_retrieve.settings.rag_vocab_semantic = orig_flag
            self._restore_lanes()
        # Flag off: no padding from the semantic lane, only the literal hit.
        self.assertEqual([t.canonical for t in terms], ["crook"])

    def test_format_block(self):
        block = format_vocab_block([VocabTerm("sian", "bored, low mood")])
        self.assertIn("Local terms", block)
        self.assertIn("- sian — bored, low mood", block)
        self.assertEqual(format_vocab_block([]), "")


if __name__ == "__main__":
    unittest.main()
