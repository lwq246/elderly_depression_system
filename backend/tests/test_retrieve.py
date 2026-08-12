import unittest

from backend.app.skills import load_companion_system_prompt
from backend.rag.vocab.normalize import normalize_resident_text
from backend.rag.vocab.retrieve import (

    _term_in_resident_text,

    retrieve_vocabulary_for_companion,

)





class TestTermInResidentText(unittest.TestCase):

    def test_matches_substring_case_insensitive(self):

        self.assertTrue(_term_in_resident_text("crook", "I feel crook today"))

        self.assertTrue(_term_in_resident_text("bit blue", "Been a bit blue lately"))



    def test_rejects_term_not_in_message(self):

        self.assertFalse(_term_in_resident_text("flat", "I feel crook today"))

        self.assertFalse(_term_in_resident_text("crook", ""))





class TestRetrieveVocabularyLiteral(unittest.TestCase):

    def test_finds_terms_in_message_en_au(self):

        rows = retrieve_vocabulary_for_companion("I feel crook today", locale="en-AU")

        terms = {(r.get("metadata") or {}).get("term") for r in rows}

        self.assertIn("feel crook", terms)
        self.assertNotIn("crook", terms)



    def test_finds_longest_phrase_en_au(self):

        rows = retrieve_vocabulary_for_companion("A bit flat lately", locale="en-AU")

        terms = [(r.get("metadata") or {}).get("term") for r in rows]

        self.assertIn("a bit flat", terms)



    def test_long_sg_ramble_finds_all_culture_terms(self):

        text = (

            "At night cannot sleep also, sleep very poor until morning still no strength. "

            "Everything buay tahan lately, very sian."

        )

        rows = retrieve_vocabulary_for_companion(text, locale="en-SG", top_k=20)

        terms = {(r.get("metadata") or {}).get("term") for r in rows}

        self.assertTrue(
            {"cannot sleep also", "sleep very poor", "no strength", "buay tahan", "very sian"} <= terms
        )
        self.assertNotIn("sian", terms)
        self.assertNotIn("cannot sleep", terms)



    def test_drops_shorter_term_when_contained_in_longer_match(self):
        rows = retrieve_vocabulary_for_companion("Very sian lately", locale="en-SG")
        terms = [(r.get("metadata") or {}).get("term") for r in rows]
        self.assertIn("very sian", terms)
        self.assertNotIn("sian", terms)

    def test_keeps_shorter_term_when_it_stands_alone(self):
        rows = retrieve_vocabulary_for_companion("I feel sian", locale="en-SG")
        terms = {(r.get("metadata") or {}).get("term") for r in rows}
        self.assertEqual(terms, {"sian"})

    def test_wrong_locale_not_retrieved(self):
        rows = retrieve_vocabulary_for_companion("I feel crook today", locale="en-SG")
        terms = {(r.get("metadata") or {}).get("term") for r in rows}
        self.assertNotIn("crook", terms)


class TestBoundaryFalsePositives(unittest.TestCase):
    """Word-boundary matching must not fire on terms embedded inside larger words."""

    def _terms(self, text: str, locale: str) -> set[str]:
        rows = retrieve_vocabulary_for_companion(text, locale=locale, top_k=20)
        return {(r.get("metadata") or {}).get("term") for r in rows}

    def test_sian_not_matched_inside_asian(self):
        self.assertNotIn("sian", self._terms("My daughter married an Asian man", "en-SG"))

    def test_wind_not_matched_inside_window(self):
        self.assertNotIn("wind", self._terms("Please open the window", "en-SG"))

    def test_loya_not_matched_inside_loyal(self):
        self.assertNotIn("loya", self._terms("He is a loyal friend", "en-SG"))

    def test_diam_not_matched_inside_diamond(self):
        self.assertNotIn("diam", self._terms("She lost her diamond ring", "en-SG"))

    def test_standalone_term_still_matches(self):
        self.assertIn("sian", self._terms("I feel sian today", "en-SG"))
        self.assertIn("wind", self._terms("Too much wind today", "en-SG"))

    def test_normalize_does_not_touch_embedded_word(self):
        self.assertEqual(
            normalize_resident_text("She lost her diamond ring", "en-SG"),
            "She lost her diamond ring",
        )
        self.assertIn("withdrawal", normalize_resident_text("He keep diam only", "en-SG").lower())


class TestCompanionPromptVocab(unittest.TestCase):
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

