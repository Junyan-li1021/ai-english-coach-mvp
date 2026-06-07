"""
Alibaba Cloud NLS — Real-time ASR via WebSocket.

Usage:
    asr = ASRService(settings)
    await asr.connect(on_result=_callback)
    await asr.send_audio(pcm_chunk)
    …
    await asr.close()
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
import asyncio
from typing import Callable, Optional

import httpx
import websockets

# The NLS gateway endpoint (Shanghai region)
_NLS_GATEWAY = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
_TOKEN_API = "https://nls-meta.cn-shanghai.aliyuncs.com/"


class ASRResult:
    """Thin wrapper around a recognition result."""

    def __init__(self, text: str, is_final: bool):
        self.text = text
        self.is_final = is_final

    def __repr__(self) -> str:
        tag = "FINAL" if self.is_final else "PARTIAL"
        return f"<ASRResult [{tag}] {self.text!r}>"


class ASRService:
    """Alibaba Cloud real-time ASR WebSocket client."""

    def __init__(self, config):
        """
        Args:
            config: a Settings instance (from app.config).
        """
        self._config = config
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._token: Optional[str] = None
        self._task_id: str = ""
        self._on_result: Optional[Callable[[ASRResult], None]] = None

    # ── Token acquisition ────────────────────────────────────

    async def _fetch_token(self) -> str:
        """
        Obtain a short-lived NLS token using AccessKey signature.
        Reference: https://help.aliyun.com/document_detail/72153.html
        """
        ak_id = self._config.ALIYUN_ACCESS_KEY_ID
        ak_secret = self._config.ALIYUN_ACCESS_KEY_SECRET

        if not ak_id or not ak_secret:
            raise RuntimeError("ALIYUN_ACCESS_KEY_ID / SECRET not configured")

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

        # Sort & percent-encode for signature (simplified, works for standard params)
        import urllib.parse
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
        signature_b64 = signature.encode("base64").decode().strip()
        params["Signature"] = signature_b64

        async with httpx.AsyncClient() as client:
            resp = await client.get(_TOKEN_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["Token"]["Id"]
            return self._token

    # ── Connection lifecycle ─────────────────────────────────

    async def connect(
        self,
        on_result: Callable[[ASRResult], None] | None = None,
        sample_rate: int = 16000,
        format: str = "pcm",
        enable_intermediate_result: bool = True,
    ) -> None:
        """
        Open WebSocket to NLS gateway and start a recognition stream.
        """
        self._on_result = on_result
        self._task_id = str(uuid.uuid4())

        if not self._token:
            await self._fetch_token()

        url = (
            f"{_NLS_GATEWAY}?token={self._token}"
            f"&appkey={self._config.ALIYUN_NLS_APPKEY}"
        )
        self._ws = await websockets.connect(url)

        # Start-task message
        start_msg = {
            "header": {
                "message_id": str(uuid.uuid4()),
                "task_id": self._task_id,
                "namespace": "SpeechTranscriber",
                "name": "StartTranscription",
                "appkey": self._config.ALIYUN_NLS_APPKEY,
            },
            "payload": {
                "format": format,
                "sample_rate": sample_rate,
                "enable_intermediate_result": enable_intermediate_result,
                "enable_punctuation_prediction": True,
                "enable_inverse_text_normalization": True,
            },
        }
        await self._ws.send(json.dumps(start_msg))

        # Kick off background listener
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Background task: read WS frames and dispatch results."""
        try:
            async for raw in self._ws:
                frame = json.loads(raw)
                header = frame.get("header", {})
                name = header.get("name", "")
                payload = frame.get("payload", {})

                if name == "TranscriptionResultChanged":
                    # Partial / intermediate result
                    result = ASRResult(
                        text=payload.get("result", ""), is_final=False
                    )
                    if self._on_result:
                        self._on_result(result)

                elif name == "SentenceEnd":
                    # Final result for a sentence
                    result = ASRResult(
                        text=payload.get("result", ""), is_final=True
                    )
                    if self._on_result:
                        self._on_result(result)

                elif name == "TaskFailed":
                    raise RuntimeError(
                        f"ASR task failed: {payload}"
                    )
        except websockets.exceptions.ConnectionClosed:
            pass

    # ── Audio streaming ──────────────────────────────────────

    async def send_audio(self, chunk: bytes) -> None:
        """Send a PCM audio chunk (bytes) to the recognition stream."""
        if self._ws is None:
            raise RuntimeError("Not connected — call connect() first")
        await self._ws.send(chunk)

    # ── Teardown ─────────────────────────────────────────────

    async def close(self) -> None:
        """Gracefully stop recognition and close the WebSocket."""
        if self._ws:
            # Send stop message
            stop_msg = {
                "header": {
                    "message_id": str(uuid.uuid4()),
                    "task_id": self._task_id,
                    "namespace": "SpeechTranscriber",
                    "name": "StopTranscription",
                    "appkey": self._config.ALIYUN_NLS_APPKEY,
                },
                "payload": {},
            }
            try:
                await self._ws.send(json.dumps(stop_msg))
            except Exception:
                pass
            await self._ws.close()
            self._ws = None
