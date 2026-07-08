import traceback
"""
Planner Node — generates a targeted research plan (search queries)
given the company name, website, and research objective.
"""
import json
import logging
from langchain_core.messages import HumanMessage
from workflow.state import ResearchState
from services.llm import get_llm, extract_text

logger = logging.getLogger(__name__)


async def planner_node(state: ResearchState) -> dict:
    """
    Generates 6-8 search queries to comprehensively research the target company.
    Returns: { plan, current_node, status }
    """
    logger.info(f"[planner] Starting for company: {state['company_name']}")

    llm = get_llm()

    prompt = f"""You are an expert sales research planner. Your job is to create a focused research plan for a sales professional preparing for a business meeting.

Company: {state['company_name']}
Website: {state['website']}
Research Objective: {state['objective']}

Generate exactly 7 targeted web search queries that will help uncover:
1. Company overview, founding story, and business model
2. Products and services they sell (with pricing if available)
3. Target customers and industries they serve
4. Recent news, funding, acquisitions, or major business signals
5. Key competitors and market positioning
6. Leadership team and company culture
7. Potential risks, challenges, or public controversies

Rules:
- Each query must be specific and actionable
- Include the company name in most queries
- Include the website domain where helpful
- Return ONLY a valid JSON array of strings — no markdown, no explanation

Example format:
["query one", "query two", "query three"]"""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = extract_text(response)

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        queries = json.loads(content)
        if not isinstance(queries, list):
            raise ValueError("LLM did not return a list")

        logger.info(f"[planner] Generated {len(queries)} search queries")

        return {
            "plan": queries,
            "current_node": "planner",
            "status": "running",
            "error": None,
        }

    except Exception as e:
        logger.error(f"[planner] Failed: {e}")
        # Fallback: generate basic queries manually
        fallback = [
            f"{state['company_name']} company overview",
            f"{state['company_name']} products services pricing",
            f"{state['company_name']} target customers market",
            f"{state['company_name']} recent news 2024 2025",
            f"{state['company_name']} competitors alternatives",
            f"{state['company_name']} leadership team CEO",
            f"{state['website']} about business model",
        ]
        logger.info("[planner] Using fallback queries")
        return {
            "plan": fallback,
            "current_node": "planner",
            "status": "running",
            "error": None,
        }
