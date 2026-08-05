"""HTTP client for the screening FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx

from .config import API_BASE

TIMEOUT = 180.0


class ScreeningClient:
    def __init__(self, base: str | None = None) -> None:
        self.base = (base or API_BASE).rstrip("/")

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{self.base}/api/health")
            r.raise_for_status()
            return r.json()

    def entry(
        self,
        *,
        resident_id: str,
        locale: str,
        speech_register: str = "standard",
    ) -> dict[str, Any]:
        body = {
            "resident_id": resident_id,
            "locale": locale,
            "speech_register": speech_register,
        }
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(f"{self.base}/api/sessions/entry", json=body)
            r.raise_for_status()
            return r.json()

    def message(self, session_id: str, text: str) -> dict[str, Any]:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(
                f"{self.base}/api/sessions/{session_id}/message",
                json={"text": text},
            )
            r.raise_for_status()
            return r.json()

    def exit(self, session_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(f"{self.base}/api/sessions/{session_id}/exit")
            r.raise_for_status()
            return r.json()
