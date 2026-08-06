import unittest
from unittest.mock import patch

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


class TestRetrieveVocabularyFilter(unittest.TestCase):
    @patch("backend.rag.vocab.retrieve.retrieve_vocabulary_chroma_hits")
    def test_cosine_hits_filtered_to_terms_in_message(self, mock_chroma):
        mock_chroma.return_value = [
            {
                "text": "low mood",
                "metadata": {"term": "flat", "locale": "en-AU"},
                "cosine_similarity": 0.9,
            },
            {
                "text": "unwell",
                "metadata": {"term": "crook", "locale": "en-AU"},
                "cosine_similarity": 0.8,
            },
        ]

        rows = retrieve_vocabulary_for_companion("I feel crook today", locale="en-AU")

        terms = {(r.get("metadata") or {}).get("term") for r in rows}
        self.assertEqual(terms, {"crook"})

    @patch("backend.rag.vocab.retrieve.retrieve_vocabulary_chroma_hits")
    def test_low_similarity_chroma_hits_included_when_in_text(self, mock_chroma):
        mock_chroma.return_value = [
            {
                "text": "low mood",
                "metadata": {"term": "flat", "locale": "en-AU"},
                "cosine_similarity": 0.17,
            },
        ]

        rows = retrieve_vocabulary_for_companion("A bit flat lately", locale="en-AU")

        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0].get("metadata") or {}).get("term"), "flat")
        self.assertEqual(rows[0]["cosine_similarity"], 0.17)


if __name__ == "__main__":
    unittest.main()
