"""
Alibaba Cloud NLS — Text-to-Speech via WebSocket.

Usage:
    tts = TTSService(settings)
    async for pcm_chunk in tts.synthesize("Hello!"):
        # pcm_chunk is raw PCM bytes (16 kHz 16-bit mono)
        handle(pcm_chunk)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
import asyncio
from typing import AsyncGenerator

import httpx
import websockets

_NLS_GATEWAY = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
_TOKEN_API = "https://nls-meta.cn-shanghai.aliyuncs.com/"


class TTSService:
    """Alibaba Cloud TTS WebSocket client — streams PCM audio."""

    def __init__(self, config):
        self._config = config
        self._token: str | None = None

    # ── Token acquisition (shared with ASR) ──────────────────

    async def _fetch_token(self) -> str:
        ak_id = self._config.ALIYUN_ACCESS_KEY_ID
        ak_secret = self._config.ALIYUN_ACCESS_KEY_SECRET
        if not ak_id or not ak_secret:
            raise RuntimeError("ALIYUN_ACCESS_KEY_ID / SECRET not configured")

        import urllib.parse
        params = {
            "AccessKeyId": ak_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "Version": "2019-02-28",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid4()),
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        sorted_query = sorted(params.items())
        canonical = "&".join(
            urllib.parse.quote(k, safe="") + "=" + urllib.parse.quote(v, safe="")
            for k, v in sorted_query
        )
        string_to_sign = "GET&%2F&" + urllib.parse.quote(canonical, safe="")
        signature = hmac.new(
            (ak_secret + "&").encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        params["Signature"] = signature.encode("base64").decode().strip()

        async with httpx.AsyncClient() as client:
            resp = await client.get(_TOKEN_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["Token"]["Id"]
            return self._token

    # ── Synthesize ───────────────────────────────────────────

    async def synthesize(
        self,
        text: str,
        voice: str = "en_us_001",
        sample_rate: int = 16000,
        format: str = "pcm",
        volume: int = 50,
        speech_rate: float = 0.0,
        pitch_rate: float = 0.0,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio as raw PCM chunks.

        Args:
            text: The text to synthesize.
            voice: Voice model name (e.g. "en_us_001").
            sample_rate: Audio sample rate in Hz.
            format: Output audio format ("pcm" recommended for streaming).
            volume: Volume 0–100.
            speech_rate: Speech rate adjustment (-500 .. 500).
            pitch_rate: Pitch rate adjustment (-500 .. 500).

        Yields:
            bytes: Raw PCM audio chunks.
        """
        if not self._token:
            await self._fetch_token()

        task_id = str(uuid.uuid4())
        url = (
            f"{_NLS_GATEWAY}?token={self._token}"
            f"&appkey={self._config.ALIYUN_NLS_APPKEY}"
        )

        async with websockets.connect(url) as ws:
            start_msg = {
                "header": {
                    "message_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "namespace": "SpeechSynthesizer",
                    "name": "StartSynthesis",
                    "appkey": self._config.ALIYUN_NLS_APPKEY,
                },
                "payload": {
                    "text": text,
                    "voice": voice,
                    "format": format,
                    "sample_rate": sample_rate,
                    "volume": volume,
                    "speech_rate": speech_rate,
                    "pitch_rate": pitch_rate,
                },
            }
            await ws.send(json.dumps(start_msg))

            # Read frames until synthesis complete
            async for raw in ws:
                if isinstance(raw, bytes):
                    # Binary audio frame
                    yield raw
                else:
                    frame = json.loads(raw)
                    name = frame.get("header", {}).get("name", "")
                    if name == "SynthesisCompleted":
                        break
                    if name == "TaskFailed":
                        raise RuntimeError(
                            f"TTS synthesis failed: {frame.get('payload', {})}"
                        )
