"""
Nether Settings Module - Independent settings component for Nether applications.

This module provides a complete settings management component with:
- Modern ES6 web component frontend (built with Vite)
- RESTful API endpoints for settings CRUD
- Secure static asset serving
- Event-driven architecture integration
"""

__version__ = "1.0.0"

__all__ = [
    "SettingsComponent",
    "SettingsAPIView",
    "SettingsModuleView",
    "GetSettings",
    "UpdateSettings",
    "SettingsUpdated",
]

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiohttp import web
from nether.modules import Module
from nether.message import Command, Event, Message
from nether.server import RegisterView


@dataclass(frozen=True, kw_only=True, slots=True)
class GetSettings(Command):
    """Command to get application settings."""

    ...


@dataclass(frozen=True, kw_only=True, slots=True)
class UpdateSettings(Command):
    """Command to update application settings."""

    settings: dict[str, Any]


@dataclass(frozen=True, kw_only=True, slots=True)
class SettingsUpdated(Event):
    """Event when settings are updated."""

    settings: dict[str, Any]


class SettingsAPIView(web.View):
    """API endpoints for settings operations."""

    async def get(self) -> web.Response:
        """Get application settings."""
        # Mock settings data - in production, this would come from a database
        settings = {
            "general": {
                "app_name": "Nether Application",
                "app_description": "Modern component-based application",
                "timezone": "UTC",
                "language": "en-US",
                "theme": "light",
            },
            "security": {
                "session_timeout": 30,
                "two_factor_auth": False,
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_numbers": True,
                },
            },
            "notifications": {
                "email_notifications": True,
                "push_notifications": False,
                "digest_frequency": "daily",
            },
        }

        return web.json_response(settings)

    async def post(self) -> web.Response:
        """Update application settings."""
        try:
            data = await self.request.json()
            updated_settings = data.get("settings", {})

            # Mock settings validation and update
            # In production: validate settings, update database, etc.

            return web.json_response(
                {
                    "success": True,
                    "message": "Settings updated successfully",
                    "updated_at": time.time(),
                    "settings": updated_settings,
                }
            )
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)


class SettingsModuleView(web.View):
    """Serve the settings component ES6 module from bundled frontend."""

    def __init__(self, request):
        super().__init__(request)
        self.static_dir = Path(__file__).parent / "static"

    async def get(self) -> web.Response:
        """Return settings component as ES6 module from bundled assets."""
        try:
            # Try to serve the bundled JavaScript module
            module_path = self.static_dir / "settings-component.js"

            if module_path.exists():
                # Serve the pre-built module
                with open(module_path, "r", encoding="utf-8") as f:
                    module_code = f.read()
            else:
                # Fallback: serve a minimal inline module
                module_code = self._get_fallback_module()

            return web.Response(
                text=module_code,
                content_type="application/javascript",
                headers={
                    "Content-Security-Policy": "default-src 'self'",
                    "Cache-Control": "public, max-age=3600",
                },
            )
        except Exception as e:
            # Return minimal error module
            error_module = f"""
// Settings Module Error
console.error('Failed to load settings module: {str(e)}');
export default class SettingsComponent extends HTMLElement {{
    connectedCallback() {{
        this.innerHTML = '<div>Settings module failed to load</div>';
    }}
}}
if (!customElements.get('settings-component')) {{
    customElements.define('settings-component', SettingsComponent);
}}
"""
            return web.Response(
                text=error_module, content_type="application/javascript", status=500
            )

    def _get_fallback_module(self) -> str:
        """Minimal fallback module when bundled assets aren't available."""
        return """
// Settings Web Module - Fallback Module
class SettingsWebComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
        this.loadSettings();
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            this.renderSettings(settings);
        } catch (error) {
            this.shadowRoot.innerHTML = '<div>Error loading settings</div>';
        }
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: system-ui, sans-serif;
                    padding: 20px;
                }
                .loading { text-align: center; padding: 40px; }
            </style>
            <div class="loading">Loading settings...</div>
        `;
    }

    renderSettings(settings) {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: system-ui, sans-serif;
                    padding: 20px;
                }
                .settings-section {
                    margin-bottom: 20px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .setting-item { margin-bottom: 10px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, select { width: 100%; padding: 8px; margin-bottom: 10px; }
            </style>
            <div>
                <h2>Settings</h2>
                <div class="settings-section">
                    <h3>General</h3>
                    <div class="setting-item">
                        <label>App Name:</label>
                        <input type="text" value="${settings.general.app_name}" readonly>
                    </div>
                    <div class="setting-item">
                        <label>Theme:</label>
                        <select disabled>
                            <option value="light" ${settings.general.theme === 'light' ? 'selected' : ''}>Light</option>
                            <option value="dark" ${settings.general.theme === 'dark' ? 'selected' : ''}>Dark</option>
                        </select>
                    </div>
                </div>
                <p><em>Note: This is a fallback interface. Build the frontend for full functionality.</em></p>
            </div>
        `;
    }
}

export default SettingsWebComponent;
if (!customElements.get('settings-component')) {
    customElements.define('settings-component', SettingsWebComponent);
}
"""


class SettingsComponent(Module[GetSettings | UpdateSettings]):
    """Settings component for application configuration."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        """Register settings routes when component starts."""
        await super().on_start()
        if not self.registered:
            async with self.application.mediator.context() as ctx:
                # Register API endpoint
                await ctx.process(
                    RegisterView(route="/api/settings", view=SettingsAPIView)
                )
                # Register module endpoint
                await ctx.process(
                    RegisterView(route="/modules/settings.js", view=SettingsModuleView)
                )

            self.registered = True
            print("Settings component routes registered")

    async def handle(
        self,
        message: GetSettings | UpdateSettings,
        *,
        handler: Callable[[Message], Awaitable[None]],
        **_: Any,
    ) -> None:
        """Handle settings requests."""
        if isinstance(message, GetSettings):
            # Handle get settings request
            print("Processing GetSettings request")
            # Could fetch from database, emit events, etc.

        elif isinstance(message, UpdateSettings):
            # Handle update settings request
            print(f"Processing UpdateSettings request: {message.settings}")

            # Emit settings updated event
            async with self.application.mediator.context() as ctx:
                await ctx.process(SettingsUpdated(settings=message.settings))

        # Forward to next handler
        await handler(message)
