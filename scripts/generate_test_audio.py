"""
Generate a test WAV file: 2 seconds of 440 Hz sine wave,
PCM 16 kHz 16-bit mono.

Usage:
    python scripts/generate_test_audio.py
    → writes tests/smoke/fixtures/test_audio.wav
"""

from __future__ import annotations

import struct
import math
import wave
from pathlib import Path


def generate_sine_wav(
    output_path: str | Path,
    frequency: int = 440,
    duration: float = 2.0,
    sample_rate: int = 16000,
    bits_per_sample: int = 16,
) -> Path:
    """Generate a sine-wave WAV file and return its path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    n_samples = int(sample_rate * duration)
    max_amp = (2 ** (bits_per_sample - 1)) - 1

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(bits_per_sample // 8)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            value = int(max_amp * 0.5 * math.sin(2 * math.pi * frequency * t))
            frames += struct.pack("<h", value)

        wf.writeframes(bytes(frames))

    return output_path


if __name__ == "__main__":
    # Resolve paths relative to project root
    project_root = Path(__file__).resolve().parents[1]
    out = project_root / "tests" / "smoke" / "fixtures" / "test_audio.wav"
    generate_sine_wav(out)
    size_kb = out.stat().st_size / 1024
    print(f"Generated {out}  ({size_kb:.1f} KB)")
