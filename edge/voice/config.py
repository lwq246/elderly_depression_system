import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOICE_MODELS_DIR = Path(os.environ.get("VOICE_MODELS_DIR", ROOT / "data" / "voice_models"))
PIPER_DIR = VOICE_MODELS_DIR / "piper"

API_BASE = os.environ.get("VOICE_API_BASE", os.environ.get("TEST_API_BASE", "http://127.0.0.1:8000"))

# Piper voices (British English works well for SG; southern GB for AU)
VOICE_BY_LOCALE = {
    "en-SG": {
        "onnx": PIPER_DIR / "en_GB-alan-medium.onnx",
        "config": PIPER_DIR / "en_GB-alan-medium.onnx.json",
    },
    "en-AU": {
        "onnx": PIPER_DIR / "en_GB-southern_english_female-low.onnx",
        "config": PIPER_DIR / "en_GB-southern_english_female-low.onnx.json",
    },
}

SAMPLE_RATE = 16_000
RECORD_SECONDS = float(os.environ.get("VOICE_RECORD_SECONDS", "5"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "tiny.en")
