"""FastAPI HTTP server exposing the LangGraph multi-agent system via REST API."""
from __future__ import annotations

import os
import sys
import types
import uuid
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Path setup ───────────────────────────────────────────────────────────────
# Railway deploys only the agents/ folder to /app, so `import agents` fails
# because the package can't find itself. Fix: register a virtual 'agents'
# package pointing to this directory before any agents.src.* imports occur.
# This also fixes sub-modules (system.py, config.py, etc.) that use the same
# `from agents.src.*` pattern.
_HERE = Path(__file__).resolve().parent
if "agents" not in sys.modules:
    _agents_pkg = types.ModuleType("agents")
    _agents_pkg.__path__ = [str(_HERE)]
    _agents_pkg.__package__ = "agents"
    sys.modules["agents"] = _agents_pkg

from langchain_core.messages import AIMessage, HumanMessage

from backend.agent_service import extract_sources
from agents.src.utils import sanitize_input, setup_logger

logger = setup_logger("api_server")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Nenagov API", version="1.0.0")

# CORS — allow requests from the deployed frontend (or * if not set)
_frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url] if _frontend_url != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[dict]
    session_id: str


@lru_cache(maxsize=1)
def get_agent_graph():
    """Load the LangGraph workflow lazily so health checks can succeed even if RAG startup is slow."""
    system_module = import_module("agents.src.agent.system")
    return system_module.agent_supervisor_graph


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "backend"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    safe_message = sanitize_input(req.message)
    if not safe_message:
        raise HTTPException(status_code=400, detail="Message is empty or invalid.")

    logger.info(
        "Received chat request | session_id=%s | preview=%s",
        session_id,
        safe_message[:120].replace("\n", " "),
    )

    state = {
        "messages": [HumanMessage(content=safe_message)],
        "session_id": session_id,
    }
    config = {"configurable": {"thread_id": session_id}}

    try:
        agent_supervisor_graph = get_agent_graph()
        result = await agent_supervisor_graph.ainvoke(state, config=config)
    except Exception as e:
        logger.exception(f"Graph invocation error for session {session_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Agent backend is unavailable or still initializing. Please try again.",
        )

    # Extract the last AI message as the response text
    messages = result.get("messages", [])
    ai_reply = next(
        (m.content for m in reversed(messages) if isinstance(m, AIMessage)),
        "I'm sorry, I couldn't generate a response. Please try again.",
    )

    sources = extract_sources(messages)

    return ChatResponse(response=ai_reply, sources=sources, session_id=session_id)


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    # MemorySaver is in-memory; sessions naturally expire with the process.
    return {"status": "deleted", "session_id": session_id}
