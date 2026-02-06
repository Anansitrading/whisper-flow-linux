"""Whisper transcription module for WhisperFlow.

Uses faster-whisper with CTranslate2 backend for CPU-optimized inference.
"""

import re
import numpy as np


# Known Whisper hallucination patterns on silence/noise
_HALLUCINATION_PATTERNS = [
    r"^\s*$",
    r"^(you|the|thank you|thanks for watching|subscribe)\.?$",
    r"^\[.*\]$",  # [Music], [Silence], etc.
    r"^\.+$",
]


class Transcriber:
    """Manages Whisper model and transcription."""

    def __init__(self, model_size="base.en", compute_type="int8", language="en"):
        self.model_size = model_size
        self.compute_type = compute_type
        self.language = language
        self._model = None

    def _ensure_model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type=self.compute_type,
            )

    def transcribe(self, audio):
        """Transcribe audio array to text.

        Args:
            audio: numpy float32 array at 16kHz.

        Returns:
            Transcribed text string, or empty string if no speech detected.
        """
        if len(audio) < 1600:  # Less than 0.1s
            return ""

        self._ensure_model()

        segments, info = self._model.transcribe(
            audio,
            beam_size=5,
            language=self.language,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200,
            ),
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()

        # Filter hallucinations
        if self._is_hallucination(text):
            return ""

        return text

    def _is_hallucination(self, text):
        """Check if text is a known Whisper hallucination on silence."""
        text_lower = text.lower().strip()
        if not text_lower:
            return True
        for pattern in _HALLUCINATION_PATTERNS:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return True
        return False
