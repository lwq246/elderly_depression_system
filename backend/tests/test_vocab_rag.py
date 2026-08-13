import unittest

from backend.rag.vocab import retrieve as vocab_retrieve
from backend.rag.vocab.parse import parse_vocabulary_markdown
from backend.rag.vocab.retrieve import (
    VocabTerm,
    _LocaleIndex,
    format_vocab_block,
    retrieve_relevant_vocab,
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
