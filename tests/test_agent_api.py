"""
Test the AI Agent API to debug the Ollama integration
"""

import asyncio
import aiohttp
import json


async def test_agent_api():
    """Test the agent API directly"""
    base_url = "http://localhost:8083"

    print("Testing AI Agent API...")
    try:
        request_data = {
            "agent_type": "chat",
            "prompt": "Provide a simple ontology for military UAVs",
            "conversation_id": "test-debug",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/agent/query", json=request_data, timeout=aiohttp.ClientTimeout(total=45)
            ) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"Error: {error_text}")
    except Exception as e:
        print(f"Request failed: {e}")
        import traceback

        print(f"Full traceback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_agent_api())
