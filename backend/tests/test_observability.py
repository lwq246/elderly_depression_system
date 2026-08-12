import unittest

from fastapi import FastAPI

from backend.app.observability import configure_observability, log_session_event, timed_span


class ObservabilityTests(unittest.TestCase):
    def test_configure_is_noop(self) -> None:
        configure_observability(FastAPI())

    def test_log_session_event_is_noop(self) -> None:
        log_session_event("session_entry", session_id="abc", text="should not log")

    def test_timed_span_yields_mutable_dict(self) -> None:
        with timed_span("companion_reply") as span:
            span["extra"] = 1
        self.assertEqual(span["extra"], 1)


if __name__ == "__main__":
    unittest.main()
