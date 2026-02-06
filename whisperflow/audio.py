"""Audio capture module for WhisperFlow.

Handles Blue Yeti USB mic detection and push-to-talk recording.
Uses sounddevice with PulseAudio for automatic sample rate conversion.
"""

import threading
import numpy as np
import sounddevice as sd


def has_blue_yeti():
    """Check if a Blue Yeti mic is connected."""
    devices = sd.query_devices()
    for d in devices:
        if "yeti" in d["name"].lower() and d["max_input_channels"] > 0:
            return True
    return False


def find_input_device(config_device):
    """Resolve configured audio device to a device index.

    For "auto": uses PulseAudio default device (None) which handles
    resampling to 16kHz automatically. The Blue Yeti ALSA hw device
    only supports 44100Hz natively, so PulseAudio is preferred.

    Args:
        config_device: "auto", "default", or an integer device index.

    Returns:
        Device index (int) or None for system default.
    """
    if config_device in ("auto", "default"):
        # Always use PulseAudio default - it handles resampling and
        # respects the user's system audio settings
        if config_device == "auto" and has_blue_yeti():
            print("[WhisperFlow] Blue Yeti detected. Using system default audio input.")
        return None
    else:
        return int(config_device)


class AudioRecorder:
    """Records audio from microphone during push-to-talk.

    Records at the device's native sample rate and resamples to 16kHz
    for Whisper. Uses PulseAudio default device for best compatibility.
    """

    def __init__(self, device=None, sample_rate=16000):
        self.target_sr = sample_rate
        self.device = device
        self.channels = 1
        self._buffer = []
        self._recording = False
        self._stream = None
        self._lock = threading.Lock()

        # Determine native sample rate
        if device is not None:
            info = sd.query_devices(device)
            self.native_sr = info["default_samplerate"]
        else:
            # PulseAudio default handles resampling, so we can request 16kHz directly
            self.native_sr = self.target_sr

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass  # Silently ignore xruns
        if self._recording:
            self._buffer.append(indata[:, 0].copy())

    def start(self):
        """Start recording audio."""
        with self._lock:
            self._buffer = []
            self._recording = True
            if self._stream is None:
                self._stream = sd.InputStream(
                    device=self.device,
                    samplerate=self.native_sr,
                    channels=self.channels,
                    dtype="float32",
                    blocksize=int(self.native_sr * 0.1),  # 100ms blocks
                    callback=self._audio_callback,
                )
                self._stream.start()

    def stop(self):
        """Stop recording and return the captured audio as float32 array at target sample rate."""
        with self._lock:
            self._recording = False
            if not self._buffer:
                return np.array([], dtype=np.float32)

            audio = np.concatenate(self._buffer)
            self._buffer = []

            # Resample if needed
            if abs(self.native_sr - self.target_sr) > 1:
                # Simple linear interpolation resampling
                duration = len(audio) / self.native_sr
                target_len = int(duration * self.target_sr)
                indices = np.linspace(0, len(audio) - 1, target_len)
                audio = np.interp(indices, np.arange(len(audio)), audio).astype(
                    np.float32
                )

            return audio

    def close(self):
        """Clean up the audio stream."""
        with self._lock:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
