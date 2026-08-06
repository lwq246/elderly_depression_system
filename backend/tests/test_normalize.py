import unittest

from backend.app.validator import (
    evidence_in_transcript,
    format_transcript_for_analyst,
    is_evidence_ref,
    resolve_evidence_refs,
    validate_analyst_report,
)
from backend.rag.vocab.normalize import normalize_resident_text


def _minimal_report(**overrides) -> dict:
    topics = [
        {
            "topic_id": topic_id,
            "label": topic_id,
            "concern": False,
            "evidence": "",
            "discussed": False,
        }
        for topic_id in [
            "mood_spirits",
            "interest_activities",
            "energy",
            "meals_appetite",
            "sleep_rest",
            "social_connection",
            "emotional_weight",
            "safety_check",
            "coping_strengths",
        ]
    ]
    report = {
        "estimate_confidence": "low",
        "suicide_risk_flag": False,
        "passive_suicidal_thoughts": False,
        "active_suicidal_ideation": False,
        "transcript_topics": topics,
        "indicators": [],
        "explanation": "Test report.",
        "recommendation": "none",
    }
    report.update(overrides)
    return report


class NormalizeResidentTextTests(unittest.TestCase):
    def test_replaces_sg_culture_terms(self) -> None:
        raw = "Very sian lately, buay tahan already."
        normalized = normalize_resident_text(raw, "en-SG")
        self.assertIn("low mood", normalized.lower())
        self.assertIn("overwhelmed", normalized.lower())
        self.assertNotIn("sian", normalized.lower())
        self.assertNotIn("buay tahan", normalized.lower())

    def test_replaces_au_culture_terms(self) -> None:
        raw = "Been a bit flat and crook this week."
        normalized = normalize_resident_text(raw, "en-AU")
        self.assertIn("low mood", normalized.lower())
        self.assertIn("unwell", normalized.lower())
        self.assertNotIn("flat", normalized.lower())
        self.assertNotIn("crook", normalized.lower())

    def test_longest_phrase_wins(self) -> None:
        raw = "Feeling a bit flat today."
        normalized = normalize_resident_text(raw, "en-AU")
        self.assertIn("low mood", normalized.lower())
        self.assertNotIn("bit flat", normalized.lower())

    def test_unknown_locale_returns_unchanged(self) -> None:
        raw = "Hello there."
        self.assertEqual(normalize_resident_text(raw, "en-XX"), raw)


class FormatTranscriptForAnalystTests(unittest.TestCase):
    def test_labels_resident_lines_with_normalized_text(self) -> None:
        transcript = [
            {"role": "companion", "text": "How are you?"},
            {
                "role": "resident",
                "text": "Very sian lately.",
                "text_normalized": "Very low mood lately.",
            },
        ]
        formatted = format_transcript_for_analyst(transcript)
        self.assertIn("**Companion:** How are you?", formatted)
        self.assertIn("**Resident [R1]:** Very low mood lately.", formatted)
        self.assertNotIn("verbatim", formatted)
        self.assertNotIn("sian", formatted)

    def test_numbers_multiple_resident_turns(self) -> None:
        transcript = [
            {"role": "resident", "text": "Hello there."},
            {"role": "companion", "text": "Thanks for sharing."},
            {"role": "resident", "text": "Sleep is poor."},
        ]
        formatted = format_transcript_for_analyst(transcript)
        self.assertIn("**Resident [R1]:** Hello there.", formatted)
        self.assertIn("**Resident [R2]:** Sleep is poor.", formatted)

    def test_evidence_checks_raw_text_only(self) -> None:
        transcript = [
            {
                "role": "resident",
                "text": "Very sian lately.",
                "text_normalized": "Very low mood lately.",
            }
        ]
        self.assertTrue(evidence_in_transcript("Very sian lately.", transcript))
        self.assertFalse(evidence_in_transcript("Very low mood lately.", transcript))


class ResolveEvidenceRefTests(unittest.TestCase):
    def test_is_evidence_ref(self) -> None:
        self.assertTrue(is_evidence_ref("R1"))
        self.assertTrue(is_evidence_ref("[R2]"))
        self.assertTrue(is_evidence_ref(" r3 "))
        self.assertFalse(is_evidence_ref("Very sian lately."))

    def test_resolve_replaces_ref_with_raw_line(self) -> None:
        transcript = [
            {
                "role": "resident",
                "text": "Very sian lately.",
                "text_normalized": "Very low mood lately.",
            }
        ]
        report = _minimal_report()
        topics = list(report["transcript_topics"])
        topics[0] = {**topics[0], "discussed": True, "concern": True, "evidence": "R1"}
        report["transcript_topics"] = topics

        errors = resolve_evidence_refs(report, transcript)
        self.assertEqual(errors, [])
        self.assertEqual(topics[0]["evidence"], "Very sian lately.")
        self.assertEqual(validate_analyst_report(report, transcript), [])

    def test_invalid_ref_returns_error(self) -> None:
        transcript = [{"role": "resident", "text": "Hello there."}]
        report = _minimal_report()
        topics = list(report["transcript_topics"])
        topics[0] = {**topics[0], "discussed": True, "concern": True, "evidence": "R9"}
        report["transcript_topics"] = topics

        errors = resolve_evidence_refs(report, transcript)
        self.assertEqual(errors, ["Invalid evidence reference: R9"])
        self.assertEqual(topics[0]["evidence"], "R9")


if __name__ == "__main__":
    unittest.main()
