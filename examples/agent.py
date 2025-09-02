"""
AI Agent Example for Nether Framework with Ollama Integration

This example demonstrates how to build AI agents using the Nether Actor Model Framework
with local Ollama LLM integration for real AI responses.

Features:
- Multiple AI agent types (Chat, Code, Analysis) with real Ollama models
- Message-driven communication
- Memory and context management
- Web interface for agent interaction
- Conversation history tracking
- Local Ollama LLM integration

Requirements:
- Ollama installed and running (ollama serve)
- Models downloaded (ollama pull llama3.2, ollama pull codellama, etc.)
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp
from aiohttp import web

import nether
from nether.component import Component
from nether.message import Event, Message, Query
from nether.server import RegisterView, RegisterViewFailure, Server, ViewRegistered

# =============================================================================
# GLOBAL RESPONSE STORE FOR WEB API
# =============================================================================

# Global store for capturing agent responses
_pending_responses: dict[str, dict[str, Any]] = {}
_response_events: dict[str, asyncio.Event] = {}


def _store_response(query_id: str, response_data: dict[str, Any]) -> None:
    """Store a response for the given query ID."""
    _pending_responses[query_id] = response_data
    if query_id in _response_events:
        _response_events[query_id].set()


def _wait_for_response(query_id: str) -> tuple[asyncio.Event, dict[str, Any]]:
    """Create an event to wait for a response."""
    event = asyncio.Event()
    _response_events[query_id] = event
    return event, _pending_responses


def _cleanup_response(query_id: str) -> dict[str, Any] | None:
    """Clean up and return the stored response."""
    response = _pending_responses.pop(query_id, None)
    _response_events.pop(query_id, None)
    return response


# =============================================================================
# MESSAGE DEFINITIONS
# =============================================================================


@dataclass(frozen=True, slots=True, kw_only=True)
class AgentQuery(Query):
    """Query to be processed by an AI agent."""

    agent_type: str  # 'chat', 'code', 'analysis'
    prompt: str
    conversation_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class AgentResponse(Event):
    """Response from an AI agent."""

    query_id: str
    agent_type: str
    response: str
    conversation_id: str | None
    processing_time: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class AgentError(Event):
    """Error event from an AI agent."""

    query_id: str
    agent_type: str
    error_message: str
    conversation_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class GetConversationHistory(Query):
    """Query to get conversation history."""

    conversation_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ConversationHistory(Event):
    """Event containing conversation history."""

    conversation_id: str
    messages: list[dict[str, Any]]


class OllamaService:
    """Service for interacting with local Ollama LLM server."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate_response(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        conversation_history: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> str:
        """Generate a response using Ollama."""
        try:
            # Prepare messages for Ollama
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user prompt
            messages.append({"role": "user", "content": prompt})

            # Prepare request data
            request_data = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048,
                },
            }

            # Make request to Ollama
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.base_url}/api/chat",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response,
            ):
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")

                result = await response.json()
                return result.get("message", {}).get("content", "No response generated")

        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to Ollama: {e}") from e
        except Exception as e:
            raise Exception(f"Ollama generation error: {e}") from e

    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            async with aiohttp.ClientSession() as session, session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    return []
                data = await response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []

    async def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response,
            ):
                return response.status == 200
        except Exception:
            return False


class BaseAgent(Component[AgentQuery]):
    """Base class for AI agents with Ollama integration."""

    def __init__(self, application, agent_type: str, model_name: str, system_prompt: str | None = None):
        super().__init__(application)
        self.agent_type = agent_type
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.conversation_memory: dict[str, list[dict[str, Any]]] = {}
        self.ollama_service = OllamaService()

    def _add_to_memory(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation memory."""
        if conversation_id not in self.conversation_memory:
            self.conversation_memory[conversation_id] = []

        self.conversation_memory[conversation_id].append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Keep only last 20 messages to prevent memory growth
        if len(self.conversation_memory[conversation_id]) > 20:
            self.conversation_memory[conversation_id] = self.conversation_memory[conversation_id][-20:]

    def _get_conversation_context(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get conversation context for the agent."""
        return self.conversation_memory.get(conversation_id, [])

    def _prepare_conversation_history(self, conversation_id: str) -> list[dict[str, Any]]:
        """Prepare conversation history for Ollama (without timestamps)."""
        context = self._get_conversation_context(conversation_id)
        return [{"role": msg["role"], "content": msg["content"]} for msg in context if "role" in msg]

    async def process_query_with_ollama(self, query: AgentQuery) -> str:
        """Process query using Ollama. Override this method in subclasses for custom prompts."""
        conversation_history = self._prepare_conversation_history(query.conversation_id or "")

        return await self.ollama_service.generate_response(
            model=self.model_name,
            prompt=query.prompt,
            system_prompt=self.system_prompt,
            conversation_history=conversation_history,
        )

    async def process_query(self, query: AgentQuery) -> str:
        """Process a query - can be overridden by subclasses for fallback behavior."""
        return await self.process_query_with_ollama(query)

    async def handle(
        self,
        message: AgentQuery,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        """Handle agent query messages."""
        if message.agent_type != self.agent_type:
            return  # Not for this agent type

        start_time = time.time()

        try:
            # Add user query to memory
            if message.conversation_id:
                self._add_to_memory(message.conversation_id, "user", message.prompt)

            # Process the query
            response = await self.process_query(message)

            # Add agent response to memory
            if message.conversation_id:
                self._add_to_memory(message.conversation_id, "assistant", response)

            processing_time = time.time() - start_time

            # Create response
            agent_response = AgentResponse(
                query_id=str(message.created_at),
                agent_type=self.agent_type,
                response=response,
                conversation_id=message.conversation_id,
                processing_time=processing_time,
                metadata={"context_length": len(self._get_conversation_context(message.conversation_id or ""))},
            )

            # Store response in global store for web API
            _store_response(
                str(message.created_at),
                {
                    "status": "success",
                    "response": response,
                    "agent_type": self.agent_type,
                    "processing_time": round(processing_time, 3),
                    "metadata": agent_response.metadata,
                },
            )

            # Send response through mediator
            await handler(agent_response)

        except Exception as error:
            # Create error response
            agent_error = AgentError(
                query_id=str(message.created_at),
                agent_type=self.agent_type,
                error_message=str(error),
                conversation_id=message.conversation_id,
            )

            # Store error in global store for web API
            _store_response(
                str(message.created_at), {"status": "error", "error": str(error), "agent_type": self.agent_type}
            )

            # Send error through mediator
            await handler(agent_error)


class ChatAgent(BaseAgent):
    """A conversational AI agent using Ollama."""

    def __init__(self, application):
        system_prompt = """You are a helpful and friendly AI assistant. You engage in natural conversations,
answer questions, and help users with various tasks. You are knowledgeable, empathetic, and always try
to be helpful while being honest about your limitations."""

        super().__init__(
            application,
            agent_type="chat",
            model_name="llama3.2",  # Default model, can be overridden
            system_prompt=system_prompt,
        )

    async def process_query(self, query: AgentQuery) -> str:
        """Process a chat query with Ollama."""
        try:
            return await self.process_query_with_ollama(query)
        except Exception as e:
            # Fallback to simple responses if Ollama is not available
            prompt_lower = query.prompt.lower()
            if "hello" in prompt_lower or "hi" in prompt_lower:
                return "Hello! I'm a chat agent. (Note: Ollama not available, using fallback response)"
            return f"I received your message: '{query.prompt}'. (Note: Ollama not available - {e!s})"


class CodeAgent(BaseAgent):
    """An AI agent specialized in code-related queries using Ollama."""

    def __init__(self, application):
        system_prompt = """You are an expert programming assistant. You help with code review, debugging,
writing code examples, explaining programming concepts, and answering technical questions. You provide
clear, well-commented code examples and explain complex concepts in simple terms. You support multiple
programming languages including Python, JavaScript, TypeScript, Java, C++, and more."""

        super().__init__(
            application,
            agent_type="code",
            model_name="codellama",  # Specialized code model
            system_prompt=system_prompt,
        )

    async def process_query(self, query: AgentQuery) -> str:
        """Process a code-related query with Ollama."""
        try:
            return await self.process_query_with_ollama(query)
        except Exception as e:
            # Fallback responses for code queries
            prompt_lower = query.prompt.lower()
            if "python" in prompt_lower:
                return """Here's a simple Python example:

```python
def greet(name):
    return f"Hello, {name}!"

# Usage
message = greet("World")
print(message)
```

(Note: Ollama not available, using fallback response)"""
            return f"Code query received: '{query.prompt}'. (Note: Ollama not available - {e!s})"


class AnalysisAgent(BaseAgent):
    """An AI agent specialized in data analysis queries using Ollama."""

    def __init__(self, application):
        system_prompt = """You are a data analysis expert. You help with statistical analysis, data
interpretation, trend analysis, performance metrics, and data visualization recommendations. You provide
insights, identify patterns, suggest analytical approaches, and explain complex data concepts clearly.
You can work with various data types and analytical frameworks."""

        super().__init__(
            application,
            agent_type="analysis",
            model_name="llama3.2",  # General model for analysis
            system_prompt=system_prompt,
        )

    async def process_query(self, query: AgentQuery) -> str:
        """Process an analysis query with Ollama."""
        try:
            return await self.process_query_with_ollama(query)
        except Exception as e:
            # Fallback responses for analysis queries
            prompt_lower = query.prompt.lower()
            if "trend" in prompt_lower:
                return """📈 **Trend Analysis**

Based on demo data:
- Upward trend: 65%
- Stable: 25%
- Downward trend: 10%

(Note: Ollama not available, using fallback response)"""
            return f"Analysis query received: '{query.prompt}'. (Note: Ollama not available - {e!s})"


class ConversationManager(Component[GetConversationHistory]):
    """Manages conversation history across agents."""

    def __init__(self, application):
        super().__init__(application)
        self.agents = {}  # Will be populated by system

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the conversation manager."""
        self.agents[agent.agent_type] = agent

    async def handle(
        self,
        message: GetConversationHistory,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        """Handle conversation history requests."""
        all_messages = []

        # Collect messages from all agents
        for agent in self.agents.values():
            if message.conversation_id in agent.conversation_memory:
                all_messages.extend(agent.conversation_memory[message.conversation_id])

        # Sort by timestamp
        all_messages.sort(key=lambda x: x["timestamp"])

        await handler(ConversationHistory(conversation_id=message.conversation_id, messages=all_messages))


class AgentWebInterface(web.View):
    """Web interface for interacting with AI agents."""

    async def get(self) -> web.Response:
        """Serve the agent interface."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Nether AI Agents</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .agent-selector { margin: 20px 0; }
        .chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .agent-message { background-color: #f5f5f5; }
        .error-message { background-color: #ffebee; color: #c62828; }
        .input-container { display: flex; gap: 10px; margin: 10px 0; }
        .query-input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .send-button { padding: 10px 20px; background-color: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .send-button:hover { background-color: #1976d2; }
        .agent-type { font-weight: bold; color: #1976d2; }
        .metadata { font-size: 0.8em; color: #666; }
    </style>
</head>
<body>
    <h1>Nether AI Agents</h1>
    <div class="agent-selector">
        <label for="agentType">Select Agent Type:</label>
        <select id="agentType">
            <option value="chat">Chat Agent</option>
            <option value="code">Code Agent</option>
            <option value="analysis">Analysis Agent</option>
        </select>
    </div>

    <div id="chatContainer" class="chat-container"></div>

    <div class="input-container">
        <input type="text" id="queryInput" class="query-input" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
        <button onclick="sendQuery()" class="send-button">Send</button>
    </div>

    <div style="margin-top: 20px;">
        <button onclick="clearChat()" style="background-color: #ff9800;">Clear Chat</button>
        <button onclick="getHistory()" style="background-color: #4caf50;">Get History</button>
    </div>

    <script>
        const conversationId = 'web-session-' + Date.now();

        function addMessage(content, type, metadata = {}) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;

            let metadataHtml = '';
            if (Object.keys(metadata).length > 0) {
                metadataHtml = '<div class="metadata">' + JSON.stringify(metadata) + '</div>';
            }

            messageDiv.innerHTML = `<div>${content}</div>${metadataHtml}`;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        async function sendQuery() {
            const queryInput = document.getElementById('queryInput');
            const agentType = document.getElementById('agentType').value;
            const query = queryInput.value.trim();

            if (!query) return;

            addMessage(query, 'user');
            queryInput.value = '';

            try {
                const response = await fetch('/agent/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        agent_type: agentType,
                        prompt: query,
                        conversation_id: conversationId
                    })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    const metadata = {
                        'Agent': result.agent_type,
                        'Processing Time': result.processing_time + 's'
                    };
                    addMessage(result.response, 'agent', metadata);
                } else {
                    addMessage('Error: ' + result.error, 'error');
                }
            } catch (error) {
                addMessage('Connection error: ' + error.message, 'error');
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendQuery();
            }
        }

        function clearChat() {
            document.getElementById('chatContainer').innerHTML = '';
        }

        async function getHistory() {
            try {
                const response = await fetch(`/agent/history/${conversationId}`);
                const result = await response.json();

                if (result.status === 'success') {
                    clearChat();
                    result.messages.forEach(msg => {
                        const type = msg.role === 'user' ? 'user' : 'agent';
                        addMessage(msg.content, type, { timestamp: msg.timestamp });
                    });
                } else {
                    addMessage('Error getting history: ' + result.error, 'error');
                }
            } catch (error) {
                addMessage('Connection error: ' + error.message, 'error');
            }
        }
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type="text/html")


class AgentQueryAPI(web.View):
    """API endpoint for agent queries."""

    async def post(self) -> web.Response:
        """Handle agent query requests."""
        try:
            data = await self.request.json()
            system = self.request.app["system"]

            # Create agent query
            query = AgentQuery(
                agent_type=data["agent_type"], prompt=data["prompt"], conversation_id=data.get("conversation_id")
            )

            query_id = str(query.created_at)

            # Set up response waiting
            event, _ = _wait_for_response(query_id)

            try:
                # Send query through mediator
                async with system.mediator.context() as ctx:
                    await ctx.process(query)

                # Wait for response (with timeout)
                try:
                    await asyncio.wait_for(event.wait(), timeout=15.0)
                    response_data = _cleanup_response(query_id)
                    if response_data:
                        return web.json_response(response_data)
                    else:
                        return web.json_response({"status": "error", "error": "No response received"})
                except TimeoutError:
                    _cleanup_response(query_id)
                    return web.json_response({"status": "error", "error": "Request timeout"})

            except Exception as inner_error:
                _cleanup_response(query_id)
                return web.json_response({"status": "error", "error": str(inner_error)}, status=500)

        except Exception as error:
            return web.json_response({"status": "error", "error": str(error)}, status=500)


class ConversationHistoryAPI(web.View):
    """API endpoint for conversation history."""

    async def get(self) -> web.Response:
        """Get conversation history."""
        try:
            conversation_id = self.request.match_info["conversation_id"]
            system = self.request.app["system"]

            # Get conversation manager
            conversation_manager = None
            for component in system.mediator.components:
                if isinstance(component, ConversationManager):
                    conversation_manager = component
                    break

            if not conversation_manager:
                return web.json_response({"status": "error", "error": "Conversation manager not found"}, status=500)

            # Get history from all agents
            all_messages = []
            for agent in conversation_manager.agents.values():
                if conversation_id in agent.conversation_memory:
                    all_messages.extend(agent.conversation_memory[conversation_id])

            # Sort by timestamp
            all_messages.sort(key=lambda x: x["timestamp"])

            return web.json_response(
                {"status": "success", "conversation_id": conversation_id, "messages": all_messages}
            )

        except Exception as error:
            return web.json_response({"status": "error", "error": str(error)}, status=500)


# =============================================================================
# VIEW REGISTRATION HANDLER
# =============================================================================


class ViewRegistrationHandler(Component[ViewRegistered | RegisterViewFailure]):
    """Component to handle view registration events."""

    async def handle(self, message: Message, *, handler: Callable[[Message], Awaitable[None]], **_: Any) -> None:
        """Handle view registration success/failure events."""
        match message:
            case ViewRegistered():
                print(f"✓ View successfully registered")
            case RegisterViewFailure():
                print(f"✗ View registration failed: {message.error}")


# =============================================================================
# MAIN SYSTEM CLASS
# =============================================================================


class AIAgentSystem(nether.Nether):
    """AI Agent system using Nether framework."""

    def __init__(self, configuration):
        super().__init__(configuration=configuration)

    async def main(self) -> None:
        print("AI Agent System Started")


async def main():
    """Main function to set up and run the AI agent system."""

    @dataclass(frozen=True, slots=True, kw_only=True)
    class ServerConfig:
        port: int = 8083
        host: str = "localhost"

    config = ServerConfig()
    system = AIAgentSystem(configuration=config)

    # Create agents
    chat_agent = ChatAgent(system)
    code_agent = CodeAgent(system)
    analysis_agent = AnalysisAgent(system)

    # Create conversation manager
    conversation_manager = ConversationManager(system)
    conversation_manager.register_agent(chat_agent)
    conversation_manager.register_agent(code_agent)
    conversation_manager.register_agent(analysis_agent)

    # Create view registration handler
    view_handler = ViewRegistrationHandler(system)

    # Attach components
    system.attach(chat_agent)
    system.attach(code_agent)
    system.attach(analysis_agent)
    system.attach(conversation_manager)
    system.attach(view_handler)

    # Set up web server
    server = Server(system, configuration=config)
    system.attach(server)

    # Store system reference for web handlers
    server._http_server["system"] = system

    # Register web routes - do this BEFORE starting the system
    register_view_1 = RegisterView(route="/", view=AgentWebInterface)
    register_view_2 = RegisterView(route="/agent/query", view=AgentQueryAPI)
    register_view_3 = RegisterView(route="/agent/history/{conversation_id}", view=ConversationHistoryAPI)

    # Process route registrations
    async with system.mediator.context() as ctx:
        await ctx.process(register_view_1)
        await ctx.process(register_view_2)
        await ctx.process(register_view_3)
    print(f"Web interface: http://localhost:{config.port}/")
    print("Available agents: chat, code, analysis")

    await system.start()


if __name__ == "__main__":
    try:
        nether.execute(main())
    except KeyboardInterrupt:
        print("\nAI Agent System shutting down gracefully")
