"""
Dashboard Component - System overview and metrics.
"""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web

from nether.component import Component
from nether.message import Event, Message, Query
from nether.server import RegisterView


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
                {"name": "Response Time", "value": "142ms", "trend": "down", "change": "-8%"},
                {"name": "Throughput", "value": "2.1k/min", "trend": "up", "change": "+12%"},
                {"name": "Error Rate", "value": "0.015%", "trend": "stable", "change": "0%"},
                {"name": "Active Sessions", "value": "342", "trend": "up", "change": "+5%"},
                {"name": "Database Connections", "value": "28/100", "trend": "stable", "change": "0%"},
                {"name": "Cache Hit Rate", "value": "94.2%", "trend": "up", "change": "+2%"},
            ],
            "recent_activity": [
                {"time": "1 min ago", "action": "System health check completed", "user": "monitoring", "status": "success"},
                {"time": "3 min ago", "action": "User session created", "user": "alice.johnson", "status": "success"},
                {"time": "5 min ago", "action": "Data backup initiated", "user": "system", "status": "in_progress"},
                {"time": "7 min ago", "action": "API rate limit adjusted", "user": "admin", "status": "success"},
                {"time": "10 min ago", "action": "Database optimization", "user": "db_admin", "status": "success"},
                {"time": "12 min ago", "action": "Security scan completed", "user": "security", "status": "success"},
            ],
            "alerts": [
                {"level": "warning", "message": "Memory usage approaching 70% threshold", "time": "5 min ago"},
                {"level": "info", "message": "Scheduled maintenance in 2 hours", "time": "15 min ago"},
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
            }
        }
        return web.json_response(data)


class DashboardComponentView(web.View):
    """Serve the dashboard web component HTML."""

    async def get(self) -> web.Response:
        """Return dashboard component HTML."""
        html = """
<div class="component-header">
    <h1 class="component-title">📊 Dashboard</h1>
    <p class="component-description">System overview and real-time metrics</p>
</div>

<style>
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
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
    .activity-item:last-child {
        border-bottom: none;
    }
    .activity-time {
        color: #7f8c8d;
        font-size: 0.9em;
    }

    .loading {
        text-align: center;
        padding: 40px;
        color: #7f8c8d;
    }
</style>

<div id="dashboard-content">
    <div class="loading">Loading dashboard data...</div>
</div>

<script>
    // Dashboard component logic
    class DashboardComponent {
        constructor() {
            this.data = null;
            this.init();
        }

        async init() {
            await this.loadData();
            this.render();

            // Listen for component loaded event
            window.addEventListener('component-dashboard-loaded', (event) => {
                this.data = event.detail.data;
                this.render();
            });

            // Auto-refresh every 30 seconds
            setInterval(() => this.refresh(), 30000);
        }

        async loadData() {
            try {
                const response = await fetch('/api/dashboard/data');
                this.data = await response.json();
            } catch (error) {
                console.error('Failed to load dashboard data:', error);
                this.data = { error: 'Failed to load data' };
            }
        }

        async refresh() {
            await this.loadData();
            this.render();
        }

        render() {
            const container = document.getElementById('dashboard-content');
            if (!this.data) return;

            if (this.data.error) {
                container.innerHTML = `<div class="error">Error: ${this.data.error}</div>`;
                return;
            }

            // Calculate uptime display
            const uptimeHours = Math.floor(this.data.uptime / 3600);
            const uptimeDisplay = `${Math.floor(uptimeHours / 24)}d ${uptimeHours % 24}h`;

            container.innerHTML = `
                <!-- System Status Overview -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
                    <div class="metric-card" style="border-left-color: #27ae60;">
                        <div class="metric-label">System Status</div>
                        <div class="metric-value" style="color: #27ae60; font-size: 1.5em;">
                            ${this.data.system_status.toUpperCase()}
                        </div>
                    </div>
                    <div class="metric-card" style="border-left-color: #3498db;">
                        <div class="metric-label">Uptime</div>
                        <div class="metric-value" style="font-size: 1.5em;">${uptimeDisplay}</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #e67e22;">
                        <div class="metric-label">Active Users</div>
                        <div class="metric-value" style="font-size: 1.5em;">${this.data.active_users}</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #9b59b6;">
                        <div class="metric-label">Total Requests</div>
                        <div class="metric-value" style="font-size: 1.5em;">${this.data.total_requests.toLocaleString()}</div>
                    </div>
                </div>

                <!-- Resource Usage -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 25px;">
                    <div class="metric-card">
                        <div class="metric-label">Memory Usage</div>
                        <div class="metric-value">${this.data.memory_usage}%</div>
                        <div style="background: #ecf0f1; height: 10px; border-radius: 5px; margin-top: 10px;">
                            <div style="background: ${this.data.memory_usage > 80 ? '#e74c3c' : this.data.memory_usage > 60 ? '#f39c12' : '#27ae60'}; 
                                        height: 100%; width: ${this.data.memory_usage}%; border-radius: 5px; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">CPU Usage</div>
                        <div class="metric-value">${this.data.cpu_usage}%</div>
                        <div style="background: #ecf0f1; height: 10px; border-radius: 5px; margin-top: 10px;">
                            <div style="background: ${this.data.cpu_usage > 80 ? '#e74c3c' : this.data.cpu_usage > 60 ? '#f39c12' : '#27ae60'}; 
                                        height: 100%; width: ${this.data.cpu_usage}%; border-radius: 5px; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Disk Usage</div>
                        <div class="metric-value">${this.data.disk_usage}%</div>
                        <div style="background: #ecf0f1; height: 10px; border-radius: 5px; margin-top: 10px;">
                            <div style="background: ${this.data.disk_usage > 80 ? '#e74c3c' : this.data.disk_usage > 60 ? '#f39c12' : '#27ae60'}; 
                                        height: 100%; width: ${this.data.disk_usage}%; border-radius: 5px; transition: width 0.3s;"></div>
                        </div>
                    </div>
                </div>

                <!-- Alerts Section -->
                ${this.data.alerts && this.data.alerts.length > 0 ? `
                <div style="margin-bottom: 25px;">
                    <h3 style="margin-bottom: 15px;">🚨 Active Alerts</h3>
                    ${this.data.alerts.map(alert => `
                        <div style="padding: 12px 15px; border-radius: 5px; margin-bottom: 10px; 
                                    background: ${alert.level === 'warning' ? '#fff3cd' : '#d1ecf1'}; 
                                    border-left: 4px solid ${alert.level === 'warning' ? '#ffc107' : '#17a2b8'};">
                            <strong>${alert.level.toUpperCase()}:</strong> ${alert.message}
                            <div style="font-size: 0.9em; color: #6c757d; margin-top: 5px;">${alert.time}</div>
                        </div>
                    `).join('')}
                </div>
                ` : ''}

                <!-- Performance Metrics -->
                <div class="dashboard-grid">
                    ${this.data.metrics.map(metric => `
                        <div class="metric-card">
                            <div class="metric-label">${metric.name}</div>
                            <div class="metric-value">
                                ${metric.value}
                                <span class="metric-trend trend-${metric.trend}">
                                    ${metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'}
                                    ${metric.change}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Network I/O -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;">
                    <div class="metric-card" style="border-left-color: #17a2b8;">
                        <div class="metric-label">Network In</div>
                        <div class="metric-value" style="color: #17a2b8;">${this.data.network_io.incoming}</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #28a745;">
                        <div class="metric-label">Network Out</div>
                        <div class="metric-value" style="color: #28a745;">${this.data.network_io.outgoing}</div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="activity-list">
                    <div class="activity-header">📋 Recent System Activity</div>
                    ${this.data.recent_activity.map(activity => `
                        <div class="activity-item">
                            <div>
                                <strong>${activity.action}</strong>
                                <br><small>by ${activity.user}</small>
                                ${activity.status ? `<span style="float: right; padding: 2px 8px; border-radius: 10px; 
                                    font-size: 0.7em; background: ${activity.status === 'success' ? '#d4edda' : 
                                    activity.status === 'in_progress' ? '#fff3cd' : '#f8d7da'}; 
                                    color: ${activity.status === 'success' ? '#155724' : 
                                    activity.status === 'in_progress' ? '#856404' : '#721c24'};">
                                    ${activity.status.replace('_', ' ').toUpperCase()}
                                </span>` : ''}
                            </div>
                            <div class="activity-time">${activity.time}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    // Initialize when this component is loaded
    if (document.getElementById('dashboard-content')) {
        new DashboardComponent();
    }
</script>
        """
        return web.Response(text=html, content_type="text/html")


class DashboardComponent(Component[GetDashboardData]):
    """Dashboard component for system overview and metrics."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register dashboard routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/dashboard/data", view=DashboardAPIView))
                await ctx.process(RegisterView(route="/components/dashboard", view=DashboardComponentView))

            self.registered = True
            print("📊 Dashboard component routes registered")

    async def handle(
        self, message: GetDashboardData, *, handler: Callable[[Message], Awaitable[None]], **_: Any
    ) -> None:
        """Handle dashboard data requests."""
        # In a real application, this would fetch actual metrics
        data = {
            "status": "success",
            "timestamp": time.time(),
            "metrics": {"active_users": 42, "total_requests": 15623, "error_rate": 0.02},
        }

        await handler(DashboardDataRetrieved(data=data))
