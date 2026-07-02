import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from agent import start_research, rerun_analyst_with_feedback, continue_after_approval

# ── App setup ─────────────────────────────────────────────────────────
app = FastAPI(title="ResearchCrew API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session store ──────────────────────────────────────────────────────
SESSIONS: dict = {}

# ── Serve the frontend HTML at root ───────────────────────────────────
# Fix for the CORS problem: instead of opening the HTML file directly from
# disk (file://) and having it try to call localhost:8000, we serve the HTML
# FROM FastAPI itself at http://127.0.0.1:8000/. The browser sees both the
# page and the API as the same origin — no cross-origin request at all.
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

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = state

    return {
        "session_id": session_id,
        "findings": state["findings"],
        "analysis": state["analysis"],
        "steps_completed": state["steps_completed"]
    }

# ── POST /research/review ──────────────────────────────────────────────
@app.post("/research/review")
def research_review(req: ReviewRequest):
    state = SESSIONS.get(req.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.decision == "approve":
        state = continue_after_approval(state)
        SESSIONS[req.session_id] = state

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
        SESSIONS[req.session_id] = state

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