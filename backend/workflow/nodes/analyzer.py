import traceback
"""
Analyzer Node — reads raw research results and produces a structured
analysis covering all 9 required report sections.
"""
import json
import logging
from langchain_core.messages import HumanMessage
from workflow.state import ResearchState
from services.llm import get_llm, extract_text

logger = logging.getLogger(__name__)


def _format_research_for_llm(raw_research: list[dict]) -> str:
    """Format raw search results into a readable text block for the LLM."""
    sections = []
    for item in raw_research:
        if not item.get("results"):
            continue
        sections.append(f"\n### Query: {item['query']}")
        for r in item["results"][:3]:  # top 3 per query
            sections.append(f"**{r['title']}** ({r['url']})")
            sections.append(r["content"][:600])
            sections.append("---")
    return "\n".join(sections)


ANALYSIS_SCHEMA = {
    "company_overview": "string — 3-4 sentences covering founding, mission, size, stage",
    "products_services": "string — detailed description of their main offerings",
    "target_customers": "string — who they sell to (industries, company sizes, personas)",
    "business_signals": "string — recent funding, partnerships, expansions, product launches",
    "risks_challenges": "string — market, competitive, operational, or reputational risks",
    "discovery_questions": "list of 5-7 specific discovery questions for a sales call",
    "outreach_strategy": "string — recommended angle, tone, and messaging for outreach",
    "unknowns": "list of 3-5 things we couldn't find but should investigate",
    "sources": "list of URLs used as primary sources",
}


async def analysis_node(state: ResearchState) -> dict:
    """
    Analyzes raw research into structured sections using LLM.
    Returns: { analysis, current_node }
    """
    logger.info(f"[analyzer] Analyzing research for {state['company_name']}")

    llm = get_llm()
    research_text = _format_research_for_llm(state.get("raw_research", []))

    if not research_text.strip():
        logger.warning("[analyzer] No research content to analyze")
        return {
            "analysis": {},
            "current_node": "analyzer",
            "error": "No research content available",
        }

    prompt = f"""You are an expert sales intelligence analyst. Analyze the following research about a company and produce a structured JSON analysis.

Company: {state['company_name']}
Website: {state['website']}
Research Objective: {state['objective']}

=== RESEARCH DATA ===
{research_text}
=== END RESEARCH DATA ===

Produce a JSON object with EXACTLY these keys (all required):
{{
    "company_overview": "3-4 sentence company overview covering founding, mission, business model, size/stage",
    "products_services": "Detailed description of main products and services, including key features and pricing if known",
    "target_customers": "Who they sell to: industries, company sizes, buyer personas, use cases",
    "business_signals": "Recent signals: funding rounds, partnerships, acquisitions, product launches, leadership changes, market expansion",
    "risks_challenges": "Key risks: competitive threats, market challenges, operational concerns, public issues",
    "discovery_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"],
    "outreach_strategy": "Recommended sales outreach approach: angle, value prop, tone, suggested hook for this specific company",
    "unknowns": ["thing we couldn't find 1", "thing 2", "thing 3"],
    "sources": ["url1", "url2", "url3"]
}}

Rules:
- Be specific. Use actual facts from the research, not generic statements.
- discovery_questions must be specific to this company's situation.
- outreach_strategy must be tailored to the research objective: {state['objective']}
- sources must be actual URLs from the research, not placeholders.
- Return ONLY the JSON object — no markdown fences, no explanation."""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = extract_text(response)

        # Strip markdown fences
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:].strip()

        analysis = json.loads(content)

        # Validate required keys
        required_keys = list(ANALYSIS_SCHEMA.keys())
        missing = [k for k in required_keys if k not in analysis]
        if missing:
            logger.warning(f"[analyzer] Missing keys: {missing}")
            for k in missing:
                analysis[k] = "Not available" if k not in ("discovery_questions", "unknowns", "sources") else []

        logger.info("[analyzer] Analysis complete")
        return {
            "analysis": analysis,
            "current_node": "analyzer",
            "error": None,
        }

    except json.JSONDecodeError as e:
        logger.error(f"[analyzer] JSON parse error: {e}")
        # Return partial analysis
        return {
            "analysis": {
                "company_overview": f"Analysis of {state['company_name']} based on available research.",
                "products_services": "Unable to parse structured analysis — see raw report.",
                "target_customers": "Unknown",
                "business_signals": "Unknown",
                "risks_challenges": "Unknown",
                "discovery_questions": ["What are your main business challenges?"],
                "outreach_strategy": "Standard discovery call approach.",
                "unknowns": ["Full structured analysis failed — retry recommended"],
                "sources": [],
            },
            "current_node": "analyzer",
            "error": f"JSON parse error: {e}",
        }

    except Exception as e:
        logger.error(f"[analyzer] Unexpected error: {e}")
        return {
            "analysis": {},
            "current_node": "analyzer",
            "error": traceback.format_exc(),
        }
