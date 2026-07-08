"""
Error Handler Node — captures workflow failures gracefully.
Sets status to 'failed' with a descriptive error message,
and preserves any partial data collected before the failure.
"""
import logging
from datetime import datetime
from workflow.state import ResearchState

logger = logging.getLogger(__name__)


async def error_handler_node(state: ResearchState) -> dict:
    """
    Handles workflow errors gracefully.
    - Logs the failure
    - Preserves partial results
    - Sets status to 'failed'
    - Builds a minimal report from whatever data is available
    """
    error = state.get("error", "Unknown error occurred")
    company = state.get("company_name", "Unknown company")
    logger.error(f"[error_handler] Workflow failed for '{company}': {error}")

    # Try to build a partial report from whatever we have
    analysis = state.get("analysis", {})
    has_partial_data = bool(analysis)

    partial_note = ""
    if has_partial_data:
        partial_note = "\n> ⚠️ **Partial Report** — The workflow encountered an error but partial data was collected.\n"
    else:
        partial_note = "\n> ❌ **Report Unavailable** — The research workflow failed before collecting data.\n"

    error_report = f"""# Research Briefing: {company}

{partial_note}

**Error Details:** {error}

**Recommendation:** 
- Check your API keys in the `.env` file
- Verify the company website is accessible
- Try running the research again
- Check backend logs for detailed error information

---

## Partial Data (if available)

{analysis.get('company_overview', 'No overview collected') if analysis else 'No data collected.'}

---
*Generated at {datetime.utcnow().strftime("%B %d, %Y %H:%M")} UTC*
"""

    return {
        "report_markdown": error_report,
        "status": "failed",
        "current_node": "error_handler",
        "error": error,
    }
