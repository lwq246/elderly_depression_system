import unittest

from backend.app.companion import generate_companion_reply
from backend.app.safety import text_signals_safety_risk


class TestSafetyDetection(unittest.TestCase):
    def test_curly_apostrophe_wake_up(self):
        spoken = "I just lie there and think I wouldn\u2019t mind if I didn\u2019t wake up."
        self.assertTrue(text_signals_safety_risk(spoken))

    def test_wasnt_here(self):
        self.assertTrue(text_signals_safety_risk("I think I wouldn't mind if I wasn't here."))

    def test_denial_still_false(self):
        self.assertFalse(text_signals_safety_risk("No, I do not wish to hurt myself."))


class TestCompanionHandoff(unittest.IsolatedAsyncioTestCase):
    async def test_no_llm_after_handoff(self):
        transcript = [
            {
                "role": "companion",
                "text": "Thank you for telling me. Someone from the care team will come and have a chat with you soon.",
            },
            {"role": "resident", "text": "Alright. Thank you for listening."},
        ]
        reply, warnings = await generate_companion_reply(
            preferred_name="Mr Lim", locale="en-AU", transcript=transcript
        )
        self.assertIn("Take care, Mr Lim", reply)
        self.assertNotIn("orchid", reply.lower())
        self.assertEqual(warnings, [])

    async def test_handoff_after_safety_yes(self):
        transcript = [
            {
                "role": "companion",
                "text": "Do you ever feel that it would be better if you weren't here?",
            },
            {"role": "resident", "text": "Sometimes, yes. I wouldn't do anything."},
        ]
        reply, _ = await generate_companion_reply(
            preferred_name="Mr Lim", locale="en-AU", transcript=transcript
        )
        self.assertIn("care team", reply.lower())
        self.assertNotIn("?", reply)


if __name__ == "__main__":
    unittest.main()
