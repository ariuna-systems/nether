#!/usr/bin/env python3
"""
Test script to verify the timeout fix for Ollama integration
"""

import aiohttp
import asyncio
import json
import time


async def test_agent_timeout():
    """Test the agent with a complex prompt that should take more than 30 seconds"""
    url = "http://localhost:8083/agent/chat"

    # Complex prompt that should take time to process
    prompt = """Please provide a comprehensive analysis of the UAV (Unmanned Aerial Vehicle) ontology including:
    1. Core components and their relationships
    2. Flight control systems architecture
    3. Sensor integration patterns
    4. Mission planning frameworks
    5. Safety and compliance considerations
    6. Communication protocols
    7. Data processing pipelines
    8. Autonomous decision-making algorithms

    Please provide detailed explanations with technical depth and specific examples."""

    payload = {"message": prompt}

    print("Sending complex prompt to chat agent...")
    print(f"Prompt length: {len(prompt)} characters")
    start_time = time.time()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=150),  # Give extra time for testing
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()
                    duration = end_time - start_time

                    print(f"\n SUCCESS! Response received in {duration:.2f} seconds")
                    print(f"Response length: {len(result.get('response', ''))} characters")

                    # Check if it's a fallback response
                    response_text = result.get("response", "")
                    if "Ollama not available" in response_text or "fallback response" in response_text:
                        print("\n Still getting fallback response!")
                        print(f"Response: {response_text[:200]}...")
                    else:
                        print("\n Real AI response received!")
                        print(f"First 300 characters: {response_text[:300]}...")
                else:
                    print(f" HTTP Error: {response.status}")
                    print(await response.text())

    except asyncio.TimeoutError:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n TIMEOUT after {duration:.2f} seconds")
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n ERROR after {duration:.2f} seconds: {e}")


if __name__ == "__main__":
    asyncio.run(test_agent_timeout())
