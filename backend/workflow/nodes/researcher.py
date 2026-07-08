"""
Researcher Node — executes web searches using:
  1. Google Search via DDGS  (no API key, uses Google backend) ← default
  2. Tavily                  (if TAVILY_API_KEY is set — best quality)
  3. DuckDuckGo fallback     (older duckduckgo_search library)

Runs all queries from the planner concurrently via asyncio.
"""
import asyncio
import logging
from typing import Any
from workflow.state import ResearchState
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Google via DDGS ──────────────────────────────────────────────────

async def _summarize_text(text: str, url: str) -> str:
    """Use the LLM to summarize long scraped text to extract dense facts."""
    if len(text) < 800:
        return text
        
    from services.llm import get_llm
    from langchain_core.messages import HumanMessage
    
    llm = get_llm()
    prompt = (
        f"Extract and summarize the core factual information, business details, products, and recent news "
        f"from the following scraped website text (URL: {url}). "
        f"Keep it densely packed with facts and ignore fluff. Text:\n\n{text[:15000]}"
    )
    try:
        # LLM calls are fast but might rate limit; fallback is truncation
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return str(getattr(response, "content", response))
    except Exception as e:
        logger.warning(f"[scraper] Summary failed for {url}, falling back to truncation: {e}")
        return text[:4000]

async def _scrape_url(url: str, session: Any, session_id: str) -> str:
    """Scrape the raw text from a URL using BeautifulSoup."""
    try:
        async with session.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"}) as response:
            if response.status == 200:
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                text = soup.get_text(separator=" ", strip=True)
                
                # [RAG INTEGRATION] Insert the raw text into Vector DB *before* summarizing
                from services.rag import add_texts_to_rag
                await add_texts_to_rag(session_id, text, url)
                
                return await _summarize_text(text, url)
    except Exception as e:
        logger.warning(f"[scraper] Failed to scrape {url}: {e}")
    return ""

async def _search_google_ddgs(query: str, max_results: int, session_id: str) -> list[dict]:
    """
    Search using DDGS and scrape the full text of the results.
    """
    from ddgs import DDGS
    import aiohttp
    loop = asyncio.get_event_loop()

    def _do():
        results = []
        try:
            with DDGS() as d:
                for r in d.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", "") or r.get("url", ""),
                        "content": r.get("body", "") or r.get("description", ""),
                    })
        except Exception as e:
            logger.warning(f"[google/ddgs] Error for '{query}': {e}")
        return results

    results = await loop.run_in_executor(None, _do)
    
    # Scrape the URLs sequentially to prevent LLM rate limiting
    async def fetch_all():
        async with aiohttp.ClientSession() as session:
            for r in results:
                if r.get("url"):
                    scraped_text = await _scrape_url(r["url"], session, session_id)
                    if isinstance(scraped_text, str) and scraped_text:
                        r["content"] = scraped_text
                    
    await fetch_all()
    return results


# ── Tavily Search ─────────────────────────────────────────────────────

async def _search_tavily(query: str, max_results: int, session_id: str) -> list[dict]:
    """Search using Tavily API — requires TAVILY_API_KEY."""
    from tavily import TavilyClient
    client = TavilyClient(api_key=settings.tavily_api_key)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: client.search(query, max_results=max_results, include_raw_content=True)
    )
    
    parsed = []
    from services.rag import add_texts_to_rag
    
    for r in result.get("results", []):
        url = r.get("url", "")
        raw_content = r.get("raw_content", "")
        content = r.get("content", "")
        
        # [RAG INTEGRATION] Insert the raw text into Vector DB *before* summarizing
        if raw_content:
            await add_texts_to_rag(session_id, raw_content, url)
            final_content = await _summarize_text(raw_content, url)
        else:
            final_content = content
            
        parsed.append({
            "title": r.get("title", ""),
            "url": url,
            "content": final_content,
        })
        
    return parsed


# ── Dispatcher ────────────────────────────────────────────────────────

async def _search_single(query: str, session_id: str) -> dict:
    """
    Run one query with the configured engine.
    Falls back to Google/DDGS if primary fails.
    """
    max_results = settings.max_search_results
    engine = settings.search_engine.lower()

    # Build ordered list of engines to try
    try_engines: list[tuple[str, object]] = []

    if engine == "tavily" and settings.tavily_api_key:
        try_engines.append(("tavily", _search_tavily))
    # Default / fallback: google via ddgs
    try_engines.append(("google", _search_google_ddgs))

    for name, fn in try_engines:
        try:
            results = await fn(query, max_results, session_id)
            if results:
                logger.info(f"[researcher] '{query}' → {len(results)} results [{name}]")
                return {"query": query, "results": results, "engine": name, "error": None}
            logger.warning(f"[researcher] {name} returned 0 results for '{query}'")
        except Exception as e:
            logger.warning(f"[researcher] {name} failed for '{query}': {e}")

    return {"query": query, "results": [], "engine": "none", "error": "All search engines returned no results"}


# ── Main Node ─────────────────────────────────────────────────────────

async def research_node(state: ResearchState) -> dict:
    """
    Executes all search queries from the planner concurrently.
    Returns: { raw_research, current_node }
    """
    queries = state.get("plan", [])
    session_id = state.get("session_id", "unknown_session")
    
    if not queries:
        logger.warning("[researcher] No queries to run")
        return {"raw_research": [], "current_node": "researcher"}

    logger.info(f"[researcher] Running {len(queries)} queries (engine={settings.search_engine})")

    # Execute queries sequentially to avoid LLM rate limits
    results = []
    for q in queries:
        result = await _search_single(q, session_id)
        results.append(result)
        await asyncio.sleep(1.0)  # polite delay between queries
    valid = [r for r in results if r["results"]]
    logger.info(f"[researcher] Got results for {len(valid)}/{len(queries)} queries")

    return {
        "raw_research": list(results),
        "current_node": "researcher",
        "retry_count": state.get("retry_count", 0),
    }
