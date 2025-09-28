"""
Settings Module - Application configuration and settings.
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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
        # Mock settings data
        settings = {
            "general": {
                "app_name": "Module SPA",
                "app_description": "Dynamic component-based application",
                "timezone": "UTC",
                "language": "en-US",
                "theme": "light",
            },
            "security": {
                "session_timeout": 30,
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_symbols": False,
                },
                "two_factor_auth": False,
                "login_attempts": 5,
            },
            "notifications": {
                "email_notifications": True,
                "push_notifications": False,
                "digest_frequency": "daily",
                "notification_types": {
                    "system_alerts": True,
                    "user_activity": False,
                    "security_events": True,
                    "maintenance": True,
                },
            },
            "performance": {
                "cache_enabled": True,
                "cache_ttl": 3600,
                "compression_enabled": True,
                "lazy_loading": True,
                "analytics_tracking": True,
            },
            "integrations": {
                "third_party_apis": {
                    "google_analytics": {"enabled": False, "tracking_id": ""},
                    "sentry": {
                        "enabled": True,
                        "dsn": "https://example@sentry.io/123456",
                    },
                }
            },
        }

        return web.json_response(settings)

    async def post(self) -> web.Response:
        """Update application settings."""
        data = await self.request.json()

        # Mock settings update
        updated_settings = data.get("settings", {})

        return web.json_response(
            {
                "success": True,
                "message": "Settings updated successfully",
                "updated_at": time.time(),
                "settings": updated_settings,
            }
        )


class SettingsModuleView(web.View):
    """Serve the settings component as a secure ES6 module."""

    async def get(self) -> web.Response:
        """Return settings component as ES6 module."""
        module_code = """
        /**
         * Settings UI ES6 Module.
         */
        class SettingsWebComponent extends HTMLElement {
            constructor() {
                super();
                this.settings = {};
                this.attachShadow({ mode: 'open' });
            }

            connectedCallback() {
                this.render();
                this.loadSettings();
            }

            async loadSettings() {
                try {
                    const apiEndpoint = this.getAttribute('api-endpoint') || '/api/settings';
                    const response = await fetch(apiEndpoint);
                    this.settings = await response.json();
                    this.render();
                } catch (error) {
                    console.error('Failed to load settings:', error);
                }
            }

            async saveSettings() {
                try {
                    const apiEndpoint = this.getAttribute('api-endpoint') || '/api/settings';
                    const response = await fetch(apiEndpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ settings: this.settings })
                    });
                    if (response.ok) {
                        console.log('Settings saved successfully');
                    }
                } catch (error) {
                    console.error('Failed to save settings:', error);
                }
            }

            render() {
                if (!this.settings.general) {
                    this.shadowRoot.innerHTML = '<div>Loading settings...</div>';
                    return;
                }

                this.shadowRoot.innerHTML = `
                    <style>
                        :host { display: block; font-family: Arial, sans-serif; }
                        .settings-group { margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
                        .setting-item { margin-bottom: 10px; }
                        .setting-label { display: block; margin-bottom: 5px; font-weight: bold; }
                        .setting-input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                        .save-btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                    </style>
                    <div>
                        <h3>Application Settings</h3>
                        <div class="settings-group">
                            <h4>General Settings</h4>
                            <div class="setting-item">
                                <label class="setting-label">App Name</label>
                                <input class="setting-input" value="${this.settings.general.app_name}"
                                    onchange="this.getRootNode().host.updateSetting('general.app_name', this.value)">
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Theme</label>
                                <select class="setting-input" onchange="this.getRootNode().host.updateSetting('general.theme', this.value)">
                                    <option value="light" ${this.settings.general.theme === 'light' ? 'selected' : ''}>Light</option>
                                    <option value="dark" ${this.settings.general.theme === 'dark' ? 'selected' : ''}>Dark</option>
                                </select>
                            </div>
                        </div>
                        <button class="save-btn" onclick="this.getRootNode().host.saveSettings()">Save Settings</button>
                    </div>
                `;
            }

            updateSetting(path, value) {
                const keys = path.split('.');
                let current = this.settings;
                for (let i = 0; i < keys.length - 1; i++) {
                    current = current[keys[i]];
                }
                current[keys[keys.length - 1]] = value;
            }
        }

        // Export and register the component
        export default SettingsWebComponent;
        if (!customElements.get('settings-component')) {
            customElements.define('settings-component', SettingsWebComponent);
        }
        """

        return web.Response(
            text=module_code,
            content_type="application/javascript",
            headers={"Content-Security-Policy": "default-src 'self'"},
        )


class SettingsModule(Module[GetSettings | UpdateSettings]):
    """Settings component for application configuration."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register settings routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/settings", view=SettingsAPIView))
                await ctx.process(RegisterView(route="/modules/settings.js", view=SettingsModuleView))

            self.registered = True
            print("Settings component routes registered")

    async def handle(
        self,
        message: GetSettings | UpdateSettings,
        *,
        handler: Callable[[Message], Awaitable[None]],  # callback
        **_: Any,
    ) -> None:
        """Handle settings requests."""
        if isinstance(message, GetSettings):
            # Handle get settings request
            pass
        elif isinstance(message, UpdateSettings):
            # Handle settings update
            await handler(SettingsUpdated(settings=message.settings))
