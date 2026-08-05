# Edge voice (local STT + TTS)

Runs on your **ThinkPad** (or Raspberry Pi) — audio stays local; only **text** goes to the cloud API.

| Role | Engine | Model |
|------|--------|--------|
| **Ears** (STT) | [whisper.cpp](https://github.com/ggerganov/whisper.cpp) via `pywhispercpp` | `ggml-tiny.en` |
| **Mouth** (TTS) | [Piper](https://github.com/rhasspy/piper) via `piper-tts` | ONNX voices (CPU) |

## Privacy

- Microphone audio → **numpy buffer in RAM** → Whisper → text
- **No** `.wav` / `.mp3` files written
- Only transcribed **text** is sent to `http://127.0.0.1:8000` (companion LLM)

## Setup (Windows ThinkPad)

```powershell
cd C:\Users\leewe\Documents\CursorDepression

# 1. Edge voice dependencies
C:\Python314\python.exe -m pip install -r edge\requirements.txt

# 2. Download Piper voices + whisper tiny.en
C:\Python314\python.exe edge\download_models.py

# 3. Start backend (separate terminal)
C:\Python314\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

## Run voice screening room

```powershell
# Mrs Tan, Singapore
C:\Python314\python.exe edge\run_voice_room.py --resident R-001 --locale en-SG

# Mr Lim, Australia
C:\Python314\python.exe edge\run_voice_room.py --resident R-002 --locale en-AU
```

**Flow each turn:** Press Enter → speak for 5 seconds → Whisper transcribes → API reply → Piper speaks.

- **Ctrl+C** during "Press Enter" → leave room and run analyst  
- Type nothing detected → press Enter again to retry  

## Voices

| Locale | Piper voice |
|--------|-------------|
| `en-SG` | `en_GB-alan-medium` |
| `en-AU` | `en_GB-southern_english_female-low` |

Models live in `data/voice_models/` (gitignored).

## Environment

| Variable | Default |
|----------|---------|
| `VOICE_API_BASE` | `http://127.0.0.1:8000` |
| `VOICE_RECORD_SECONDS` | `5` |
| `WHISPER_MODEL` | `tiny.en` |
| `VOICE_MODELS_DIR` | `data/voice_models` |

## Note on `whisper-cpp-python`

The PyPI package `whisper-cpp-python` needs a C++ compiler on Windows. This project uses **`pywhispercpp`** instead — same whisper.cpp engine, prebuilt wheels for Python 3.14.

## Raspberry Pi

Same code; use `tiny.en` on Pi 4/5. For faster STT on Pi, keep utterances short (`VOICE_RECORD_SECONDS=4`).
