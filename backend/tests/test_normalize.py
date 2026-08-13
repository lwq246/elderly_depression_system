import unittest

from backend.app.validator import (
    evidence_in_transcript,
    format_transcript_for_analyst,
    is_evidence_ref,
    resolve_evidence_refs,
    validate_analyst_report,
)


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


class FormatTranscriptForAnalystTests(unittest.TestCase):
    def test_labels_resident_lines_with_raw_text(self) -> None:
        transcript = [
            {"role": "companion", "text": "How are you?"},
            {
                "role": "resident",
                "text": "Very sian lately.",
                "vocab_matches": [{"term": "sian", "meaning": "Low mood; tired of things."}],
            },
        ]
        formatted = format_transcript_for_analyst(transcript)
        self.assertIn("**Companion:** How are you?", formatted)
        self.assertIn("**Resident [R1]:** Very sian lately.", formatted)
        # Per-turn vocab notes are no longer inlined — the full glossary lives in the analyst
        # system prompt instead. Any vocab_matches stored on a turn must not leak into the text.
        self.assertNotIn("Local vocabulary (matched this turn):", formatted)
        self.assertNotIn("sian \u2192 Low mood", formatted)

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
                "vocab_matches": [{"term": "sian", "meaning": "Low mood; tired of things."}],
            }
        ]
        self.assertTrue(evidence_in_transcript("Very sian lately.", transcript))
        self.assertFalse(evidence_in_transcript("Low mood; tired of things.", transcript))


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
                "vocab_matches": [{"term": "sian", "meaning": "Low mood; tired of things."}],
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
