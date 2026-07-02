import os
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

# ── Clients ──────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


# ── Core LLM call ─────────────────────────────────────────────────────────────
def call_llm(system_prompt: str, user_message: str) -> str:
    """
    Makes a single call to the LLM.
    system_prompt: defines who the agent is and how it should behave
    user_message: the actual task or content to process
    Returns the model's response as a plain string.
    """
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


# ── Agent 1: Scout ────────────────────────────────────────────────────────────
def scout_agent(topic: str) -> str:
    """
    Searches the web for information on the topic using Tavily.
    Returns raw search findings as a formatted string.
    """
    print("\n[SCOUT] Searching the web...")

    # Run the web search
    search_results = tavily_client.search(
        query=topic,
        max_results=5,
        search_depth="advanced"
    )

    # Format raw results into a readable string
    raw_findings = []
    for i, result in enumerate(search_results["results"], 1):
        raw_findings.append(
            f"Source {i}: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Content: {result['content']}\n"
        )

    raw_text = "\n---\n".join(raw_findings)

    # Ask the LLM to organize and summarize the raw search results
    system_prompt = """You are a Research Scout. Your job is to organize raw web search 
    results into a clean, structured list of findings. For each finding:
    - State the key fact or insight clearly
    - Note the source title and URL
    - Explain why it's relevant to the topic
    Keep it factual — do not analyze or editorialize."""

    user_message = f"""Topic: {topic}

Raw search results:
{raw_text}

Organize these into a structured list of key findings with their sources."""

    findings = call_llm(system_prompt, user_message)
    print(f"[SCOUT] Found and organized {len(search_results['results'])} sources.")
    return findings


# ── Agent 2: Analyst ──────────────────────────────────────────────────────────
def analyst_agent(topic: str, findings: str) -> str:
    """
    Takes the Scout's raw findings and extracts key insights.
    Returns structured analysis as a string.
    """
    print("\n[ANALYST] Analyzing findings...")

    system_prompt = """You are a Research Analyst. You receive raw research findings 
    and extract meaningful insights. Your job is to:
    - Identify the 3-5 most important insights
    - Spot patterns, trends, or recurring themes
    - Flag any contradictions or areas of uncertainty
    - Prioritize findings by importance
    Do NOT search for new information. Only analyze what you receive."""

    user_message = f"""Topic: {topic}

Research findings from the Scout:
{findings}

Extract the key insights and patterns from these findings."""

    analysis = call_llm(system_prompt, user_message)
    print("[ANALYST] Analysis complete.")
    return analysis


# ── Agent 3: Writer ───────────────────────────────────────────────────────────
def writer_agent(topic: str, findings: str, analysis: str) -> str:
    """
    Takes findings + analysis and writes a structured briefing report.
    Returns the final report as a string.
    """
    print("\n[WRITER] Writing report...")

    system_prompt = """You are a professional Report Writer. You transform research 
    findings and analysis into polished, structured briefing reports. 
    Write clearly and concisely for a professional audience.
    Always include: Executive Summary, Key Findings sections, Key Takeaways, Sources."""

    user_message = f"""Topic: {topic}

Raw findings from Scout:
{findings}

Analysis from Analyst:
{analysis}

Write a complete professional briefing report."""

    report = call_llm(system_prompt, user_message)
    print("[WRITER] Report complete.")
    return report


# ── Orchestrator ──────────────────────────────────────────────────────────────
def run_research(topic: str) -> dict:
    """
    Stage 3: Adds conditional branching and retry logic on top of state management.
    
    Conditional branching: if Scout findings are too thin, search again with
    a different angle before proceeding — same concept as LangGraph's 
    conditional edges.
    
    Retry logic: if any agent fails, retry up to MAX_RETRIES times before
    giving up — same concept as LangGraph's RetryPolicy.
    """
    MAX_RETRIES = 3
    MIN_FINDINGS_LENGTH = 200  # minimum characters we expect from a good search

    state = {
        "topic": topic,
        "findings": None,
        "analysis": None,
        "report": None,
        "steps_completed": [],
        "retries": {},
        "errors": []
    }

    print(f"\n{'='*60}")
    print(f"RESEARCH TOPIC: {state['topic']}")
    print(f"{'='*60}")

    # ── Step 1: Scout with retry logic ───────────────────────────────────────
    for attempt in range(MAX_RETRIES):
        try:
            state["findings"] = scout_agent(state["topic"])

            # ── CONDITIONAL BRANCH: check quality of findings ─────────────
            if len(state["findings"]) < MIN_FINDINGS_LENGTH:
                print(f"[BRANCH] Findings too thin ({len(state['findings'])} chars). "
                      f"Searching with a broader angle...")
                # Search again with a different query angle
                broader_topic = f"{state['topic']} overview recent developments"
                additional_findings = scout_agent(broader_topic)
                # Merge both searches into one combined findings string
                state["findings"] = (
                    f"=== Primary Search ===\n{state['findings']}\n\n"
                    f"=== Broader Search ===\n{additional_findings}"
                )
                print("[BRANCH] Merged findings from both searches.")
            else:
                print(f"[BRANCH] Findings quality OK "
                      f"({len(state['findings'])} chars). Proceeding.")

            state["steps_completed"].append("scout")
            state["retries"]["scout"] = attempt
            print(f"[STATE] Steps completed: {state['steps_completed']}")
            break  # success — exit retry loop

        except Exception as e:
            print(f"[RETRY] Scout attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Scout failed after {MAX_RETRIES} attempts: {e}")
                return state

    # ── Step 2: Analyst with retry logic ─────────────────────────────────────
    for attempt in range(MAX_RETRIES):
        try:
            state["analysis"] = analyst_agent(state["topic"], state["findings"])
            state["steps_completed"].append("analyst")
            state["retries"]["analyst"] = attempt
            print(f"[STATE] Steps completed: {state['steps_completed']}")
            break

        except Exception as e:
            print(f"[RETRY] Analyst attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Analyst failed after {MAX_RETRIES} attempts: {e}")
                return state

# ── HUMAN-IN-THE-LOOP: approval after Analyst ────────────────────────────
    print("\n" + "─"*60)
    print("HUMAN REVIEW REQUIRED")
    print("─"*60)
    print("\nAnalyst produced the following analysis:")
    print(f"\n{state['analysis']}\n")
    print("─"*60)
    
    while True:
        decision = input(
            "\nOptions:\n"
            "  [A] Approve — proceed to Writer\n"
            "  [R] Reject — re-run Analyst with feedback\n"
            "  [Q] Quit — stop the pipeline\n"
            "Your choice (A/R/Q): "
        ).strip().upper()

        if decision == "A":
            print("[HUMAN] Approved. Proceeding to Writer...")
            state["human_decision"] = "approved"
            break

        elif decision == "R":
            feedback = input(
                "What should the Analyst focus on differently? "
            ).strip()
            print(f"[HUMAN] Re-running Analyst with feedback: '{feedback}'")
            state["human_decision"] = f"rejected — feedback: {feedback}"

            # Re-run Analyst with the human's feedback added to the prompt
            feedback_prompt = (
                f"{state['findings']}\n\n"
                f"Previous analysis was rejected. Human feedback: {feedback}\n"
                f"Please re-analyze with this guidance in mind."
            )
            for attempt in range(MAX_RETRIES):
                try:
                    state["analysis"] = analyst_agent(state["topic"], feedback_prompt)
                    print("[ANALYST] Re-analysis complete.")
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        state["errors"].append(f"Analyst re-run failed: {e}")
                        return state
            # Loop back to show the new analysis for approval
            print(f"\nUpdated analysis:\n{state['analysis']}\n")

        elif decision == "Q":
            print("[HUMAN] Pipeline stopped by user.")
            state["human_decision"] = "quit"
            state["steps_completed"].append("human_review_quit")
            return state

        else:
            print("Please enter A, R, or Q.")

    state["steps_completed"].append("human_review")

    # ── Step 3: Writer with retry logic ──────────────────────────────────────
    for attempt in range(MAX_RETRIES):
        try:
            state["report"] = writer_agent(
                state["topic"],
                state["findings"],
                state["analysis"]
            )
            state["steps_completed"].append("writer")
            state["retries"]["writer"] = attempt
            print(f"[STATE] Steps completed: {state['steps_completed']}")
            break

        except Exception as e:
            print(f"[RETRY] Writer attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Writer failed after {MAX_RETRIES} attempts: {e}")
                return state

    return state

# These three functions reuse your existing scout_agent / analyst_agent /
# writer_agent — nothing about those changes. What's new is HOW they're
# chained together: no input(), no while True, no blocking.
# ══════════════════════════════════════════════════════════════════════════

def start_research(topic: str) -> dict:
    """
    API-safe version of the first half of run_research().
    Runs Scout (with the thin-findings branch) + Analyst, then STOPS —
    it returns the state for human review instead of calling input().

    This is what the /research/start endpoint will call.
    """
    MAX_RETRIES = 3
    MIN_FINDINGS_LENGTH = 200

    state = {
        "topic": topic,
        "findings": None,
        "analysis": None,
        "report": None,
        "steps_completed": [],
        "retries": {},
        "errors": []
    }

    # ── Step 1: Scout with retry logic (identical logic to run_research) ────
    for attempt in range(MAX_RETRIES):
        try:
            state["findings"] = scout_agent(state["topic"])

            if len(state["findings"]) < MIN_FINDINGS_LENGTH:
                broader_topic = f"{state['topic']} overview recent developments"
                additional_findings = scout_agent(broader_topic)
                state["findings"] = (
                    f"=== Primary Search ===\n{state['findings']}\n\n"
                    f"=== Broader Search ===\n{additional_findings}"
                )

            state["steps_completed"].append("scout")
            state["retries"]["scout"] = attempt
            break

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Scout failed after {MAX_RETRIES} attempts: {e}")
                return state

    # ── Step 2: Analyst with retry logic ─────────────────────────────────────
    for attempt in range(MAX_RETRIES):
        try:
            state["analysis"] = analyst_agent(state["topic"], state["findings"])
            state["steps_completed"].append("analyst")
            state["retries"]["analyst"] = attempt
            break

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Analyst failed after {MAX_RETRIES} attempts: {e}")
                return state

    # NOTE: no human review here, no Writer call. We stop right after
    # Analyst and hand the state back — the frontend will show this
    # analysis to the human and decide what happens next.
    return state


def rerun_analyst_with_feedback(state: dict, feedback: str) -> dict:
    """
    API-safe version of the 'Reject' branch from run_research()'s
    human-in-the-loop section. Re-runs Analyst with the human's feedback
    folded into the prompt, same as before — just no input() around it.

    This is what /research/review calls when decision == 'reject'.
    """
    MAX_RETRIES = 3

    feedback_prompt = (
        f"{state['findings']}\n\n"
        f"Previous analysis was rejected. Human feedback: {feedback}\n"
        f"Please re-analyze with this guidance in mind."
    )

    for attempt in range(MAX_RETRIES):
        try:
            state["analysis"] = analyst_agent(state["topic"], feedback_prompt)
            state["retries"]["analyst"] = state["retries"].get("analyst", 0) + 1
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Analyst re-run failed: {e}")
    return state


def continue_after_approval(state: dict) -> dict:
    """
    API-safe version of the Writer step that used to run after the human
    typed 'A' for Approve. Takes the (now-approved) findings + analysis
    and produces the final report.

    This is what /research/review calls when decision == 'approve'.
    """
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            state["report"] = writer_agent(
                state["topic"],
                state["findings"],
                state["analysis"]
            )
            state["steps_completed"].append("writer")
            state["retries"]["writer"] = attempt
            break

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                state["errors"].append(f"Writer failed after {MAX_RETRIES} attempts: {e}")

    return state

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*60)
    print("MULTI-AGENT RESEARCH ASSISTANT — by GP CUBE")
    print("="*60)
    topic = input("\nWhat do you want to research? ").strip()
    
    if not topic:
        print("No topic entered. Exiting.")
        exit()

    state = run_research(topic)

    print(f"\n{'='*60}")
    print(f"STEPS COMPLETED: {state['steps_completed']}")
    print(f"RETRIES USED: {state['retries']}")
    print(f"HUMAN DECISION: {state['human_decision']}")
    if state['errors']:
        print(f"ERRORS: {state['errors']}")
    print(f"{'='*60}\n")
    if state["report"]:
        print(state["report"])