import unittest

from backend.app.skills import load_companion_system_prompt
from backend.rag.vocab.chunking import build_vocabulary_chunks, chunk_local_vocabulary, vocab_embedding_input


class TestVocabChunking(unittest.TestCase):
    def test_chunk_sg_vocabulary_term_rows_only(self):
        chunks = chunk_local_vocabulary(source="culture-vocabulary/en-SG", locale="en-SG")
        for chunk in chunks:
            self.assertIn("term", chunk.get("metadata") or {})
        self.assertGreaterEqual(len(chunks), 50)

    def test_chunk_sg_vocabulary_has_sian_term(self):
        chunks = chunk_local_vocabulary(source="culture-vocabulary/en-SG", locale="en-SG")
        terms = {(c.get("metadata") or {}).get("term") for c in chunks}
        self.assertIn("sian", terms)
        self.assertIn("buay tahan", terms)
        self.assertGreaterEqual(len(chunks), 10)
        sian = next(c for c in chunks if (c.get("metadata") or {}).get("term") == "sian")
        self.assertEqual(vocab_embedding_input(sian), "sian")
        self.assertEqual(sian["text"], "low mood")
        self.assertNotIn("meaning", sian.get("metadata") or {})

        heaty = next(c for c in chunks if (c.get("metadata") or {}).get("term") == "heaty")
        self.assertEqual(heaty["text"], "unwell")

        no_strength = next(c for c in chunks if (c.get("metadata") or {}).get("term") == "no strength")
        self.assertEqual(no_strength["text"], "fatigue")

    def test_chunk_au_vocabulary_has_crook(self):
        chunks = chunk_local_vocabulary(source="culture-vocabulary/en-AU", locale="en-AU")
        terms = {(c.get("metadata") or {}).get("term") for c in chunks}
        self.assertIn("crook", terms)
        self.assertIn("bit blue", terms)
        self.assertIn("doing it tough", terms)
        self.assertGreaterEqual(len(chunks), 50)
        crook = next(c for c in chunks if (c.get("metadata") or {}).get("term") == "crook")
        self.assertEqual(crook["text"], "unwell")

    def test_build_vocabulary_chunks_both_locales(self):
        chunks = build_vocabulary_chunks()
        locales = {(c.get("metadata") or {}).get("locale") for c in chunks}
        self.assertIn("en-SG", locales)
        self.assertIn("en-AU", locales)

    def test_companion_prompt_without_static_vocab(self):
        prompt = load_companion_system_prompt("en-SG")
        self.assertNotIn("## Local vocabulary reference", prompt)
        self.assertNotIn("## Retrieved local vocabulary (this turn)", prompt)

    def test_companion_prompt_with_rag_context(self):
        prompt = load_companion_system_prompt(
            "en-SG",
            vocabulary_context="### Vocabulary 1 — sian\nsian → low mood",
        )
        self.assertIn("Retrieved local vocabulary", prompt)
        self.assertIn("sian", prompt)


if __name__ == "__main__":
    unittest.main()
