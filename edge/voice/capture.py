"""Capture microphone audio into RAM only — no files written."""

from __future__ import annotations

import numpy as np
import sounddevice as sd

from .config import SAMPLE_RATE


def record_seconds(seconds: float, *, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Record mono float32 audio. Caller must delete the array when done."""
    frames = int(seconds * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return np.squeeze(audio)
