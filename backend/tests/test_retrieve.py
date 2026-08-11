import unittest



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





if __name__ == "__main__":

    unittest.main()

