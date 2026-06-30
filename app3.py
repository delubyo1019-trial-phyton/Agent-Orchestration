import streamlit as st
import html
import os
from dotenv import load_dotenv
from agent import scout_agent, analyst_agent, writer_agent

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchCrew — by GP CUBE",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:           #FFFFFF;
    --surface:      #F7F8FC;
    --border:       #E2E6EF;
    --amber:        #D97706;
    --violet:       #7C3AED;
    --success:      #059669;
    --text-primary: #111827;
    --text-muted:   #6B7280;
    --text-dim:     #9CA3AF;
    --glow-amber:   0 0 24px rgba(217,119,6,0.18);
}

.stApp { background-color: var(--bg) !important; font-family: 'Inter', sans-serif; }
.stApp > header { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1200px; }
h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: var(--text-primary) !important; }
p, li { color: var(--text-primary) !important; }
hr { border-color: var(--border) !important; }
strong { color: var(--text-primary) !important; }

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

.stTextArea textarea, .stTextInput > div > div > input {
    background-color: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput > div > div > input:focus {
    border-color: var(--amber) !important;
    box-shadow: var(--glow-amber) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #D97706, #7C3AED) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--glow-amber) !important;
    color: #fff !important;
}

/* ── HEADER ── */
.rc-header {
    background: linear-gradient(135deg, var(--surface) 0%, #EDEEF8 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
}
.rc-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--amber), var(--violet), var(--amber));
    background-size: 200% 100%;
    animation: shimmer 4s linear infinite;
}
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
.rc-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.7rem; font-weight: 700;
    background: linear-gradient(90deg, var(--amber), var(--violet));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0 0 0.25rem 0; display: inline-block;
}
.rc-badge {
    display: inline-block;
    background: rgba(217,119,6,0.07);
    border: 1px solid rgba(217,119,6,0.28);
    color: var(--amber); -webkit-text-fill-color: var(--amber);
    font-size: 0.65rem; font-family: 'JetBrains Mono', monospace;
    padding: 2px 7px; border-radius: 4px; margin-left: 0.6rem;
    vertical-align: middle; letter-spacing: 0.8px;
}
.rc-subtitle {
    color: var(--text-muted); -webkit-text-fill-color: var(--text-muted);
    font-size: 0.87rem; margin: 0;
}

/* ── PIPELINE NODES ── */
.pipeline-wrap {
    display: flex; align-items: center;
    padding: 1rem 1.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.pipeline-node { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; flex: 1; }
.node-circle {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; border: 2px solid var(--border);
    color: var(--text-dim); background: var(--bg);
    transition: all 0.3s ease;
}
.node-circle.done  { border-color: var(--success); color: var(--success); background: rgba(5,150,105,0.07); }
.node-circle.active {
    border-color: var(--amber); color: var(--amber);
    background: rgba(217,119,6,0.07);
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 8px rgba(217,119,6,0.22); }
    50%      { box-shadow: 0 0 20px rgba(217,119,6,0.55); }
}
.node-label {
    font-size: 0.62rem; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: var(--text-dim); -webkit-text-fill-color: var(--text-dim);
}
.node-label.done   { color: var(--success); -webkit-text-fill-color: var(--success); }
.node-label.active { color: var(--amber);   -webkit-text-fill-color: var(--amber); }
.pipeline-connector       { height: 2px; flex: 0.25; background: var(--border); margin-bottom: 1.4rem; }
.pipeline-connector.done  { background: var(--success); }

/* ── SECTION LABEL ── */
.sg-label {
    color: var(--text-muted); -webkit-text-fill-color: var(--text-muted);
    font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.4rem;
}

/* ── REVIEW BANNER ── */
.review-banner {
    background: rgba(217,119,6,0.05);
    border: 1px solid rgba(217,119,6,0.32);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 1px;
    color: var(--amber); -webkit-text-fill-color: var(--amber);
}

/* ── ANALYSIS DISPLAY ── */
.analysis-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    font-size: 0.88rem;
    line-height: 1.7;
    color: var(--text-primary);
    -webkit-text-fill-color: var(--text-primary);
    white-space: pre-wrap;
    font-family: 'Inter', sans-serif;
    max-height: 400px;
    overflow-y: auto;
}

/* ── REPORT CARD ── */
.report-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin: 1rem 0;
}

/* ── LOG ENTRIES ── */
.log-entry {
    font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted); -webkit-text-fill-color: var(--text-muted);
    padding: 0.25rem 0; border-bottom: 1px solid var(--border);
}
.log-entry.done  { color: var(--success); -webkit-text-fill-color: var(--success); }
.log-entry.active{ color: var(--amber);   -webkit-text-fill-color: var(--amber); }
.log-entry.human { color: var(--violet);  -webkit-text-fill-color: var(--violet); }

/* ── EMPTY STATE ── */
.empty-state {
    text-align: center; padding: 3rem 1rem;
    border: 1px dashed var(--border); border-radius: 12px;
    margin-top: 1rem;
}
.empty-icon  { font-size: 2.5rem; opacity: 0.35; margin-bottom: 0.8rem; }
.empty-title {
    font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 600;
    color: var(--text-muted); -webkit-text-fill-color: var(--text-muted);
}
.empty-sub { font-size: 0.8rem; color: var(--text-dim); -webkit-text-fill-color: var(--text-dim); margin-top: 0.3rem; }
</style>
""", unsafe_allow_html=True)


# ── Pipeline visualization ────────────────────────────────────────────────────
def render_pipeline(steps_completed: list, active_node: str = ""):
    stages = [
        ("scout",        "🔍", "SCOUT"),
        ("analyst",      "🧠", "ANALYST"),
        ("human_review", "👤", "REVIEW"),
        ("writer",       "✍️",  "WRITER"),
    ]
    html_parts = []
    for i, (key, icon, label) in enumerate(stages):
        if key in steps_completed:
            c_class = "done"
            content = "✓"
        elif active_node == key:
            c_class = "active"
            content = icon
        else:
            c_class = ""
            content = icon

        html_parts.append(f"""
<div class="pipeline-node">
  <div class="node-circle {c_class}">{content}</div>
  <div class="node-label {c_class}">{label}</div>
</div>""")

        if i < len(stages) - 1:
            conn = "done" if key in steps_completed else ""
            html_parts.append(f'<div class="pipeline-connector {conn}"></div>')

    st.markdown(
        f'<div class="pipeline-wrap">{"".join(html_parts)}</div>',
        unsafe_allow_html=True
    )


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "stage": "idle",
        "topic": "",
        "findings": None,
        "analysis": None,
        "report": None,
        "steps_completed": [],
        "retries": {},
        "human_decision": None,
        "rejection_count": 0,
        "agent_log": [],
        "errors": [],
        "show_feedback": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Log helper ────────────────────────────────────────────────────────────────
def add_log(msg: str, entry_type: str = ""):
    st.session_state.agent_log.append({"msg": msg, "type": entry_type})


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:0.5rem 0 1rem 0;">
  <div style="font-family:'Inter',sans-serif;font-size:1.1rem;font-weight:700;
      background:linear-gradient(90deg,#D97706,#7C3AED);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
    🔬 ResearchCrew
  </div>
  <div style="font-size:0.7rem;font-family:'JetBrains Mono',monospace;
      color:#6B7280;letter-spacing:0.8px;margin-top:0.2rem;-webkit-text-fill-color:#6B7280;">
    by GP CUBE · v1.0
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("**🤖 The Crew**")
    st.markdown("""
- 🔍 **Scout** — Live web search + source curation
- 🧠 **Analyst** — Insight extraction + pattern detection
- 👤 **You** — Human review + feedback
- ✍️ **Writer** — Structured report generation
""")

    st.divider()
    st.markdown("**📋 Activity Log**")

    log_entries = st.session_state.agent_log[-12:]
    if log_entries:
        log_html = "".join(
            f'<div class="log-entry {e["type"]}">{html.escape(e["msg"])}</div>'
            for e in log_entries
        )
        st.markdown(log_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="log-entry">Waiting for crew deployment...</div>',
                    unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 New Research", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rc-header">
  <div>
    <span class="rc-title">🔬 ResearchCrew</span>
    <span class="rc-badge">BETA</span>
    <span class="rc-badge" style="border-color:rgba(124,58,237,0.28);
        background:rgba(124,58,237,0.07);color:#6D28D9;-webkit-text-fill-color:#6D28D9;">
      GROQ · LLAMA 3.3 70B
    </span>
  </div>
  <p class="rc-subtitle">by GP CUBE &nbsp;·&nbsp;
    Multi-agent research assistant — Scout → Analyst → Human Review → Writer
  </p>
</div>
""", unsafe_allow_html=True)


# ── Pipeline visualization ────────────────────────────────────────────────────
stage_to_node = {
    "idle":      "",
    "scouting":  "scout",
    "analyzing": "analyst",
    "review":    "human_review",
    "writing":   "writer",
    "complete":  "",
    "error":     "",
}
render_pipeline(
    st.session_state.steps_completed,
    stage_to_node.get(st.session_state.stage, "")
)


# ────────────────────────────────────────────────────────────────────────────
# STAGE ROUTER
# ────────────────────────────────────────────────────────────────────────────

# ── IDLE ─────────────────────────────────────────────────────────────────────
if st.session_state.stage == "idle":
    st.markdown('<div class="sg-label">Research Topic</div>', unsafe_allow_html=True)
    topic = st.text_area(
        label="topic",
        placeholder=(
            "e.g. Latest developments in AI agent frameworks 2026\n"
            "or: What businesses can I start in the Philippines with 300K pesos?\n"
            "or: How does Snowflake handle data governance at enterprise scale?"
        ),
        height=110,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        go = st.button("🔬 Deploy Crew", type="primary", use_container_width=True)

    if go and topic.strip():
        st.session_state.topic = topic.strip()
        add_log(f"▶ Research started: {topic.strip()[:60]}...", "active")
        st.session_state.stage = "scouting"
        st.rerun()
    elif go:
        st.warning("Please enter a research topic first.")

    st.markdown("""
<div class="empty-state">
  <div class="empty-icon">🔬</div>
  <div class="empty-title">Deploy your research crew</div>
  <div class="empty-sub">Enter a topic above → Scout searches → Analyst extracts insights → You review → Writer reports</div>
</div>
""", unsafe_allow_html=True)


# ── SCOUTING ──────────────────────────────────────────────────────────────────
elif st.session_state.stage == "scouting":
    st.info(f"🔍 **Scout** is scanning the web for: *{st.session_state.topic}*")
    add_log("🔍 Scout deployed — scanning web...", "active")

    with st.spinner("Scout is searching..."):
        try:
            findings = scout_agent(st.session_state.topic)
            MIN_LEN = 200
            if len(findings) < MIN_LEN:
                add_log(f"⚠ Thin findings ({len(findings)} chars) — running broader search", "active")
                broader = scout_agent(
                    f"{st.session_state.topic} overview recent developments"
                )
                findings = (
                    f"=== Primary Search ===\n{findings}\n\n"
                    f"=== Broader Search ===\n{broader}"
                )
                add_log("✓ Merged findings from broader search", "done")

            st.session_state.findings = findings
            st.session_state.steps_completed.append("scout")
            st.session_state.retries["scout"] = 0
            add_log(f"✓ Scout complete — {len(findings):,} chars collected", "done")
        except Exception as e:
            st.session_state.errors.append(str(e))
            add_log(f"✗ Scout failed: {str(e)[:80]}", "")
            st.session_state.stage = "error"
            st.rerun()

    st.session_state.stage = "analyzing"
    st.rerun()


# ── ANALYZING ─────────────────────────────────────────────────────────────────
elif st.session_state.stage == "analyzing":
    st.info("🧠 **Analyst** is extracting key insights from Scout's findings...")
    add_log("🧠 Analyst processing findings...", "active")

    with st.spinner("Analyst is working..."):
        try:
            analysis = analyst_agent(
                st.session_state.topic,
                st.session_state.findings
            )
            st.session_state.analysis = analysis
            st.session_state.steps_completed.append("analyst")
            st.session_state.retries["analyst"] = 0
            add_log("✓ Analyst complete — insights extracted", "done")
        except Exception as e:
            st.session_state.errors.append(str(e))
            add_log(f"✗ Analyst failed: {str(e)[:80]}", "")
            st.session_state.stage = "error"
            st.rerun()

    st.session_state.stage = "review"
    st.rerun()


# ── REVIEW (human-in-the-loop) ────────────────────────────────────────────────
elif st.session_state.stage == "review":
    rev_count = st.session_state.rejection_count

    # Review banner
    revision_tag = f" — Revision #{rev_count}" if rev_count > 0 else ""
    st.markdown(
        f'<div class="review-banner">▶ ANALYST OUTPUT READY{revision_tag} &nbsp;·&nbsp; YOUR REVIEW REQUIRED</div>',
        unsafe_allow_html=True
    )

    # Analysis display
    st.markdown('<div class="sg-label">Analyst Findings</div>', unsafe_allow_html=True)
    analysis_escaped = html.escape(st.session_state.analysis)
    st.markdown(
        f'<div class="analysis-box">{analysis_escaped}</div>',
        unsafe_allow_html=True
    )

    # Decision buttons
    st.markdown('<div class="sg-label" style="margin-top:1rem;">Your Decision</div>',
                unsafe_allow_html=True)
    col_approve, col_reject = st.columns(2)

    with col_approve:
        if st.button("✅ Approve — Send to Writer", type="primary", use_container_width=True):
            st.session_state.steps_completed.append("human_review")
            st.session_state.human_decision = "approved"
            add_log("👤 Human approved — proceeding to Writer", "human")
            st.session_state.show_feedback = False
            st.session_state.stage = "writing"
            st.rerun()

    with col_reject:
        if st.button("↩ Revise with Feedback", use_container_width=True):
            st.session_state.show_feedback = True
            st.rerun()

    # Feedback form (shown after clicking Revise)
    if st.session_state.show_feedback:
        st.divider()
        st.markdown('<div class="sg-label">Feedback for Analyst</div>', unsafe_allow_html=True)
        feedback = st.text_input(
            label="feedback",
            placeholder="e.g. Focus more on AI-related opportunities and ignore traditional businesses",
            label_visibility="collapsed",
            key="feedback_text"
        )
        if st.button("🔄 Re-run Analyst with Feedback", use_container_width=True) and feedback:
            add_log(f"👤 Rejected — feedback: {feedback[:60]}...", "human")
            feedback_prompt = (
                f"{st.session_state.findings}\n\n"
                f"IMPORTANT: Previous analysis was rejected by the human reviewer.\n"
                f"Human feedback: {feedback}\n"
                f"Please re-analyze with this guidance, prioritizing the feedback."
            )
            with st.spinner("Re-running Analyst with your feedback..."):
                try:
                    new_analysis = analyst_agent(
                        st.session_state.topic, feedback_prompt
                    )
                    st.session_state.analysis = new_analysis
                    st.session_state.rejection_count += 1
                    st.session_state.show_feedback = False
                    add_log(
                        f"✓ Analyst revised (revision #{st.session_state.rejection_count})",
                        "done"
                    )
                except Exception as e:
                    st.error(f"Re-run failed: {e}")
            st.rerun()


# ── WRITING ───────────────────────────────────────────────────────────────────
elif st.session_state.stage == "writing":
    st.info("✍️ **Writer** is composing your briefing report...")
    add_log("✍️ Writer drafting report...", "active")

    with st.spinner("Writer is working..."):
        try:
            report = writer_agent(
                st.session_state.topic,
                st.session_state.findings,
                st.session_state.analysis
            )
            st.session_state.report = report
            st.session_state.steps_completed.append("writer")
            st.session_state.retries["writer"] = 0
            add_log("✓ Report complete — ready to read", "done")
        except Exception as e:
            st.session_state.errors.append(str(e))
            add_log(f"✗ Writer failed: {str(e)[:80]}", "")
            st.session_state.stage = "error"
            st.rerun()

    st.session_state.stage = "complete"
    st.rerun()


# ── COMPLETE ──────────────────────────────────────────────────────────────────
elif st.session_state.stage == "complete":
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Steps", len(st.session_state.steps_completed))
    col2.metric("Revisions", st.session_state.rejection_count)
    col3.metric("Decision", st.session_state.human_decision or "—")
    col4.metric("Errors", len(st.session_state.errors))

    st.divider()
    st.markdown('<div class="sg-label">Briefing Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown(st.session_state.report)
    st.markdown('</div>', unsafe_allow_html=True)


# ── ERROR ─────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "error":
    st.error("❌ The research pipeline encountered an error.")
    if st.session_state.errors:
        for err in st.session_state.errors:
            st.code(err)
    st.info("Click **🔄 New Research** in the sidebar to try again.")