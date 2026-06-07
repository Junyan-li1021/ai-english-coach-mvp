"""
REST API endpoints for session management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models.schemas import SessionCreate, SessionResponse, EvaluationRequest, EvaluationResult

router = APIRouter(prefix="/api", tags=["session"])

# ── In-memory session store (swap for DB later) ─────────────
_sessions: dict[str, dict] = {}


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionCreate):
    """Create a new interview session."""
    import uuid
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "topic": body.topic,
        "difficulty": body.difficulty,
        "created_at": datetime.now(),
        "status": "active",
        "messages": [],
    }
    _sessions[session_id] = session
    return SessionResponse(**session)


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Retrieve session details."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)


@router.post("/session/{session_id}/evaluate", response_model=EvaluationResult)
async def evaluate_session(session_id: str, body: EvaluationRequest):
    """
    Trigger evaluation for a session.
    This is a placeholder — actual evaluation logic will be wired in Day1.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Placeholder response
    return EvaluationResult(
        overall_score=0.0,
        pronunciation_score=0.0,
        fluency_score=0.0,
        vocabulary_score=0.0,
        grammar_score=0.0,
        feedback="Evaluation not yet implemented — placeholder response.",
        suggestions=["Wire up the actual evaluation pipeline."],
    )
