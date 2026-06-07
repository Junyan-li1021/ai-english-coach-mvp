"""
Speakeasy Backend — FastAPI application entry point.

Provides:
  - GET  /health              Health check
  - POST /api/session          Create session
  - POST /api/session/{id}/evaluate  Trigger evaluation
  - WS   /ws/interview/{id}   Real-time interview WebSocket
"""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.api.session import router as session_router

# ── App factory ──────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="Speakeasy Backend",
    version="0.1.0",
    description="AI-powered English interview practice backend",
)

# ── CORS ─────────────────────────────────────────────────────

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST routes ──────────────────────────────────────────────

app.include_router(session_router)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "env": settings.APP_ENV,
    }


# ── WebSocket: real-time interview ──────────────────────────

@app.websocket("/ws/interview/{session_id}")
async def interview_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time interview interaction.

    Protocol (skeleton — full logic in Day1):
      Client sends:
        { "type": "audio_chunk", "payload": { "data": "<base64>" } }
        { "type": "text_message", "payload": { "text": "..." } }
      Server responds:
        { "type": "asr_partial", "payload": { "text": "..." } }
        { "type": "asr_final",   "payload": { "text": "..." } }
        { "type": "llm_response", "payload": { "text": "..." } }
        { "type": "tts_audio",   "payload": { "data": "<base64>" } }
        { "type": "error",       "payload": { "message": "..." } }
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON"},
                })
                continue

            msg_type = msg.get("type", "")
            payload = msg.get("payload", {})

            # ── Skeleton echo-back (Day1: wire up real services) ──
            if msg_type == "text_message":
                text = payload.get("text", "")
                await websocket.send_json({
                    "type": "asr_final",
                    "payload": {"text": text},
                })
                await websocket.send_json({
                    "type": "llm_response",
                    "payload": {
                        "text": (
                            f"[Skeleton] You said: {text}. "
                            "Full logic coming in Day1."
                        ),
                    },
                })
            elif msg_type == "audio_chunk":
                # Day1: pipe through ASR → LLM → TTS
                await websocket.send_json({
                    "type": "asr_partial",
                    "payload": {"text": "[audio received — ASR not wired yet]"},
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"Unknown message type: {msg_type}"},
                })

    except WebSocketDisconnect:
        pass
