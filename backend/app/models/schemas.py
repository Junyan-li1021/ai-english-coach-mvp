"""
Pydantic schemas shared across the application.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Session ──────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """Request body for creating a new interview session."""
    topic: str = Field(default="general", description="Interview topic")
    difficulty: str = Field(default="intermediate", description="easy | intermediate | hard")


class SessionResponse(BaseModel):
    id: str
    topic: str
    difficulty: str
    created_at: datetime
    status: str = "active"


# ── Chat ─────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None


# ── Evaluation ───────────────────────────────────────────────

class EvaluationRequest(BaseModel):
    transcript: Optional[str] = None
    audio_duration: Optional[float] = None


class EvaluationResult(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    pronunciation_score: float = Field(ge=0, le=100)
    fluency_score: float = Field(ge=0, le=100)
    vocabulary_score: float = Field(ge=0, le=100)
    grammar_score: float = Field(ge=0, le=100)
    feedback: str = ""
    suggestions: list[str] = Field(default_factory=list)


# ── WebSocket messages ──────────────────────────────────────

class WSMessageType(str, Enum):
    AUDIO_CHUNK = "audio_chunk"
    TEXT_MESSAGE = "text_message"
    ASR_PARTIAL = "asr_partial"
    ASR_FINAL = "asr_final"
    TTS_AUDIO = "tts_audio"
    LLM_RESPONSE = "llm_response"
    EVAL_RESULT = "eval_result"
    ERROR = "error"
    SESSION_END = "session_end"


class WSMessage(BaseModel):
    type: WSMessageType
    payload: dict = Field(default_factory=dict)
