"""
Youdao Oral Evaluation Service (有道口语评测).

API docs: https://ai.youdao.com/DOCSIRMA/html/trans/api/wenbenfy/index.html

Usage:
    svc = EvalService(settings)
    result = await svc.evaluate(wav_bytes, ref_text="Hello world")
    print(result["pronunciation_score"])
"""

from __future__ import annotations

import hashlib
import struct
import time
import uuid
from typing import Optional

import httpx


_YOUDAO_API = "https://openapi.youdao.com/evalapi"


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class EvalService:
    """Youdao spoken-English evaluation client."""

    def __init__(self, config):
        self._config = config

    # ── Signing ──────────────────────────────────────────────

    @staticmethod
    def _sign(
        app_key: str,
        text: str,
        salt: str,
        curtime: str,
        app_secret: str,
    ) -> str:
        """
        Compute Youdao sign:
            sha256(appKey + sha256(text) + salt + curtime + appSecret)
        """
        text_hash = _sha256_hex(text)
        raw = f"{app_key}{text_hash}{salt}{curtime}{app_secret}"
        return _sha256_hex(raw)

    # ── WAV header helper ────────────────────────────────────

    @staticmethod
    def _make_wav(
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        bits_per_sample: int = 16,
        channels: int = 1,
    ) -> bytes:
        """Prepend a standard WAV header to raw PCM data."""
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        data_size = len(pcm_bytes)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,  # chunk size
            1,   # PCM format
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size,
        )
        return header + pcm_bytes

    # ── Evaluate ─────────────────────────────────────────────

    async def evaluate(
        self,
        audio_wav_bytes: bytes,
        ref_text: Optional[str] = None,
        q_type: str = "open",
        lang: str = "en",
    ) -> dict:
        """
        Call the Youdao oral evaluation API.

        Args:
            audio_wav_bytes: WAV audio data (16 kHz, 16-bit, mono recommended).
            ref_text: Reference text. If None, uses open (free-speaking) mode.
            q_type: Evaluation mode — "open" for free speaking.
            lang: Language code.

        Returns:
            dict with keys like pronunciation_score, fluency_score, etc.
        """
        app_key = self._config.YOUDAO_APP_KEY
        app_secret = self._config.YOUDAO_APP_SECRET

        if not app_key or not app_secret:
            raise RuntimeError("YOUDAO_APP_KEY / YOUDAO_APP_SECRET not configured")

        salt = str(uuid.uuid4())
        curtime = str(int(time.time()))
        text = ref_text or ""

        sign = self._sign(app_key, text, salt, curtime, app_secret)

        # Ensure the audio has a proper WAV header
        if not audio_wav_bytes[:4] == b"RIFF":
            audio_wav_bytes = self._make_wav(audio_wav_bytes)

        data = {
            "appKey": app_key,
            "salt": salt,
            "curtime": curtime,
            "sign": sign,
            "signType": "v3",
            "qType": q_type,
            "lang": lang,
            "text": text,
        }

        files = {
            "audio": ("audio.wav", audio_wav_bytes, "audio/wav"),
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(_YOUDAO_API, data=data, files=files)
            resp.raise_for_status()
            result = resp.json()

        # Normalize result into a flat dict of scores
        if "result" in result:
            eval_data = result["result"]
            return {
                "overall_score": eval_data.get("overall", 0.0),
                "pronunciation_score": eval_data.get("pronunciation", 0.0),
                "fluency_score": eval_data.get("fluency", 0.0),
                "integrity_score": eval_data.get("integrity", 0.0),
                "raw": result,
            }
        elif "errorCod" in result and result["errorCod"] != "0":
            raise RuntimeError(f"Youdao API error: {result}")

        return result
