import unittest

from backend.app.validator import validate_analyst_report


def _transcript(*resident_lines: str) -> list[dict]:
    turns: list[dict] = []
    for line in resident_lines:
        turns.append({"role": "resident", "text": line})
    return turns


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


class ValidateReportTests(unittest.TestCase):
    def test_passive_report_passes_without_regex(self) -> None:
        transcript = _transcript(
            "Sometimes I wish I did not wake up.",
            "No plan. I will not do that.",
        )
        report = _minimal_report(
            passive_suicidal_thoughts=True,
            suicide_risk_flag=True,
            recommendation="visit_soon",
            estimate_confidence="low",
        )
        topics = list(report["transcript_topics"])
        for topic in topics:
            if topic["topic_id"] == "safety_check":
                topic.update(
                    {
                        "discussed": True,
                        "concern": True,
                        "evidence": "Sometimes I wish I did not wake up.",
                    }
                )
        report["transcript_topics"] = topics
        errors = validate_analyst_report(report, transcript)
        self.assertEqual(errors, [])

    def test_active_ideation_requires_urgent(self) -> None:
        report = _minimal_report(active_suicidal_ideation=True, recommendation="visit_soon")
        errors = validate_analyst_report(report, _transcript("I have pills in the drawer."))
        self.assertTrue(any("requires recommendation urgent" in e for e in errors))

    def test_urgent_without_safety_flag_fails(self) -> None:
        report = _minimal_report(recommendation="urgent")
        errors = validate_analyst_report(report, _transcript("Spirits okay this week."))
        self.assertTrue(any("urgent requires a safety flag" in e for e in errors))

    def test_urgent_with_safety_flag_passes(self) -> None:
        report = _minimal_report(
            recommendation="urgent",
            active_suicidal_ideation=True,
            suicide_risk_flag=True,
            estimate_confidence="low",
        )
        topics = list(report["transcript_topics"])
        for topic in topics:
            if topic["topic_id"] == "safety_check":
                topic.update(
                    {
                        "discussed": True,
                        "concern": True,
                        "evidence": "I have pills in the drawer.",
                    }
                )
        report["transcript_topics"] = topics
        errors = validate_analyst_report(report, _transcript("I have pills in the drawer."))
        self.assertEqual(errors, [])

    def test_evidence_must_be_in_transcript(self) -> None:
        report = _minimal_report()
        topics = list(report["transcript_topics"])
        topics[0] = {**topics[0], "concern": True, "evidence": "I never said this"}
        report["transcript_topics"] = topics
        errors = validate_analyst_report(report, _transcript("Hello there."))
        self.assertTrue(any("Evidence not found" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
