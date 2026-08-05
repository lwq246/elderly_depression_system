"""Speech-to-text via whisper.cpp (pywhispercpp) — ggml-tiny.en, in-memory only."""

from __future__ import annotations

import numpy as np
from pywhispercpp.model import Model

from .config import SAMPLE_RATE, WHISPER_MODEL

_model: Model | None = None


def get_model() -> Model:
    global _model
    if _model is None:
        _model = Model(WHISPER_MODEL)
    return _model


def transcribe_audio(audio: np.ndarray, *, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Transcribe float32 mono PCM. Audio stays in RAM; no .wav is created.
    Resamples to 16 kHz if needed (whisper expects 16 kHz).
    """
    if audio.size == 0:
        return ""

    pcm = np.asarray(audio, dtype=np.float32).flatten()
    if sample_rate != SAMPLE_RATE:
        from scipy import signal

        samples = int(len(pcm) * SAMPLE_RATE / sample_rate)
        pcm = signal.resample(pcm, samples).astype(np.float32)

    model = get_model()
    segments = model.transcribe(pcm)
    text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
    return text.strip()
