"""Text-to-speech via Piper ONNX — local CPU, plays through default speaker."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from piper import PiperVoice

from .config import VOICE_BY_LOCALE

_voices: dict[str, PiperVoice] = {}


def get_voice(locale: str) -> PiperVoice:
    if locale not in _voices:
        paths = VOICE_BY_LOCALE.get(locale) or VOICE_BY_LOCALE["en-SG"]
        onnx = paths["onnx"]
        if not onnx.is_file():
            raise FileNotFoundError(
                f"Piper voice not found: {onnx}\n"
                "Run: C:\\Python314\\python.exe edge\\download_models.py"
            )
        _voices[locale] = PiperVoice.load(str(onnx), config_path=str(paths["config"]))
    return _voices[locale]


def speak(text: str, *, locale: str = "en-SG") -> None:
    """Synthesize and play text. Audio buffers are not written to disk."""
    if not text.strip():
        return
    voice = get_voice(locale)
    chunks: list[np.ndarray] = []
    sample_rate = 22_050
    for chunk in voice.synthesize(text):
        sample_rate = chunk.sample_rate
        samples = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16).astype(np.float32)
        samples /= 32768.0
        chunks.append(samples)
    if not chunks:
        return
    audio = np.concatenate(chunks)
    sd.play(audio, samplerate=sample_rate)
    sd.wait()
