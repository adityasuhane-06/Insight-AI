"""
LangGraph graph definition and compilation.

Workflow shape:
  planner → researcher → analyzer → quality_check
                ↑_____(retry)____________|
                                         ↓
                                    report_gen → END
                                         ↓
                                   error_handler → END

Conditional routing at quality_check:
  - score >= threshold OR max retries → report_gen
  - score < threshold AND retries left → researcher (retry)
  - hard error → error_handler
"""
import logging
from langgraph.graph import StateGraph, END

from workflow.state import ResearchState
from workflow.nodes.planner import planner_node
from workflow.nodes.researcher import research_node
from workflow.nodes.analyzer import analysis_node
from workflow.nodes.quality_check import quality_check_node, quality_router
from workflow.nodes.report_gen import report_gen_node
from workflow.nodes.error_handler import error_handler_node

logger = logging.getLogger(__name__)


def _increment_retry(state: ResearchState) -> dict:
    """Increment retry counter before going back to researcher."""
    return {"retry_count": state.get("retry_count", 0) + 1}


def build_graph():
    """
    Build and compile the LangGraph research workflow.
    Returns a compiled graph ready for invocation.
    """
    workflow = StateGraph(ResearchState)

    # ── Register nodes ────────────────────────────────────────────────
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", research_node)
    workflow.add_node("analyzer", analysis_node)
    workflow.add_node("quality_check", quality_check_node)
    workflow.add_node("report_gen", report_gen_node)
    workflow.add_node("error_handler", error_handler_node)
    workflow.add_node("increment_retry", _increment_retry)

    # ── Define edges ──────────────────────────────────────────────────
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "analyzer")
    workflow.add_edge("analyzer", "quality_check")

    # Conditional routing from quality_check
    workflow.add_conditional_edges(
        "quality_check",
        quality_router,
        {
            "report_gen": "report_gen",
            "researcher": "increment_retry",  # first increment, then retry
            "error_handler": "error_handler",
        }
    )

    # After retry increment, go back to researcher
    workflow.add_edge("increment_retry", "researcher")

    # Terminal edges
    workflow.add_edge("report_gen", END)
    workflow.add_edge("error_handler", END)

    graph = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")
    return graph


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
