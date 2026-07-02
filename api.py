import os
import uuid
import json
from pathlib import Path
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from agent import start_research, rerun_analyst_with_feedback, continue_after_approval

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ── App setup ─────────────────────────────────────────────────────────
app = FastAPI(title="ResearchCrew API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Database connection helper ──────────────────────────────────────────
# A small context manager so every route can do:
#     with get_db() as conn:
#         ...
# and the connection is guaranteed to close afterward, even if an
# exception happens mid-query. This is the same discipline as Snowflake
# connection handling — never leave a connection open longer than needed.
@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


# ── Table creation (runs once, at startup) ───────────────────────────────
# Postgres' "CREATE TABLE IF NOT EXISTS" makes this idempotent — safe to
# run every time the app starts, whether the table already exists or not.
# This replaces having a separate manual migration step for this project's
# scale; a bigger production app would use a real migration tool instead.
def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id UUID PRIMARY KEY,
                    topic TEXT NOT NULL,
                    findings TEXT,
                    analysis TEXT,
                    report TEXT,
                    steps_completed TEXT[] DEFAULT '{}',
                    retries JSONB DEFAULT '{}',
                    errors TEXT[] DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                );
            """)
        conn.commit()

@app.on_event("startup")
def on_startup():
    init_db()


# ── Session persistence helpers ─────────────────────────────────────────
def save_session(state: dict, session_id: str = None) -> str:
    """
    Inserts a new session row (if session_id is None, generates one) or
    updates an existing one. Returns the session_id either way.

    ON CONFLICT ... DO UPDATE is Postgres' "upsert" — insert if the row
    doesn't exist yet, update it if it does, all in a single statement
    instead of a separate SELECT-then-INSERT-or-UPDATE round trip.
    """
    sid = session_id or str(uuid.uuid4())
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO research_sessions
                    (session_id, topic, findings, analysis, report,
                     steps_completed, retries, errors, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (session_id) DO UPDATE SET
                    findings = EXCLUDED.findings,
                    analysis = EXCLUDED.analysis,
                    report = EXCLUDED.report,
                    steps_completed = EXCLUDED.steps_completed,
                    retries = EXCLUDED.retries,
                    errors = EXCLUDED.errors,
                    updated_at = now();
            """, (
                sid,
                state["topic"],
                state.get("findings"),
                state.get("analysis"),
                state.get("report"),
                state.get("steps_completed", []),
                json.dumps(state.get("retries", {})),
                state.get("errors", []),
            ))
        conn.commit()
    return sid


def load_session(session_id: str) -> dict | None:
    """Fetches a session row and reshapes it back into the same dict
    shape agent.py's functions expect (topic/findings/analysis/etc)."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM research_sessions WHERE session_id = %s;",
                (session_id,)
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "topic": row["topic"],
                "findings": row["findings"],
                "analysis": row["analysis"],
                "report": row["report"],
                "steps_completed": row["steps_completed"] or [],
                "retries": row["retries"] or {},
                "errors": row["errors"] or [],
            }


# ── Serve the frontend HTML at root ───────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = Path(__file__).parent / "researchcrew_v4.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── Request/response shapes ────────────────────────────────────────────
class StartRequest(BaseModel):
    topic: str

class ReviewRequest(BaseModel):
    session_id: str
    decision: str
    feedback: Optional[str] = None


# ── POST /research/start ───────────────────────────────────────────────
@app.post("/research/start")
def research_start(req: StartRequest):
    state = start_research(req.topic)

    if state["errors"]:
        raise HTTPException(status_code=500, detail=state["errors"])

    session_id = save_session(state)

    return {
        "session_id": session_id,
        "findings": state["findings"],
        "analysis": state["analysis"],
        "steps_completed": state["steps_completed"]
    }


# ── POST /research/review ──────────────────────────────────────────────
@app.post("/research/review")
def research_review(req: ReviewRequest):
    state = load_session(req.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.decision == "approve":
        state = continue_after_approval(state)
        save_session(state, session_id=req.session_id)

        if state["errors"]:
            raise HTTPException(status_code=500, detail=state["errors"])

        return {
            "session_id": req.session_id,
            "report": state["report"],
            "steps_completed": state["steps_completed"]
        }

    elif req.decision == "reject":
        if not req.feedback:
            raise HTTPException(status_code=400, detail="Feedback required when rejecting")

        state = rerun_analyst_with_feedback(state, req.feedback)
        save_session(state, session_id=req.session_id)

        if state["errors"]:
            raise HTTPException(status_code=500, detail=state["errors"])

        return {
            "session_id": req.session_id,
            "analysis": state["analysis"],
            "steps_completed": state["steps_completed"]
        }

    else:
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)