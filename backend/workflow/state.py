"""
ResearchState — the shared graph state passed between all LangGraph nodes.
"""
from typing import TypedDict, Optional


class ResearchState(TypedDict):
    # Input
    session_id: str
    company_name: str
    website: str
    objective: str

    # Planner output
    plan: list[str]           # list of search queries

    # Researcher output
    raw_research: list[dict]  # [{query, results: [{title, url, content}]}]

    # Analyzer output
    analysis: dict            # structured dict with all 9 report sections

    # Quality check
    quality_score: float      # 0.0 – 1.0
    quality_feedback: str     # improvement suggestions if score low

    # Final report
    report_markdown: str      # polished markdown report
    report_json: str          # JSON string of report sections

    # Control flow
    retry_count: int
    error: Optional[str]
    current_node: str         # name of node currently executing (for SSE)
    status: str               # pending | running | completed | failed
