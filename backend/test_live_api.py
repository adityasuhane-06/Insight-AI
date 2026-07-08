import asyncio
import json
import httpx

API_BASE_URL = "https://insight-ai-wwot.onrender.com/api"

async def test_live_api():
    print("========================================")
    print(f"[TEST] STARTING LIVE API TEST ON: {API_BASE_URL}")
    print("========================================")

    # 1. Create a session
    company_name = "Snowflake"
    website = "https://www.snowflake.com"
    objective = "Find out their latest enterprise AI products, recent financial performance, and key pain points that a cloud security vendor could pitch to their IT executives during a sales meeting."

    print(f"\n[1] Creating Research Session for {company_name}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/sessions",
            json={
                "company_name": company_name,
                "website": website,
                "objective": objective
            }
        )
        response.raise_for_status()
        session_data = response.json()
        session_id = session_data["id"]
        print(f"   [OK] Session Created! ID: {session_id}")

    # 2. Stream the workflow
    print("\n[2] Executing LangGraph Workflow via SSE...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("GET", f"{API_BASE_URL}/sessions/{session_id}/stream") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
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

    # 3. Check final report
    print("\n[3] Fetching Final Report...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_BASE_URL}/sessions/{session_id}")
        session_data = response.json()
        report = session_data.get("report_markdown")
        if report:
            print(f"   [OK] Fetched report of length {len(report)} characters!")
        else:
            print("   [X] Report is empty!")

    # 4. Test Chat
    print("\n[4] Testing RAG Chat Endpoint...")
    chat_query = "What are the specific pain points mentioned that I can use in my sales pitch?"
    print(f"   [?] User Query: {chat_query}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/sessions/{session_id}/chat",
            json={"message": chat_query}
        )
        chat_data = response.json()
        print(f"\n   [Assistant Reply]:\n{chat_data.get('content')}")

    print("\n========================================")
    print("[OK] LIVE API TEST COMPLETE")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(test_live_api())
