"""
Workflow router — triggers LangGraph workflow execution with SSE streaming.
Streams real-time progress to the frontend as the graph executes node by node.
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, ResearchSession
from workflow.graph import get_graph
from workflow.state import ResearchState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["workflow"])

# Human-readable node descriptions for UI display
NODE_DESCRIPTIONS = {
    "planner": "Planning research strategy...",
    "researcher": "Searching the web for information...",
    "analyzer": "Analyzing collected data...",
    "quality_check": "Evaluating report quality...",
    "increment_retry": "Preparing additional research...",
    "report_gen": "Generating final report...",
    "error_handler": "Handling workflow error...",
}


def _make_sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _run_workflow_and_stream(session_id: str, db: AsyncSession):
    """
    Core generator function that runs the LangGraph workflow
    and yields SSE events as nodes complete.
    """
    # Fetch session
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        yield _make_sse_event({"type": "error", "message": "Session not found"})
        return

    # Check if already running
    if session.status == "running":
        yield _make_sse_event({"type": "error", "message": "Workflow already running"})
        return

    # Mark as running
    session.status = "running"
    session.current_node = "starting"
    session.error_message = ""
    await db.commit()

    yield _make_sse_event({
        "type": "start",
        "message": f"Starting research for {session.company_name}",
    })

    # Build initial state
    initial_state: ResearchState = {
        "session_id": session_id,
        "company_name": session.company_name,
        "website": session.website,
        "objective": session.objective,
        "plan": [],
        "raw_research": [],
        "analysis": {},
        "quality_score": 0.0,
        "quality_feedback": "",
        "report_markdown": "",
        "report_json": "",
        "retry_count": 0,
        "error": None,
        "current_node": "",
        "status": "running",
    }

    graph = get_graph()
    final_state = initial_state.copy()

    try:
        async for chunk in graph.astream(initial_state, {"recursion_limit": 25}):
            for node_name, node_output in chunk.items():
                if not isinstance(node_output, dict):
                    continue

                # Update final_state with latest outputs
                final_state.update(node_output)

                # Update DB incrementally
                current_node = node_name.replace("_", " ").title()
                session.current_node = node_name
                if node_output.get("error"):
                    session.error_message = node_output["error"]
                await db.commit()

                description = NODE_DESCRIPTIONS.get(node_name, f"Running {node_name}...")
                logger.info(f"[workflow] Node complete: {node_name}")

                yield _make_sse_event({
                    "type": "progress",
                    "node": node_name,
                    "description": description,
                    "retry_count": final_state.get("retry_count", 0),
                    "quality_score": final_state.get("quality_score", 0.0),
                })

                await asyncio.sleep(0.05)  # small yield for proper streaming

        # Workflow complete — save final state
        session.status = final_state.get("status", "completed")
        session.report_markdown = final_state.get("report_markdown", "")
        session.report_json = final_state.get("report_json", "")
        session.quality_score = final_state.get("quality_score", 0.0)
        session.retry_count = final_state.get("retry_count", 0)
        session.current_node = final_state.get("current_node", "")
        if final_state.get("error"):
            session.error_message = final_state["error"]
        await db.commit()

        yield _make_sse_event({
            "type": "complete",
            "status": session.status,
            "quality_score": session.quality_score,
            "message": "Research complete!" if session.status == "completed" else "Research finished with errors.",
        })

    except Exception as e:
        logger.exception(f"[workflow] Fatal error for session {session_id}: {e}")
        session.status = "failed"
        session.error_message = str(e)
        await db.commit()

        yield _make_sse_event({
            "type": "error",
            "message": f"Workflow failed: {str(e)}",
        })


@router.get("/{session_id}/stream")
async def stream_workflow(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    SSE endpoint to trigger and stream the LangGraph research workflow.
    Frontend connects here to receive real-time progress events.
    """
    return StreamingResponse(
        _run_workflow_and_stream(session_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
