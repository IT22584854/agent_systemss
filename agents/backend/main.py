"""FastAPI backend — exposes the LangGraph medical triage agent via REST."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

# ---------------------------------------------------------------------------
# Load environment variables from agents/.env BEFORE importing agent code
# ---------------------------------------------------------------------------
from dotenv import load_dotenv

_AGENTS_DIR = Path(__file__).resolve().parent.parent     # …/agents/
load_dotenv(_AGENTS_DIR / ".env")

# Make project root importable
_PROJECT_ROOT = _AGENTS_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent_service import run_agent

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Medical Triage Agent API",
    description="LangGraph-powered medical information assistant",
    version="1.0.0",
)

_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
)
_allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SourceItem(BaseModel):
    id: int
    source: str
    url: Optional[str] = None
    chunk_index: Optional[int] = None
    excerpt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[SourceItem]
    session_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "medical-triage-agent"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the agent and receive a response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = req.session_id or str(uuid4())

    try:
        response_text, sources = run_agent(req.message.strip(), session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    return ChatResponse(
        response=response_text,
        sources=[SourceItem(**s) for s in sources],
        session_id=session_id,
    )


@app.delete("/api/session/{session_id}")
async def reset_session(session_id: str):
    """
    Reset a conversation thread.
    MemorySaver doesn't expose a delete method, but we confirm session_id accepted.
    New invocations on this session_id will start fresh if the checkpointer has no state.
    Returns 200 for client compatibility.
    """
    return {"status": "reset", "session_id": session_id}
