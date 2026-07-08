"""
Chat router — follow-up Q&A grounded in the session's research report.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage

from database import get_db, ResearchSession, ChatMessage
from models import ChatRequest, ChatResponse, ChatMessageOut
from services.llm import get_llm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["chat"])


@router.get("/{session_id}/chat", response_model=list[ChatMessageOut])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all chat messages for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    session_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a follow-up question grounded in the session's research report.
    Uses the full report as context so the LLM answers only from researched data.
    """
    # Fetch session
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Research must be completed before chatting",
        )

    if not session.report_markdown:
        raise HTTPException(status_code=400, detail="No report available for this session")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)
    await db.commit()

    # Fetch recent chat history for context (last 10 messages)
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))

    # Retrieve raw facts from Chroma RAG store
    from services.rag import retrieve_context
    raw_chunks = await retrieve_context(session_id, payload.message)
    raw_context_str = "\n\n".join(raw_chunks) if raw_chunks else "No additional raw context found."

    # Build LangChain messages
    llm = get_llm()
    system = SystemMessage(content=f"""You are a sales intelligence assistant helping a sales professional prepare for a meeting with {session.company_name}.

You have access to the final research report, AND directly retrieved raw text chunks from the original website scrapes. Answer questions ONLY based on this provided context. If the information is not in the context, say so clearly.

=== FINAL RESEARCH REPORT ===
{session.report_markdown}
=== END REPORT ===

=== RAW SCRAPED DATA (RAG) ===
{raw_context_str}
=== END RAW DATA ===

Guidelines:
- Be concise and direct
- Reference specific facts from the report or raw data
- If asked about something not in the context, be honest about gaps
- Frame answers in a sales/business development context
- Research objective was: {session.objective}""")

    messages = [system]
    for h in history[:-1]:  # exclude the latest user message we just saved
        if h.role == "user":
            messages.append(HumanMessage(content=h.content))
        else:
            from langchain_core.messages import AIMessage
            messages.append(AIMessage(content=h.content))

    messages.append(HumanMessage(content=payload.message))

    try:
        response = await llm.ainvoke(messages)
        reply_content = response.content.strip()
    except Exception as e:
        logger.error(f"[chat] LLM error: {e}")
        reply_content = f"I encountered an error processing your question. Please try again. ({e})"

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply_content,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    logger.info(f"[chat] Replied to session {session_id}")
    return assistant_msg
