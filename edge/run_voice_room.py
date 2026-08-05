"""
Voice screening room (ThinkPad / edge device).

Mic → whisper.cpp (tiny.en) → screening API → Piper TTS → speaker
Raw audio is held in RAM only during each turn (no .wav / .mp3 saved).

Usage:
  C:\\Python314\\python.exe edge\\download_models.py
  C:\\Python314\\python.exe edge\\run_voice_room.py --resident R-001 --locale en-SG
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge.voice.api import ScreeningClient
from edge.voice.capture import record_seconds
from edge.voice.config import RECORD_SECONDS
from edge.voice.stt import transcribe_audio
from edge.voice.tts import speak


def companion_lines(session: dict) -> list[str]:
    return [t["text"] for t in session.get("transcript", []) if t.get("role") == "companion"]


def last_companion(session: dict) -> str:
    lines = companion_lines(session)
    return lines[-1] if lines else ""


def run_turn(locale: str) -> str | None:
    print(f"\n[{RECORD_SECONDS:.0f}s recording — speak after the beep, or Ctrl+C to leave room]")
    try:
        input("  Press Enter when ready to speak...")
    except KeyboardInterrupt:
        return None
    print("  ● recording...")
    audio = record_seconds(RECORD_SECONDS)
    print("  ○ transcribing...")
    text = transcribe_audio(audio)
    del audio
    if not text:
        print("  (no speech detected — try again)")
        return ""
    print(f"  Resident: {text}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Voice screening room (local STT/TTS)")
    parser.add_argument("--resident", default="R-001", help="Resident ID (UWB)")
    parser.add_argument("--locale", default="en-SG", choices=["en-SG", "en-AU"])
    parser.add_argument("--register", default="standard", choices=["standard", "local-light"])
    parser.add_argument("--api", default=None, help="Backend URL (default VOICE_API_BASE)")
    parser.add_argument("--record-seconds", type=float, default=None)
    args = parser.parse_args()

    if args.record_seconds:
        import edge.voice.config as cfg

        cfg.RECORD_SECONDS = args.record_seconds

    api = ScreeningClient(args.api)
    health = api.health()
    if not health.get("llm_configured"):
        print("ERROR: Backend LLM not configured. Set OPENAI_API_KEY and restart backend.")
        return 1

    print(f"Backend: {api.base}  model={health.get('model')}  locale={args.locale}")
    print(f"UWB entry — resident {args.resident}")
    session = api.entry(
        resident_id=args.resident,
        locale=args.locale,
        speech_register=args.register,
    )
    sid = session["id"]
    greeting = last_companion(session)
    if greeting:
        print(f"\nCompanion: {greeting}")
        speak(greeting, locale=args.locale)

    while session.get("status") == "active":
        text = run_turn(args.locale)
        if text is None:
            break
        if text == "":
            continue
        session = api.message(sid, text)
        reply = last_companion(session)
        if reply:
            print(f"Companion: {reply}")
            speak(reply, locale=args.locale)
        if session.get("status") == "ended":
            print("\n(Session ended by safety or permission rule.)")
            break

    if session.get("status") != "ended":
        print("\nUWB exit — generating nurse report...")
        session = api.exit(sid)

    report = session.get("report") or {}
    print(
        f"\nReport: recommendation={report.get('recommendation')} "
        f"confidence={report.get('estimate_confidence')}"
    )
    if session.get("validation_errors"):
        print("Validation errors:", session["validation_errors"])
    print(f"Session id: {sid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
