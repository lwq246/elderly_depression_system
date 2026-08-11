import unittest
from unittest.mock import patch

from fastapi import FastAPI

from backend.app.observability import configure_observability, log_session_event, timed_span


class ObservabilityTests(unittest.TestCase):
    def test_configure_disabled_does_not_import_logfire(self) -> None:
        app = FastAPI()

        with patch("backend.app.config.settings.logfire_enabled", False):
            configure_observability(app)

    def test_log_session_event_noop_when_disabled(self) -> None:
        with patch("backend.app.config.settings.logfire_enabled", False):
            log_session_event("session_entry", session_id="abc", text="should not log")

    def test_timed_span_when_disabled(self) -> None:
        with patch("backend.app.config.settings.logfire_enabled", False):
            with timed_span("companion_reply") as span:
                span["extra"] = 1
            self.assertNotIn("duration_ms", span)


if __name__ == "__main__":
    unittest.main()
