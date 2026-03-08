"""FastAPI HTTP server exposing the LangGraph multi-agent system via REST API."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Path setup ───────────────────────────────────────────────────────────────
# Ensure the repo root is on sys.path so `agents.src.*` imports resolve.
# When Railway runs from agents/ as root dir, parent is the full repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from langchain_core.messages import AIMessage, HumanMessage

from agents.src.agent.system import agent_supervisor_graph
from agents.src.utils import sanitize_input, setup_logger

logger = setup_logger("api_server")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="MedTriage AI API", version="1.0.0")

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
    sources: List[str]
    session_id: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    safe_message = sanitize_input(req.message)
    if not safe_message:
        raise HTTPException(status_code=400, detail="Message is empty or invalid.")

    state = {
        "messages": [HumanMessage(content=safe_message)],
        "session_id": session_id,
    }
    config = {"configurable": {"thread_id": session_id}}

    try:
        result = await agent_supervisor_graph.ainvoke(state, config=config)
    except Exception as e:
        logger.error(f"Graph invocation error for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Agent encountered an error. Please try again.",
        )

    # Extract the last AI message as the response text
    messages = result.get("messages", [])
    ai_reply = next(
        (m.content for m in reversed(messages) if isinstance(m, AIMessage)),
        "I'm sorry, I couldn't generate a response. Please try again.",
    )

    return ChatResponse(response=ai_reply, sources=[], session_id=session_id)


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    # MemorySaver is in-memory; sessions naturally expire with the process.
    return {"status": "deleted", "session_id": session_id}
