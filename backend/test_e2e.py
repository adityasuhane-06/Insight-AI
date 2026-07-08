import asyncio
import logging
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# CRITICAL: Disable TensorFlow warnings since we are using Torch
# This must happen before ANY other imports (especially routers/database)
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, init_db, ResearchSession
from routers.workflow import _run_workflow_and_stream
from routers.chat import send_chat_message
from models import ChatRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_e2e_test():
    print("========================================")
    print("[TEST] STARTING E2E BACKEND TEST (WORKFLOW + RAG CHAT)")
    print("========================================")

    # 1. Initialize the database
    await init_db()

    session_id = str(uuid.uuid4())
    print(f"\n[1] Creating Research Session in DB (ID: {session_id})")

    # Create dummy session
    async with AsyncSessionLocal() as db:
        new_session = ResearchSession(
            id=session_id,
            company_name="Snowflake",
            website="https://www.snowflake.com",
            objective="Find out their latest enterprise AI products, recent financial performance, and key pain points that a cloud security vendor could pitch to their IT executives during a sales meeting.",
            status="pending"
        )
        db.add(new_session)
        await db.commit()

    # 2. Run Workflow
    print("\n[2] Executing LangGraph Workflow...")
    async with AsyncSessionLocal() as db:
        # We iterate over the SSE event generator just like the frontend would
        async for sse_event in _run_workflow_and_stream(session_id, db):
            # Parse the SSE data line to print nice progress
            if sse_event.startswith("data: "):
                import json
                try:
                    data = json.loads(sse_event[6:])
                    event_type = data.get("type")
                    if event_type == "progress":
                        print(f"   [⏳] Progress: {data.get('description')} (Node: {data.get('node')})")
                    elif event_type == "start":
                        print(f"   [>] Start: {data.get('message')}")
                    elif event_type == "complete":
                        print(f"   [OK] Complete: {data.get('message')} (Quality: {data.get('quality_score')})")
                    elif event_type == "error":
                        print(f"   [X] Error: {data.get('message')}")
                except Exception:
                    pass

    # Fetch final report to verify
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        completed_session = res.scalar_one()
        
        print("\n[3] Final Report Generation Check")
        if completed_session.report_markdown:
            print(f"   [OK] Generated a {len(completed_session.report_markdown)} character markdown report!")
        else:
            print("   [X] Report generation failed!")
            return

    # 3. Test RAG Chat
    print("\n[4] Testing RAG Chat Endpoint...")
    chat_query = "Based on the scraped raw data, what specific funding rounds have they had?"
    print(f"   [?] User Query: {chat_query}")
    
    async with AsyncSessionLocal() as db:
        payload = ChatRequest(message=chat_query)
        try:
            # We call the chat router endpoint logic directly
            assistant_msg = await send_chat_message(session_id, payload, db)
            print(f"\n   [Assistant Reply]:\n      {assistant_msg.content}")
        except Exception as e:
            print(f"   [X] Chat failed: {e}")

    print("\n========================================")
    print("[OK] E2E TEST COMPLETE")
    print("========================================")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(run_e2e_test())
