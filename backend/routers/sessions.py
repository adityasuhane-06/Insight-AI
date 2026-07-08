"""
Sessions router — CRUD for research sessions.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db, ResearchSession
from models import SessionCreate, SessionOut, SessionListItem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new research session."""
    session = ResearchSession(
        company_name=payload.company_name,
        website=payload.website,
        objective=payload.objective,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(f"Created session {session.id} for {session.company_name}")
    return session


@router.get("", response_model=list[SessionListItem])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all research sessions, newest first."""
    result = await db.execute(
        select(ResearchSession).order_by(desc(ResearchSession.created_at))
    )
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single session by ID including report."""
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a session and all its chat messages."""
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    logger.info(f"Deleted session {session_id}")
