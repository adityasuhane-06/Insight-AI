import traceback
"""
Quality Check Node — evaluates the completeness and quality of the analysis.
Returns a score 0-1. If score < threshold AND retry_count < max_retries,
the conditional router will send execution back to the researcher node.
"""
import json
import logging
from langchain_core.messages import HumanMessage
from workflow.state import ResearchState
from services.llm import get_llm, extract_text
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REQUIRED_SECTIONS = [
    "company_overview",
    "products_services",
    "target_customers",
    "business_signals",
    "risks_challenges",
    "discovery_questions",
    "outreach_strategy",
    "unknowns",
    "sources",
]


def _heuristic_score(analysis: dict) -> float:
    """
    Fast heuristic score (0-1) based on content richness.
    Used as a fallback if LLM scoring fails.
    """
    if not analysis:
        return 0.0

    score = 0.0
    weights = {
        "company_overview": 0.15,
        "products_services": 0.15,
        "target_customers": 0.10,
        "business_signals": 0.15,
        "risks_challenges": 0.10,
        "discovery_questions": 0.15,
        "outreach_strategy": 0.10,
        "unknowns": 0.05,
        "sources": 0.05,
    }

    for key, weight in weights.items():
        value = analysis.get(key, "")
        if isinstance(value, list):
            if len(value) >= 2:
                score += weight
            elif len(value) == 1:
                score += weight * 0.5
        elif isinstance(value, str):
            word_count = len(value.split())
            if word_count >= 30:
                score += weight
            elif word_count >= 10:
                score += weight * 0.5

    return round(min(score, 1.0), 2)


async def quality_check_node(state: ResearchState) -> dict:
    """
    Evaluates analysis quality using LLM + heuristics.
    Returns: { quality_score, quality_feedback, current_node }
    """
    logger.info(f"[quality_check] Evaluating analysis (retry #{state.get('retry_count', 0)})")

    analysis = state.get("analysis", {})

    # Fast heuristic check first
    heuristic = _heuristic_score(analysis)
    logger.info(f"[quality_check] Heuristic score: {heuristic}")

    # If heuristic is high, skip LLM scoring to save tokens
    if heuristic >= 0.85:
        logger.info("[quality_check] Heuristic score sufficient — skipping LLM eval")
        return {
            "quality_score": heuristic,
            "quality_feedback": "Analysis is comprehensive.",
            "current_node": "quality_check",
        }

    # LLM-based quality evaluation
    llm = get_llm()
    analysis_summary = json.dumps(
        {k: (v[:200] if isinstance(v, str) else v) for k, v in analysis.items()},
        indent=2
    )

    prompt = f"""You are a quality assurance reviewer for sales research reports.

Company: {state['company_name']}
Research Objective: {state['objective']}

Evaluate this analysis for completeness and quality:
{analysis_summary}

Score each section (0-10) and return a JSON response:
{{
    "overall_score": <float 0.0-1.0>,
    "feedback": "<specific feedback on what is missing or weak>",
    "missing_sections": ["list of weak/missing sections"],
    "is_sufficient": <true if score >= 0.65, else false>
}}

Be strict. A good report must have:
- Specific, factual company overview (not generic)
- At least 3 concrete products/services
- Clear target customer segments
- At least 1 concrete business signal (not vague)
- 5+ specific discovery questions
- Actionable outreach strategy
- Real source URLs

Return ONLY the JSON object."""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = extract_text(response)

        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)
        score = float(result.get("overall_score", heuristic))
        feedback = result.get("feedback", "")

        # Blend heuristic + LLM score
        final_score = round((score * 0.7 + heuristic * 0.3), 2)
        logger.info(f"[quality_check] LLM score: {score}, blended: {final_score}")

        return {
            "quality_score": final_score,
            "quality_feedback": feedback,
            "current_node": "quality_check",
        }

    except Exception as e:
        logger.warning(f"[quality_check] LLM scoring failed, using heuristic: {e}")
        return {
            "quality_score": heuristic,
            "quality_feedback": f"Auto-scored (LLM eval failed): {e}",
            "current_node": "quality_check",
        }


def quality_router(state: ResearchState) -> str:
    """
    Conditional routing function.
    - If error → error_handler
    - If score >= threshold OR max retries reached → report_gen
    - Otherwise → researcher (retry with potentially expanded queries)
    """
    if state.get("error") and not state.get("analysis"):
        logger.info("[router] Routing to error_handler (hard error)")
        return "error_handler"

    score = state.get("quality_score", 0.0)
    retry_count = state.get("retry_count", 0)
    threshold = settings.quality_threshold
    max_retries = settings.max_retries

    if score >= threshold:
        logger.info(f"[router] Quality sufficient ({score:.2f} >= {threshold}) → report_gen")
        return "report_gen"

    if retry_count >= max_retries:
        logger.info(f"[router] Max retries reached ({retry_count}) → report_gen with partial data")
        return "report_gen"

    logger.info(f"[router] Quality insufficient ({score:.2f} < {threshold}), retry #{retry_count + 1} → researcher")
    return "researcher"
