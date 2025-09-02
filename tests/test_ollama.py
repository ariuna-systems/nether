"""
Simple Ollama test script to debug the API connection
"""

import asyncio
import aiohttp
import json


async def test_ollama():
    """Test Ollama API directly"""
    base_url = "http://localhost:11434"

    # Test 1: Check if Ollama is responding
    print("1. Testing Ollama server availability...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    print(f"   Available models: {models}")
                else:
                    print(f"   Error: {await response.text()}")
    except Exception as e:
        print(f"   Connection failed: {e}")
        return False

    # Test 2: Try a simple chat request
    print("\n2. Testing chat API...")
    try:
        request_data = {"model": "llama3.2", "messages": [{"role": "user", "content": "Say hello"}], "stream": False}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/chat", json=request_data, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    message_content = result.get("message", {}).get("content", "No content")
                    print(f"   Extracted content: {message_content}")
                else:
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   Request failed: {e}")
        import traceback

        print(f"   Full traceback:\n{traceback.format_exc()}")

    return True


if __name__ == "__main__":
    asyncio.run(test_ollama())
