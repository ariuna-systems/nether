"""
Dashboard Component - Complete system overview and metrics
Includes: API endpoints, Nether component, and secure ES6 module serving
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from nether.component import Component
from nether.message import Event, Message, Query
from nether.server import RegisterView

__all__ = ["DashboardComponent"]


@dataclass(frozen=True, kw_only=True, slots=True)
class GetDashboardData(Query):
    """Query to get dashboard data."""

    ...


@dataclass(frozen=True, kw_only=True, slots=True)
class DashboardDataRetrieved(Event):
    """Event when dashboard data is retrieved."""

    data: dict[str, Any]


class DashboardAPIView(web.View):
    """API endpoints for dashboard operations."""

    async def get(self) -> web.Response:
        """Get dashboard data."""
        # Enhanced dashboard data with more realistic metrics
        data = {
            "system_status": "healthy",
            "uptime": time.time() - 86400,  # 1 day uptime
            "active_users": 342,
            "total_requests": 156234,
            "error_rate": 0.015,
            "memory_usage": 68.7,
            "cpu_usage": 34.2,
            "disk_usage": 45.8,
            "network_io": {"incoming": "12.4 MB/s", "outgoing": "8.7 MB/s"},
            "metrics": [
                {
                    "name": "Response Time",
                    "value": "142ms",
                    "trend": "down",
                    "change": "-8%",
                },
                {
                    "name": "Throughput",
                    "value": "2.1k/min",
                    "trend": "up",
                    "change": "+12%",
                },
                {
                    "name": "Error Rate",
                    "value": "0.015%",
                    "trend": "stable",
                    "change": "0%",
                },
                {
                    "name": "Active Sessions",
                    "value": "342",
                    "trend": "up",
                    "change": "+5%",
                },
                {
                    "name": "Database Connections",
                    "value": "28/100",
                    "trend": "stable",
                    "change": "0%",
                },
                {
                    "name": "Cache Hit Rate",
                    "value": "94.2%",
                    "trend": "up",
                    "change": "+2%",
                },
            ],
            "recent_activity": [
                {
                    "time": "1 min ago",
                    "action": "System health check completed",
                    "user": "monitoring",
                    "status": "success",
                },
                {
                    "time": "3 min ago",
                    "action": "User session created",
                    "user": "alice.johnson",
                    "status": "success",
                },
                {
                    "time": "5 min ago",
                    "action": "Data backup initiated",
                    "user": "system",
                    "status": "in_progress",
                },
                {
                    "time": "7 min ago",
                    "action": "API rate limit adjusted",
                    "user": "admin",
                    "status": "success",
                },
                {
                    "time": "10 min ago",
                    "action": "Database optimization",
                    "user": "db_admin",
                    "status": "success",
                },
                {
                    "time": "12 min ago",
                    "action": "Security scan completed",
                    "user": "security",
                    "status": "success",
                },
            ],
            "alerts": [
                {
                    "level": "warning",
                    "message": "Memory usage approaching 70% threshold",
                    "time": "5 min ago",
                },
                {
                    "level": "info",
                    "message": "Scheduled maintenance in 2 hours",
                    "time": "15 min ago",
                },
            ],
            "performance_data": {
                "last_24h": [
                    {"time": "00:00", "requests": 1200, "errors": 2},
                    {"time": "04:00", "requests": 800, "errors": 1},
                    {"time": "08:00", "requests": 2100, "errors": 3},
                    {"time": "12:00", "requests": 3200, "errors": 5},
                    {"time": "16:00", "requests": 2800, "errors": 2},
                    {"time": "20:00", "requests": 1900, "errors": 1},
                ]
            },
        }
        return web.json_response(data)


class DashboardComponentView(web.View):
    """Serve the dashboard component HTML (non-module) so SPA fallback works."""

    async def get(self) -> web.Response:
        html = """
<div class="component-header">
    <h1 class="component-title">Dashboard</h1>
    <p class="component-description">System overview and real-time metrics</p>
</div>

<dashboard-component api-endpoint="/api/dashboard/data"></dashboard-component>

<style>
    dashboard-component {
        display: block;
        min-height: 200px;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background: #f9f9f9;
    }
    dashboard-component:empty::after {
        content: "Loading dashboard component...";
        color: #666;
        font-style: italic;
        display: block;
        padding: 20px;
        text-align: center;
    }
</style>
<script type="module">
// Enhanced dashboard loader with better debugging
const DASHBOARD_TAG = 'dashboard-component';

console.log('[dashboard-loader] Starting dashboard component loading...');

async function loadDashboardModule(retries = 8) {
    console.log(`[dashboard-loader] Attempting to load module, retries left: ${retries}`);

    if (customElements.get(DASHBOARD_TAG)) {
        console.log('[dashboard-loader] Custom element already defined');
        return true;
    }

    try {
        console.log('[dashboard-loader] Importing module from /modules/dashboard.js');
        await import('/modules/dashboard.js');
        console.log('[dashboard-loader] Module imported successfully');

        // Wait for custom element to register
        await new Promise(resolve => setTimeout(resolve, 100));

        if (customElements.get(DASHBOARD_TAG)) {
            console.log('[dashboard-loader] Custom element is now defined');
            return true;
        } else {
            console.warn('[dashboard-loader] Custom element still not defined after import');
            return false;
        }

    } catch (err) {
        console.warn('[dashboard-loader] Module import failed', err);
        if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, 500));
            return loadDashboardModule(retries - 1);
        } else {
            const el = document.querySelector(DASHBOARD_TAG);
            if (el) {
                el.innerHTML = '<div style="padding:12px;color:#e74c3c;font-family:system-ui;">Failed to load dashboard module after multiple attempts.</div>';
            }
            return false;
        }
    }
}

// Check dashboard element status
function checkDashboardElement() {
    const el = document.querySelector(DASHBOARD_TAG);
    if (el) {
        console.log('[dashboard-loader] Dashboard element found:', el);
        console.log('[dashboard-loader] Element connected:', el.isConnected);
        console.log('[dashboard-loader] Has shadow root:', !!el.shadowRoot);
        console.log('[dashboard-loader] Element content:', el.innerHTML);

        // Add data loaded listener
        el.addEventListener('dashboard-loaded', (event) => {
            console.log('[dashboard-loader] Dashboard data loaded event:', event.detail);
        });
    } else {
        console.warn('[dashboard-loader] Dashboard element not found');
    }
}

// Start the loading process
loadDashboardModule().then(success => {
    console.log('[dashboard-loader] Module loading result:', success);
    setTimeout(checkDashboardElement, 500);
});

// Also check periodically
let checkCount = 0;
const checker = setInterval(() => {
    checkCount++;
    checkDashboardElement();
    if (checkCount >= 5) {
        clearInterval(checker);
    }
}, 1000);
</script>
        """
        return web.Response(text=html, content_type="text/html")


class DashboardModuleView(web.View):
    """Serve the dashboard component as a secure ES6 module."""

    async def get(self) -> web.Response:
        """Return dashboard component as ES6 module."""
        module_code = """
// Dashboard Web Component - ES6 Module
// Secure, self-contained dashboard component

class DashboardWebComponent extends HTMLElement {
    constructor() {
        super();
        this.data = null;
        this.refreshInterval = null;

        // Create shadow DOM for encapsulation
        this.attachShadow({ mode: 'open' });

        console.log('Secure Dashboard web component constructed');
    }

    // Web Component lifecycle: called when element is added to DOM
    connectedCallback() {
        console.log('Secure Dashboard web component connected to DOM');
        this.render();
        this.setupEventListeners();
        this.loadData();

        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => this.loadData(), 30000);
    }

    // Web Component lifecycle: called when element is removed from DOM
    disconnectedCallback() {
        console.log('Secure Dashboard web component disconnected from DOM');
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.cleanup();
    }

    // Web Component lifecycle: called when attributes change
    attributeChangedCallback(name, oldValue, newValue) {
        console.log(`Dashboard attribute ${name} changed from ${oldValue} to ${newValue}`);
        if (name === 'api-endpoint' && oldValue !== newValue) {
            this.loadData();
        }
    }

    // Define which attributes to observe
    static get observedAttributes() {
        return ['api-endpoint', 'refresh-interval'];
    }

    setupEventListeners() {
        // Listen for external data events (for SPA integration)
        window.addEventListener('dashboard-data-updated', (event) => {
            console.log('Dashboard received external data update:', event.detail);
            this.data = event.detail.data;
            this.renderContent();
        });
    }

    cleanup() {
        // Remove event listeners to prevent memory leaks
        window.removeEventListener('dashboard-data-updated', this.handleDataUpdate);
    }

    async loadData() {
        try {
            const apiEndpoint = this.getAttribute('api-endpoint') || '/api/dashboard/data';
            console.log(`Loading dashboard data from ${apiEndpoint}`);

            const response = await fetch(apiEndpoint, {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.data = await response.json();
            console.log('Secure dashboard data loaded:', this.data);
            this.renderContent();

            // Dispatch event for external listeners
            this.dispatchEvent(new CustomEvent('dashboard-loaded', {
                detail: { data: this.data },
                bubbles: true
            }));

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.data = { error: 'Failed to load data: ' + error.message };
            this.renderContent();
        }
    }

    render() {
        // Create the basic structure with enhanced security styling
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    white-space: normal;
                }

                .security-badge {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: #27ae60;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }

                .component-header {
                    border-bottom: 2px solid #3498db;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    position: relative;
                }

                .component-title {
                    color: #2c3e50;
                    font-size: 24px;
                    margin: 0;
                }

                .component-description {
                    color: #7f8c8d;
                    margin: 5px 0 0 0;
                }

                .metric-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-left: 4px solid #3498db;
                }

                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 10px 0;
                }

                .metric-label {
                    color: #7f8c8d;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                .metric-trend {
                    font-size: 0.8em;
                    padding: 2px 8px;
                    border-radius: 12px;
                    margin-left: 10px;
                }

                .trend-up { background: #d4edda; color: #155724; }
                .trend-down { background: #f8d7da; color: #721c24; }
                .trend-stable { background: #fff3cd; color: #856404; }

                .activity-list {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }

                .activity-header {
                    padding: 15px 20px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #dee2e6;
                    font-weight: bold;
                }

                .activity-item {
                    padding: 15px 20px;
                    border-bottom: 1px solid #f1f1f1;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .activity-item:last-child { border-bottom: none; }
                .activity-time { color: #7f8c8d; font-size: 0.9em; }
                .loading { text-align: center; padding: 40px; color: #7f8c8d; }
                .error { color: #e74c3c; padding: 20px; background: #f8f9fa; border-radius: 5px; border: 1px solid #e74c3c; }
            </style>

            <div class="component-header">
                <div class="security-badge">SECURE</div>
                <h1 class="component-title">Dashboard</h1>
                <p class="component-description">Secure system overview and real-time metrics</p>
            </div>

            <div id="dashboard-content">
                <div class="loading">Loading secure dashboard data...</div>
            </div>
        `;
    }

    renderContent() {
        const container = this.shadowRoot.getElementById('dashboard-content');

        if (!this.data) {
            container.innerHTML = '<div class="loading">Loading secure dashboard data...</div>';
            return;
        }

        if (this.data.error) {
            container.innerHTML = `<div class="error">Security Error: ${this.escapeHtml(this.data.error)}</div>`;
            return;
        }

        // Calculate uptime display
        const uptimeHours = Math.floor(this.data.uptime / 3600);
        const uptimeDisplay = `${Math.floor(uptimeHours / 24)}d ${uptimeHours % 24}h`;

        // Secure HTML generation with proper escaping
        container.innerHTML = `
            <!-- System Status Overview -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
                <div class="metric-card" style="border-left-color: #27ae60;">
                    <div class="metric-label">System Status</div>
                    <div class="metric-value" style="color: #27ae60; font-size: 1.5em;">
                        ${this.escapeHtml(this.data.system_status.toUpperCase())}
                    </div>
                </div>
                <div class="metric-card" style="border-left-color: #3498db;">
                    <div class="metric-label">Uptime</div>
                    <div class="metric-value" style="font-size: 1.5em;">${this.escapeHtml(uptimeDisplay)}</div>
                </div>
                <div class="metric-card" style="border-left-color: #e67e22;">
                    <div class="metric-label">Active Users</div>
                    <div class="metric-value" style="font-size: 1.5em;">${this.escapeHtml(String(this.data.active_users))}</div>
                </div>
                <div class="metric-card" style="border-left-color: #9b59b6;">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-value" style="font-size: 1.5em;">${this.escapeHtml(this.data.total_requests.toLocaleString())}</div>
                </div>
            </div>

            <!-- Resource Usage -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 25px;">
                ${this.renderResourceUsage('Memory Usage', this.data.memory_usage)}
                ${this.renderResourceUsage('CPU Usage', this.data.cpu_usage)}
                ${this.renderResourceUsage('Disk Usage', this.data.disk_usage)}
            </div>

            <!-- Performance Metrics -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                ${this.data.metrics.map(metric => this.renderMetricCard(metric)).join('')}
            </div>

            <!-- Recent Activity -->
            <div class="activity-list">
                <div class="activity-header">Recent Secure Activity</div>
                ${this.data.recent_activity.map(activity => `
                    <div class="activity-item">
                        <div>
                            <strong>${this.escapeHtml(activity.action)}</strong>
                            <br><small>by ${this.escapeHtml(activity.user)}</small>
                        </div>
                        <div class="activity-time">${this.escapeHtml(activity.time)}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderResourceUsage(label, value) {
        const safeLabel = this.escapeHtml(label);
        const safeValue = this.escapeHtml(String(value));
        const color = value > 80 ? '#e74c3c' : value > 60 ? '#f39c12' : '#27ae60';

        return `
            <div class="metric-card">
                <div class="metric-label">${safeLabel}</div>
                <div class="metric-value">${safeValue}%</div>
                <div style="background: #ecf0f1; height: 10px; border-radius: 5px; margin-top: 10px;">
                    <div style="background: ${color}; height: 100%; width: ${value}%; border-radius: 5px; transition: width 0.3s;"></div>
                </div>
            </div>
        `;
    }

    renderMetricCard(metric) {
        return `
            <div class="metric-card">
                <div class="metric-label">${this.escapeHtml(metric.name)}</div>
                <div class="metric-value">
                    ${this.escapeHtml(metric.value)}
                    <span class="metric-trend trend-${this.escapeHtml(metric.trend)}">
                        ${metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'}
                        ${this.escapeHtml(metric.change)}
                    </span>
                </div>
            </div>
        `;
    }

    // Security: HTML escaping to prevent XSS
    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') {
            return String(unsafe);
        }
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Export the component class
export default DashboardWebComponent;

// Also provide named export for flexibility
export { DashboardWebComponent };

// Register the custom element if not already defined
if (!customElements.get('dashboard-component')) {
    customElements.define('dashboard-component', DashboardWebComponent);
}

console.log('Secure Dashboard component module loaded');
"""

        return web.Response(
            text=module_code,
            content_type="application/javascript",
            headers={
                "Content-Security-Policy": "default-src 'self'",
                "X-Content-Type-Options": "nosniff",
            },
        )


class DashboardComponent(Component[GetDashboardData]):
    """Dashboard component for system overview and metrics."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register both API and module routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(
                    RegisterView(route="/api/dashboard/data", view=DashboardAPIView)
                )
                await ctx.process(
                    RegisterView(
                        route="/modules/dashboard.js", view=DashboardModuleView
                    )
                )
                # Provide an HTML endpoint similar to other components so the SPA can fetch /components/dashboard
                await ctx.process(
                    RegisterView(
                        route="/components/dashboard", view=DashboardComponentView
                    )
                )

            self.registered = True
            print("Dashboard component routes registered (API + secure ES6 module)")

    async def handle(
        self,
        message: GetDashboardData,
        *,
        handler: Callable[[Message], Awaitable[None]],
        **_: Any,
    ) -> None:
        """Handle dashboard data requests."""
        # In a real application, this would fetch actual metrics
        data = {
            "status": "success",
            "timestamp": time.time(),
            "metrics": {
                "active_users": 42,
                "total_requests": 15623,
                "error_rate": 0.02,
            },
        }

        await handler(DashboardDataRetrieved(data=data))
