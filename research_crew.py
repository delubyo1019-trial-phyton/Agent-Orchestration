import os
import litellm
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import TavilySearchTool

load_dotenv()

# Force LiteLLM to drop unsupported params (fixes cache_breakpoint issue with Groq)
litellm.drop_params = True
os.environ["LITELLM_DROP_PARAMS"] = "true"

# ── Model ────────────────────────────────────────────────────────────────────
llm = "groq/llama-3.3-70b-versatile"

# ── Tools ────────────────────────────────────────────────────────────────────
search_tool = TavilySearchTool(
    api_key=os.getenv("TAVILY_API_KEY")
)

# ── Agents ───────────────────────────────────────────────────────────────────
scout = Agent(
    role="Research Scout",
    goal="Find the most relevant, current, and credible information on the given topic",
    backstory="""You are an expert research scout with years of experience finding 
    high-quality information across the web. You know how to identify credible sources, 
    spot the most relevant results, and collect raw findings efficiently. 
    You don't analyze — you find and report what exists.""",
    tools=[search_tool],
    llm=llm,
    verbose=True,
    max_iter=5
)

analyst = Agent(
    role="Research Analyst",
    goal="Extract key insights and patterns from raw research findings",
    backstory="""You are a senior research analyst who specializes in synthesizing 
    information from multiple sources. Given raw findings, you identify the most 
    important insights, spot patterns and trends, flag contradictions, and organize 
    information into a clear structure. You don't search — you analyze what the Scout found.""",
    tools=[],
    llm=llm,
    verbose=True,
    max_iter=3
)

writer = Agent(
    role="Report Writer",
    goal="Write a clear, structured, professional briefing report from analyzed insights",
    backstory="""You are a professional report writer who transforms research insights 
    into polished, actionable briefing documents. You write clearly, structure 
    information logically, and make complex topics accessible. Your reports always 
    include an executive summary, key sections, and clear takeaways.""",
    tools=[],
    llm=llm,
    verbose=True,
    max_iter=3
)

# ── Tasks ────────────────────────────────────────────────────────────────────
def create_tasks(topic: str):

    search_task = Task(
        description=f"""Search the web thoroughly for information about: {topic}

        Your job:
        1. Run multiple searches with different angle queries on this topic
        2. Collect the most relevant and recent findings
        3. Note the sources (URLs/titles) for each key finding
        4. Focus on facts, data, recent developments, and expert opinions
        
        Return a structured list of findings with their sources.""",
        expected_output="""A structured list of raw research findings, each with:
        - The key finding or fact
        - The source it came from
        - Why it's relevant to the topic
        Minimum 5 distinct findings from different sources.""",
        agent=scout
    )

    analysis_task = Task(
        description=f"""Analyze the research findings about: {topic}

        You will receive raw findings from the Research Scout.
        Your job:
        1. Identify the 3-5 most important insights
        2. Spot any patterns, trends, or recurring themes
        3. Note any contradictions or areas of uncertainty
        4. Prioritize findings by importance and relevance
        5. Structure the insights logically
        
        Do NOT search for new information — only analyze what was found.""",
        expected_output="""A structured analysis containing:
        - Top 3-5 key insights (clearly stated)
        - 2-3 patterns or trends identified
        - Any notable contradictions or gaps
        - Prioritized list of what matters most""",
        agent=analyst,
        context=[search_task]
    )

    report_task = Task(
        description=f"""Write a professional briefing report on: {topic}

        You will receive analyzed insights from the Research Analyst.
        Your job:
        1. Write a clear executive summary (2-3 sentences)
        2. Structure the main findings into logical sections
        3. Include specific facts and data points from the research
        4. End with 3-5 clear, actionable key takeaways
        5. List the main sources referenced
        
        Write for a professional audience — clear, concise, no fluff.""",
        expected_output="""A complete briefing report with:
        ## Executive Summary
        (2-3 sentences capturing the essence)
        
        ## Key Findings
        (3-4 sections with headers, each covering a major aspect)
        
        ## Key Takeaways
        (3-5 bullet points — the most important things to know)
        
        ## Sources
        (list of main sources referenced)""",
        agent=writer,
        context=[search_task, analysis_task]
    )

    return search_task, analysis_task, report_task


# ── Crew ─────────────────────────────────────────────────────────────────────
def run_research(topic: str) -> str:
    """
    Runs the full research crew on a given topic.
    Returns the final briefing report as a string.
    """
    search_task, analysis_task, report_task = create_tasks(topic)

    crew = Crew(
        agents=[scout, analyst, writer],
        tasks=[search_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return str(result)


# ── Test run ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    topic = "Latest developments in AI agent frameworks 2026"
    print(f"\n{'='*60}")
    print(f"RESEARCH TOPIC: {topic}")
    print(f"{'='*60}\n")
    report = run_research(topic)
    print(f"\n{'='*60}")
    print("FINAL REPORT:")
    print(f"{'='*60}\n")
    print(report)