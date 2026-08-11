import unittest
from unittest.mock import patch

from backend.app.llm_capture import llm_capture_scope, record_llm_input


class LlmCaptureTests(unittest.TestCase):
    def test_record_llm_input_when_enabled(self) -> None:
        with patch("backend.app.db.append_llm_input") as append_mock:
            with llm_capture_scope("session-1", enabled=True):
                record_llm_input(
                    "companion",
                    system="system prompt",
                    user="user prompt",
                    turn_index=1,
                )
            append_mock.assert_called_once()
            record = append_mock.call_args[0][1]
            self.assertEqual(record["call"], "companion")
            self.assertEqual(record["messages"][0]["content"], "system prompt")

    def test_record_llm_input_when_disabled(self) -> None:
        with patch("backend.app.db.append_llm_input") as append_mock:
            with llm_capture_scope("session-1", enabled=False):
                record_llm_input("companion", system="s", user="u")
            append_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
