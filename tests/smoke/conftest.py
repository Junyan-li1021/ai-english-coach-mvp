"""
Shared pytest fixtures and helpers for smoke tests.
Also loads the project .env file automatically.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# ── Resolve project root & load .env ────────────────────────
# When running as `python tests/smoke/test_xxx.py` from the repo root,
# __file__ is  tests/smoke/conftest.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # speakeasy/
_BACKEND_DIR = _PROJECT_ROOT / "backend"

# Make backend/app importable
sys.path.insert(0, str(_BACKEND_DIR))

load_dotenv(_PROJECT_ROOT / ".env", override=False)


@pytest.fixture(scope="session")
def get_config():
    """Return a lazily-created Settings instance."""
    from app.config import Settings
    _settings = Settings()
    return _settings


def check_env(key: str) -> str | None:
    """
    Return the env value if present (and non-empty / non-placeholder),
    else None. Useful for gating tests that need real API keys.
    """
    val = os.environ.get(key, "").strip()
    if not val or val.startswith("your_"):
        return None
    return val
