"""Download ggml-tiny.en (whisper.cpp) and Piper voice models for en-SG / en-AU."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge.voice.config import PIPER_DIR, VOICE_MODELS_DIR

PIPER_VOICES = [
    {
        "name": "en_GB-alan-medium (en-SG)",
        "files": [
            (
                "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
                "en_GB-alan-medium.onnx",
            ),
            (
                "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
                "en_GB-alan-medium.onnx.json",
            ),
        ],
    },
    {
        "name": "en_GB-southern_english_female-low (en-AU)",
        "files": [
            (
                "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx",
                "en_GB-southern_english_female-low.onnx",
            ),
            (
                "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/southern_english_female/low/en_GB-southern_english_female-low.onnx.json",
                "en_GB-southern_english_female-low.onnx.json",
            ),
        ],
    },
]


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        print(f"  skip {dest.name} (exists)")
        return
    print(f"  download {dest.name}...")
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with dest.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    print(f"  saved {dest} ({dest.stat().st_size // 1024} KB)")


def download_whisper() -> None:
    print("Whisper (ggml-tiny.en) — downloaded on first use by pywhispercpp...")
    from pywhispercpp.model import Model

    Model("tiny.en")
    print("  whisper tiny.en ready")


def main() -> int:
    print(f"Voice models dir: {VOICE_MODELS_DIR}")
    PIPER_DIR.mkdir(parents=True, exist_ok=True)

    for voice in PIPER_VOICES:
        print(f"\nPiper: {voice['name']}")
        for url, filename in voice["files"]:
            download_file(url, PIPER_DIR / filename)

    print()
    download_whisper()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
