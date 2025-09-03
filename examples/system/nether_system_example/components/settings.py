"""
Settings Component - Application configuration and settings.
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from nether.component import Component
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
                "app_name": "Component SPA",
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


class SettingsComponentView(web.View):
    """Serve the settings web component HTML."""

    async def get(self) -> web.Response:
        """Return settings component HTML."""
        html = """
<div class="component-header">
    <h1 class="component-title">Settings</h1>
    <p class="component-description">Configure application preferences and system settings</p>
</div>

<style>
    .settings-container {
        display: flex;
        gap: 20px;
    }

    .settings-sidebar {
        width: 200px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 20px;
        height: fit-content;
    }

    .settings-main {
        flex: 1;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 20px;
    }

    .settings-nav {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .settings-nav-item {
        margin-bottom: 5px;
    }

    .settings-nav-link {
        display: block;
        padding: 10px 15px;
        color: #2c3e50;
        text-decoration: none;
        border-radius: 5px;
        transition: background 0.3s;
        cursor: pointer;
    }

    .settings-nav-link:hover,
    .settings-nav-link.active {
        background: #f8f9fa;
        color: #3498db;
    }

    .settings-section {
        display: none;
    }

    .settings-section.active {
        display: block;
    }

    .section-title {
        font-size: 1.5em;
        color: #2c3e50;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f1f1f1;
    }

    .settings-form {
        max-width: 600px;
    }

    .form-group {
        margin-bottom: 20px;
    }

    .form-label {
        display: block;
        margin-bottom: 8px;
        font-weight: bold;
        color: #2c3e50;
    }

    .form-input,
    .form-select,
    .form-textarea {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 14px;
        transition: border-color 0.3s;
    }

    .form-input:focus,
    .form-select:focus,
    .form-textarea:focus {
        outline: none;
        border-color: #3498db;
    }

    .form-checkbox {
        margin-right: 8px;
    }

    .checkbox-group {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }

    .form-description {
        font-size: 0.9em;
        color: #7f8c8d;
        margin-top: 5px;
    }

    .btn-primary {
        background: #3498db;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        margin-right: 10px;
    }

    .btn-primary:hover {
        background: #2980b9;
    }

    .btn-secondary {
        background: #95a5a6;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
    }

    .btn-secondary:hover {
        background: #7f8c8d;
    }

    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        display: none;
    }

    .section-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
    }

    .loading {
        text-align: center;
        padding: 40px;
        color: #7f8c8d;
    }
</style>

<div id="settings-content">
    <div class="loading">Loading settings...</div>
</div>

<script>
    class SettingsComponent {
        constructor() {
            this.data = null;
            this.currentSection = 'general';
            this.init();
        }

        async init() {
            await this.loadData();
            this.render();

            // Listen for component loaded event
            window.addEventListener('component-settings-loaded', (event) => {
                this.data = event.detail.data;
                this.render();
            });
        }

        async loadData() {
            try {
                const response = await fetch('/api/settings/data');
                this.data = await response.json();
            } catch (error) {
                console.error('Failed to load settings data:', error);
                this.data = { error: 'Failed to load data' };
            }
        }

        async saveSettings() {
            try {
                const formData = new FormData(document.getElementById('settings-form'));
                const settings = {};

                // Convert form data to nested object structure
                for (const [key, value] of formData.entries()) {
                    const parts = key.split('.');
                    let current = settings;
                    for (let i = 0; i < parts.length - 1; i++) {
                        if (!current[parts[i]]) {
                            current[parts[i]] = {};
                        }
                        current = current[parts[i]];
                    }
                    current[parts[parts.length - 1]] = value === 'on' ? true : value;
                }

                const response = await fetch('/api/settings/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ settings })
                });

                if (response.ok) {
                    this.showSuccessMessage('Settings saved successfully!');
                    await this.loadData();
                    this.render();
                }
            } catch (error) {
                console.error('Failed to save settings:', error);
            }
        }

        showSuccessMessage(message) {
            const successEl = document.querySelector('.success-message');
            if (successEl) {
                successEl.textContent = message;
                successEl.style.display = 'block';
                setTimeout(() => {
                    successEl.style.display = 'none';
                }, 3000);
            }
        }

        switchSection(section) {
            this.currentSection = section;

            // Update nav
            document.querySelectorAll('.settings-nav-link').forEach(link => {
                link.classList.remove('active');
            });
            document.querySelector(`[data-section="${section}"]`).classList.add('active');

            // Update content
            document.querySelectorAll('.settings-section').forEach(sec => {
                sec.classList.remove('active');
            });
            document.getElementById(`section-${section}`).classList.add('active');
        }

        render() {
            const container = document.getElementById('settings-content');
            if (!this.data) return;

            if (this.data.error) {
                container.innerHTML = `<div class="error">Error: ${this.data.error}</div>`;
                return;
            }

            container.innerHTML = `
                <div class="settings-container">
                    <div class="settings-sidebar">
                        <ul class="settings-nav">
                            <li class="settings-nav-item">
                                <a class="settings-nav-link active" data-section="general" onclick="settingsComp.switchSection('general')">General</a>
                            </li>
                            <li class="settings-nav-item">
                                <a class="settings-nav-link" data-section="security" onclick="settingsComp.switchSection('security')">Security</a>
                            </li>
                            <li class="settings-nav-item">
                                <a class="settings-nav-link" data-section="notifications" onclick="settingsComp.switchSection('notifications')">Notifications</a>
                            </li>
                            <li class="settings-nav-item">
                                <a class="settings-nav-link" data-section="performance" onclick="settingsComp.switchSection('performance')">Performance</a>
                            </li>
                            <li class="settings-nav-item">
                                <a class="settings-nav-link" data-section="integrations" onclick="settingsComp.switchSection('integrations')">Integrations</a>
                            </li>
                        </ul>
                    </div>

                    <div class="settings-main">
                        <div class="success-message">Settings saved successfully!</div>

                        <form id="settings-form">
                            <!-- General Settings -->
                            <div id="section-general" class="settings-section active">
                                <h2 class="section-title">General Settings</h2>
                                <div class="form-group">
                                    <label class="form-label">Application Name</label>
                                    <input type="text" name="general.app_name" class="form-input" value="${this.data.general.app_name}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Description</label>
                                    <textarea name="general.app_description" class="form-textarea" rows="3">${this.data.general.app_description}</textarea>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Timezone</label>
                                    <select name="general.timezone" class="form-select">
                                        <option value="UTC" ${this.data.general.timezone === 'UTC' ? 'selected' : ''}>UTC</option>
                                        <option value="EST" ${this.data.general.timezone === 'EST' ? 'selected' : ''}>EST</option>
                                        <option value="PST" ${this.data.general.timezone === 'PST' ? 'selected' : ''}>PST</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Theme</label>
                                    <select name="general.theme" class="form-select">
                                        <option value="light" ${this.data.general.theme === 'light' ? 'selected' : ''}>Light</option>
                                        <option value="dark" ${this.data.general.theme === 'dark' ? 'selected' : ''}>Dark</option>
                                    </select>
                                </div>
                            </div>

                            <!-- Security Settings -->
                            <div id="section-security" class="settings-section">
                                <h2 class="section-title">Security Settings</h2>
                                <div class="form-group">
                                    <label class="form-label">Session Timeout (minutes)</label>
                                    <input type="number" name="security.session_timeout" class="form-input" value="${this.data.security.session_timeout}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Password Policy</label>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="security.password_policy.require_uppercase" class="form-checkbox" ${this.data.security.password_policy.require_uppercase ? 'checked' : ''}>
                                        <label>Require uppercase letters</label>
                                    </div>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="security.password_policy.require_numbers" class="form-checkbox" ${this.data.security.password_policy.require_numbers ? 'checked' : ''}>
                                        <label>Require numbers</label>
                                    </div>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="security.two_factor_auth" class="form-checkbox" ${this.data.security.two_factor_auth ? 'checked' : ''}>
                                        <label>Enable two-factor authentication</label>
                                    </div>
                                </div>
                            </div>

                            <!-- Notifications Settings -->
                            <div id="section-notifications" class="settings-section">
                                <h2 class="section-title">Notification Settings</h2>
                                <div class="form-group">
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="notifications.email_notifications" class="form-checkbox" ${this.data.notifications.email_notifications ? 'checked' : ''}>
                                        <label>Email notifications</label>
                                    </div>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="notifications.push_notifications" class="form-checkbox" ${this.data.notifications.push_notifications ? 'checked' : ''}>
                                        <label>Push notifications</label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Digest Frequency</label>
                                    <select name="notifications.digest_frequency" class="form-select">
                                        <option value="daily" ${this.data.notifications.digest_frequency === 'daily' ? 'selected' : ''}>Daily</option>
                                        <option value="weekly" ${this.data.notifications.digest_frequency === 'weekly' ? 'selected' : ''}>Weekly</option>
                                        <option value="monthly" ${this.data.notifications.digest_frequency === 'monthly' ? 'selected' : ''}>Monthly</option>
                                    </select>
                                </div>
                            </div>

                            <!-- Performance Settings -->
                            <div id="section-performance" class="settings-section">
                                <h2 class="section-title">Performance Settings</h2>
                                <div class="form-group">
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="performance.cache_enabled" class="form-checkbox" ${this.data.performance.cache_enabled ? 'checked' : ''}>
                                        <label>Enable caching</label>
                                    </div>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="performance.compression_enabled" class="form-checkbox" ${this.data.performance.compression_enabled ? 'checked' : ''}>
                                        <label>Enable compression</label>
                                    </div>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="performance.lazy_loading" class="form-checkbox" ${this.data.performance.lazy_loading ? 'checked' : ''}>
                                        <label>Enable lazy loading</label>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Cache TTL (seconds)</label>
                                    <input type="number" name="performance.cache_ttl" class="form-input" value="${this.data.performance.cache_ttl}">
                                </div>
                            </div>

                            <!-- Integrations Settings -->
                            <div id="section-integrations" class="settings-section">
                                <h2 class="section-title">Integration Settings</h2>
                                <div class="form-group">
                                    <label class="form-label">Google Analytics</label>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="integrations.third_party_apis.google_analytics.enabled" class="form-checkbox" ${this.data.integrations.third_party_apis.google_analytics.enabled ? 'checked' : ''}>
                                        <label>Enable Google Analytics</label>
                                    </div>
                                    <input type="text" name="integrations.third_party_apis.google_analytics.tracking_id" class="form-input" placeholder="Tracking ID" value="${this.data.integrations.third_party_apis.google_analytics.tracking_id}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Sentry</label>
                                    <div class="checkbox-group">
                                        <input type="checkbox" name="integrations.third_party_apis.sentry.enabled" class="form-checkbox" ${this.data.integrations.third_party_apis.sentry.enabled ? 'checked' : ''}>
                                        <label>Enable Sentry error tracking</label>
                                    </div>
                                    <input type="text" name="integrations.third_party_apis.sentry.dsn" class="form-input" placeholder="Sentry DSN" value="${this.data.integrations.third_party_apis.sentry.dsn}">
                                </div>
                            </div>
                        </form>

                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #f1f1f1;">
                            <button type="button" class="btn-primary" onclick="settingsComp.saveSettings()">Save Settings</button>
                            <button type="button" class="btn-secondary" onclick="settingsComp.loadData(); settingsComp.render();">Reset</button>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // Initialize when this component is loaded
    if (document.getElementById('settings-content')) {
        window.settingsComp = new SettingsComponent();
    }
</script>
        """
        return web.Response(text=html, content_type="text/html")


class SettingsComponent(Component[GetSettings | UpdateSettings]):
    """Settings component for application configuration."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register settings routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(
                    RegisterView(route="/api/settings/data", view=SettingsAPIView)
                )
                await ctx.process(
                    RegisterView(
                        route="/components/settings", view=SettingsComponentView
                    )
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
            pass
        elif isinstance(message, UpdateSettings):
            # Handle settings update
            await handler(SettingsUpdated(settings=message.settings))
