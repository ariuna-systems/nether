"""
Analytics Component - Data analytics and reporting.
"""

import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web

from nether.component import Component
from nether.message import Event, Message, Query
from nether.server import RegisterView


@dataclass(frozen=True, kw_only=True, slots=True)
class GetAnalyticsData(Query):
    """Query to get analytics data."""

    period: str = "7d"


@dataclass(frozen=True, kw_only=True, slots=True)
class AnalyticsDataRetrieved(Event):
    """Event when analytics data is retrieved."""

    data: dict[str, Any]


class AnalyticsAPIView(web.View):
    """API endpoints for analytics operations."""

    async def get(self) -> web.Response:
        """Get analytics data."""
        # Comprehensive mock analytics data
        data = {
            "overview": {
                "total_pageviews": 156789,
                "unique_visitors": 12341,
                "bounce_rate": 0.28,
                "avg_session_duration": "4m 23s",
                "conversion_rate": 0.034,
                "revenue": 45678.90,
                "growth": {"pageviews": "+12.5%", "visitors": "+8.3%", "bounce_rate": "-5.2%", "revenue": "+18.7%"},
            },
            "traffic_sources": [
                {"source": "Direct", "visitors": 5420, "percentage": 43.9, "growth": "+15.2%", "revenue": 18234.50},
                {
                    "source": "Google Search",
                    "visitors": 3982,
                    "percentage": 32.3,
                    "growth": "+8.7%",
                    "revenue": 15678.20,
                },
                {
                    "source": "Social Media",
                    "visitors": 1521,
                    "percentage": 12.3,
                    "growth": "+22.1%",
                    "revenue": 6789.40,
                },
                {
                    "source": "Email Campaigns",
                    "visitors": 845,
                    "percentage": 6.8,
                    "growth": "+5.4%",
                    "revenue": 3456.80,
                },
                {"source": "Referrals", "visitors": 573, "percentage": 4.6, "growth": "-2.1%", "revenue": 1520.00},
            ],
            "page_views_daily": [
                {"date": "2024-03-14", "views": 2250, "unique": 1420, "bounce": 0.31},
                {"date": "2024-03-15", "views": 2180, "unique": 1380, "bounce": 0.29},
                {"date": "2024-03-16", "views": 2420, "unique": 1520, "bounce": 0.26},
                {"date": "2024-03-17", "views": 2580, "unique": 1650, "bounce": 0.24},
                {"date": "2024-03-18", "views": 2780, "unique": 1750, "bounce": 0.22},
                {"date": "2024-03-19", "views": 3120, "unique": 1980, "bounce": 0.25},
                {"date": "2024-03-20", "views": 2950, "unique": 1820, "bounce": 0.28},
            ],
            "page_views_hourly": [
                {"hour": "00:00", "views": 45},
                {"hour": "01:00", "views": 32},
                {"hour": "02:00", "views": 28},
                {"hour": "03:00", "views": 35},
                {"hour": "04:00", "views": 42},
                {"hour": "05:00", "views": 58},
                {"hour": "06:00", "views": 78},
                {"hour": "07:00", "views": 125},
                {"hour": "08:00", "views": 185},
                {"hour": "09:00", "views": 245},
                {"hour": "10:00", "views": 298},
                {"hour": "11:00", "views": 342},
                {"hour": "12:00", "views": 367},
                {"hour": "13:00", "views": 385},
                {"hour": "14:00", "views": 378},
                {"hour": "15:00", "views": 356},
                {"hour": "16:00", "views": 332},
                {"hour": "17:00", "views": 298},
                {"hour": "18:00", "views": 265},
                {"hour": "19:00", "views": 234},
                {"hour": "20:00", "views": 198},
                {"hour": "21:00", "views": 156},
                {"hour": "22:00", "views": 124},
                {"hour": "23:00", "views": 89},
            ],
            "top_pages": [
                {"path": "/dashboard", "views": 15420, "unique": 8245, "bounce": 0.19, "avg_time": "3m 45s"},
                {"path": "/products", "views": 12890, "unique": 7234, "bounce": 0.24, "avg_time": "2m 12s"},
                {"path": "/pricing", "views": 9876, "unique": 6123, "bounce": 0.31, "avg_time": "1m 56s"},
                {"path": "/about", "views": 7654, "unique": 4567, "bounce": 0.28, "avg_time": "2m 34s"},
                {"path": "/contact", "views": 5432, "unique": 3456, "bounce": 0.35, "avg_time": "1m 23s"},
                {"path": "/blog", "views": 4321, "unique": 2890, "bounce": 0.42, "avg_time": "4m 12s"},
                {"path": "/support", "views": 3210, "unique": 2134, "bounce": 0.38, "avg_time": "3m 01s"},
            ],
            "devices": [
                {"type": "Desktop", "visitors": 7245, "percentage": 58.7, "bounce": 0.23, "revenue": 32456.80},
                {"type": "Mobile", "visitors": 3892, "percentage": 31.5, "bounce": 0.34, "revenue": 10234.50},
                {"type": "Tablet", "visitors": 1204, "percentage": 9.8, "bounce": 0.29, "revenue": 2987.60},
            ],
            "browsers": [
                {"name": "Chrome", "visitors": 6789, "percentage": 55.0},
                {"name": "Safari", "visitors": 2456, "percentage": 19.9},
                {"name": "Firefox", "visitors": 1789, "percentage": 14.5},
                {"name": "Edge", "visitors": 892, "percentage": 7.2},
                {"name": "Opera", "visitors": 415, "percentage": 3.4},
            ],
            "geographic": [
                {"country": "United States", "visitors": 4256, "percentage": 34.5, "revenue": 18945.60},
                {"country": "United Kingdom", "visitors": 2134, "percentage": 17.3, "revenue": 9876.40},
                {"country": "Canada", "visitors": 1789, "percentage": 14.5, "revenue": 7234.20},
                {"country": "Germany", "visitors": 1456, "percentage": 11.8, "revenue": 6789.80},
                {"country": "Australia", "visitors": 987, "percentage": 8.0, "revenue": 4567.30},
                {"country": "France", "visitors": 856, "percentage": 6.9, "revenue": 3456.70},
                {"country": "Others", "visitors": 863, "percentage": 7.0, "revenue": 2789.90},
            ],
            "conversion_funnel": [
                {"stage": "Visitors", "count": 12341, "conversion": 100.0},
                {"stage": "Product Views", "count": 8756, "conversion": 70.9},
                {"stage": "Add to Cart", "count": 2134, "conversion": 17.3},
                {"stage": "Checkout Started", "count": 1067, "conversion": 8.6},
                {"stage": "Payment", "count": 678, "conversion": 5.5},
                {"stage": "Completed Purchase", "count": 420, "conversion": 3.4},
            ],
            "real_time": {
                "active_users": 127,
                "pageviews_last_hour": 245,
                "top_active_pages": [
                    {"page": "/dashboard", "users": 34},
                    {"page": "/products", "users": 28},
                    {"page": "/analytics", "users": 19},
                    {"page": "/pricing", "users": 15},
                    {"page": "/contact", "users": 12},
                ],
                "live_events": [
                    {
                        "time": "2 min ago",
                        "event": "Purchase completed",
                        "value": "$89.99",
                        "location": "New York, USA",
                    },
                    {
                        "time": "3 min ago",
                        "event": "User registration",
                        "value": "Premium Plan",
                        "location": "London, UK",
                    },
                    {"time": "5 min ago", "event": "Cart abandonment", "value": "$156.50", "location": "Toronto, CA"},
                    {"time": "7 min ago", "event": "Newsletter signup", "value": "Marketing", "location": "Berlin, DE"},
                    {"time": "9 min ago", "event": "Support ticket", "value": "Technical", "location": "Sydney, AU"},
                ],
            },
            "performance": {
                "page_load_time": 1.23,
                "server_response_time": 0.145,
                "total_blocking_time": 0.089,
                "largest_contentful_paint": 1.456,
                "cumulative_layout_shift": 0.023,
                "performance_score": 94,
            },
        }

        return web.json_response(data)


class AnalyticsComponentView(web.View):
    """Serve the analytics web component HTML."""

    async def get(self) -> web.Response:
        """Return analytics component HTML."""
        html = """
<div class="component-header">
    <h1 class="component-title">📈 Analytics</h1>
    <p class="component-description">Data insights and traffic analytics</p>
</div>

<style>
    .analytics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }

    .analytics-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .overview-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
    }

    .stat-box {
        text-align: center;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 6px;
    }

    .stat-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #3498db;
        margin-bottom: 5px;
    }

    .stat-label {
        color: #7f8c8d;
        font-size: 0.9em;
    }

    .chart-container {
        height: 200px;
        display: flex;
        align-items: end;
        justify-content: space-between;
        padding: 20px 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 10px;
    }

    .chart-bar {
        background: linear-gradient(to top, #3498db, #5dade2);
        width: 30px;
        border-radius: 2px 2px 0 0;
        margin: 0 2px;
        position: relative;
        transition: all 0.3s ease;
    }

    .chart-bar:hover {
        background: linear-gradient(to top, #2980b9, #3498db);
    }

    .chart-label {
        font-size: 0.8em;
        color: #7f8c8d;
        text-align: center;
        margin-top: 5px;
    }

    .source-list {
        list-style: none;
        padding: 0;
    }

    .source-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #f1f1f1;
    }

    .source-item:last-child {
        border-bottom: none;
    }

    .source-bar {
        height: 6px;
        background: #3498db;
        border-radius: 3px;
        margin: 5px 0;
    }

    .page-list {
        list-style: none;
        padding: 0;
    }

    .page-item {
        padding: 12px 0;
        border-bottom: 1px solid #f1f1f1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .page-item:last-child {
        border-bottom: none;
    }

    .page-path {
        font-family: monospace;
        color: #2c3e50;
        font-weight: bold;
    }

    .page-stats {
        text-align: right;
        font-size: 0.9em;
        color: #7f8c8d;
    }

    .device-chart {
        display: flex;
        gap: 10px;
        align-items: end;
        justify-content: center;
        height: 150px;
    }

    .device-bar {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    }

    .device-segment {
        width: 40px;
        border-radius: 4px;
        position: relative;
    }

    .device-desktop { background: #3498db; }
    .device-mobile { background: #e74c3c; }
    .device-tablet { background: #f39c12; }

    .device-label {
        font-size: 0.8em;
        color: #7f8c8d;
        text-align: center;
    }

    .loading {
        text-align: center;
        padding: 40px;
        color: #7f8c8d;
    }
</style>

<div id="analytics-content">
    <div class="loading">Loading analytics data...</div>
</div>

<script>
    class AnalyticsComponent {
        constructor() {
            this.data = null;
            this.init();
        }

        async init() {
            await this.loadData();
            this.render();

            // Listen for component loaded event
            window.addEventListener('component-analytics-loaded', (event) => {
                this.data = event.detail.data;
                this.render();
            });

            // Auto-refresh every 60 seconds
            setInterval(() => this.refresh(), 60000);
        }

        async loadData() {
            try {
                const response = await fetch('/api/analytics/data');
                this.data = await response.json();
            } catch (error) {
                console.error('Failed to load analytics data:', error);
                this.data = { error: 'Failed to load data' };
            }
        }

        async refresh() {
            await this.loadData();
            this.render();
        }

        render() {
            const container = document.getElementById('analytics-content');
            if (!this.data) return;

            if (this.data.error) {
                container.innerHTML = `<div class="error">Error: ${this.data.error}</div>`;
                return;
            }

            const maxViews = Math.max(...this.data.page_views_daily.map(pv => pv.views));
            const maxHourly = Math.max(...this.data.page_views_hourly.map(pv => pv.views));

            container.innerHTML = `
                <!-- Real-time Stats -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px;">
                    <div class="metric-card" style="border-left-color: #e74c3c;">
                        <div class="metric-label">🔴 Live Users</div>
                        <div class="metric-value" style="color: #e74c3c; font-size: 1.8em;">${this.data.real_time.active_users}</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #27ae60;">
                        <div class="metric-label">Page Views (Last Hour)</div>
                        <div class="metric-value" style="color: #27ae60;">${this.data.real_time.pageviews_last_hour}</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #9b59b6;">
                        <div class="metric-label">Performance Score</div>
                        <div class="metric-value" style="color: #9b59b6;">${this.data.performance.performance_score}/100</div>
                    </div>
                    <div class="metric-card" style="border-left-color: #f39c12;">
                        <div class="metric-label">Conversion Rate</div>
                        <div class="metric-value" style="color: #f39c12;">${(this.data.overview.conversion_rate * 100).toFixed(2)}%</div>
                    </div>
                </div>

                <!-- Overview Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px;">
                    <div class="metric-card">
                        <div class="metric-label">Total Page Views</div>
                        <div class="metric-value">${this.data.overview.total_pageviews.toLocaleString()}</div>
                        <small style="color: #27ae60;">${this.data.overview.growth.pageviews} from last period</small>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Unique Visitors</div>
                        <div class="metric-value">${this.data.overview.unique_visitors.toLocaleString()}</div>
                        <small style="color: #27ae60;">${this.data.overview.growth.visitors} from last period</small>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Bounce Rate</div>
                        <div class="metric-value">${(this.data.overview.bounce_rate * 100).toFixed(1)}%</div>
                        <small style="color: #27ae60;">${this.data.overview.growth.bounce_rate} from last period</small>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Avg. Session Duration</div>
                        <div class="metric-value">${this.data.overview.avg_session_duration}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Revenue</div>
                        <div class="metric-value">$${this.data.overview.revenue.toLocaleString()}</div>
                        <small style="color: #27ae60;">${this.data.overview.growth.revenue} from last period</small>
                    </div>
                </div>

                <div class="analytics-grid">
                    <!-- Daily Page Views Chart -->
                    <div class="analytics-card" style="grid-column: span 2;">
                        <div class="card-title">📈 Daily Page Views (Last 7 Days)</div>
                        <div class="chart-container">
                            ${this.data.page_views_daily.map(pv => `
                                <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
                                    <div class="chart-bar" style="height: ${(pv.views / maxViews) * 150}px;" title="${pv.date}: ${pv.views} views"></div>
                                    <div class="chart-label">${new Date(pv.date).toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</div>
                                    <small style="color: #666;">${pv.views}</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Hourly Traffic Pattern -->
                    <div class="analytics-card" style="grid-column: span 2;">
                        <div class="card-title">🕒 Hourly Traffic Pattern (Today)</div>
                        <div class="chart-container" style="height: 120px;">
                            ${this.data.page_views_hourly.map(pv => `
                                <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
                                    <div class="chart-bar" style="height: ${(pv.views / maxHourly) * 80}px; width: 12px;" title="${pv.hour}: ${pv.views} views"></div>
                                    <div style="font-size: 0.7em; color: #666; transform: rotate(-45deg); margin-top: 8px;">${pv.hour.split(':')[0]}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Traffic Sources -->
                    <div class="analytics-card">
                        <div class="card-title">🚀 Traffic Sources</div>
                        <ul class="source-list">
                            ${this.data.traffic_sources.map(source => `
                                <li class="source-item">
                                    <div>
                                        <strong>${source.source}</strong>
                                        <div class="source-bar" style="width: ${source.percentage * 2}px;"></div>
                                        <small style="color: #666;">${source.visitors.toLocaleString()} visitors</small>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-weight: bold;">${source.percentage.toFixed(1)}%</div>
                                        <small style="color: #27ae60;">${source.growth}</small><br>
                                        <small style="color: #666;">$${source.revenue.toLocaleString()}</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Conversion Funnel -->
                    <div class="analytics-card">
                        <div class="card-title">🎯 Conversion Funnel</div>
                        <div style="padding: 10px 0;">
                            ${this.data.conversion_funnel.map((stage, index) => `
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span style="font-weight: bold;">${stage.stage}</span>
                                        <span>${stage.conversion.toFixed(1)}%</span>
                                    </div>
                                    <div style="background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden;">
                                        <div style="background: linear-gradient(45deg, #3498db, #2ecc71); height: 100%;
                                                    width: ${stage.conversion}%; transition: width 0.5s ease;"></div>
                                    </div>
                                    <small style="color: #666;">${stage.count.toLocaleString()} users</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Top Pages -->
                    <div class="analytics-card">
                        <div class="card-title">📄 Top Pages</div>
                        <ul class="page-list">
                            ${this.data.top_pages.map(page => `
                                <li class="page-item">
                                    <div>
                                        <div class="page-path">${page.path}</div>
                                        <small style="color: #666;">${page.views.toLocaleString()} views • ${(page.bounce * 100).toFixed(1)}% bounce</small>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-weight: bold;">${page.unique.toLocaleString()}</div>
                                        <small style="color: #666;">unique</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Device Analytics -->
                    <div class="analytics-card">
                        <div class="card-title">💻 Device Breakdown</div>
                        <div style="padding: 10px 0;">
                            ${this.data.devices.map(device => `
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span>${device.type}</span>
                                        <span style="font-weight: bold;">${device.percentage.toFixed(1)}%</span>
                                    </div>
                                    <div style="background: #ecf0f1; height: 8px; border-radius: 4px;">
                                        <div style="background: #3498db; height: 100%; width: ${device.percentage}%; border-radius: 4px;"></div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                        <small style="color: #666;">${device.visitors.toLocaleString()} visitors</small>
                                        <small style="color: #666;">$${device.revenue.toLocaleString()}</small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Geographic Distribution -->
                    <div class="analytics-card">
                        <div class="card-title">🌍 Geographic Distribution</div>
                        <ul class="source-list">
                            ${this.data.geographic.slice(0, 6).map(country => `
                                <li class="source-item">
                                    <div>
                                        <strong>${country.country}</strong>
                                        <div class="source-bar" style="width: ${country.percentage * 3}px;"></div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-weight: bold;">${country.percentage.toFixed(1)}%</div>
                                        <small style="color: #666;">${country.visitors.toLocaleString()}</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Live Activity Feed -->
                    <div class="analytics-card" style="grid-column: span 2;">
                        <div class="card-title">⚡ Live Activity Feed</div>
                        <div style="max-height: 200px; overflow-y: auto;">
                            ${this.data.real_time.live_events.map(event => `
                                <div style="padding: 8px 0; border-bottom: 1px solid #eee; display: flex; justify-content: space-between;">
                                    <div>
                                        <strong>${event.event}</strong> - ${event.value}<br>
                                        <small style="color: #666;">${event.location}</small>
                                    </div>
                                    <small style="color: #999;">${event.time}</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Performance Metrics -->
                    <div class="analytics-card">
                        <div class="card-title">⚡ Performance Metrics</div>
                        <div style="padding: 10px 0;">
                            <div style="margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Page Load Time</span>
                                    <span style="font-weight: bold;">${this.data.performance.page_load_time}s</span>
                                </div>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>Server Response</span>
                                    <span style="font-weight: bold;">${this.data.performance.server_response_time}s</span>
                                </div>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>LCP</span>
                                    <span style="font-weight: bold;">${this.data.performance.largest_contentful_paint}s</span>
                                </div>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span>CLS</span>
                                    <span style="font-weight: bold;">${this.data.performance.cumulative_layout_shift}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Browser Stats -->
                    <div class="analytics-card">
                        <div class="card-title">🌐 Browser Distribution</div>
                        <ul class="source-list">
                            ${this.data.browsers.map(browser => `
                                <li class="source-item">
                                    <div>
                                        <strong>${browser.name}</strong>
                                        <div class="source-bar" style="width: ${browser.percentage * 2}px;"></div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-weight: bold;">${browser.percentage.toFixed(1)}%</div>
                                        <small style="color: #666;">${browser.visitors.toLocaleString()}</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
                                <div class="stat-label">Avg Session</div>
                            </div>
                        </div>
                    </div>

                    <!-- Page Views Chart -->
                    <div class="analytics-card">
                        <div class="card-title">📈 Page Views (7 days)</div>
                        <div class="chart-container">
                            ${this.data.page_views.map(pv => `
                                <div>
                                    <div class="chart-bar" style="height: ${(pv.views / maxViews) * 150}px"></div>
                                    <div class="chart-label">${pv.date.split('-')[2]}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Traffic Sources -->
                    <div class="analytics-card">
                        <div class="card-title">🌐 Traffic Sources</div>
                        <ul class="source-list">
                            ${this.data.traffic_sources.map(source => `
                                <li class="source-item">
                                    <div>
                                        <strong>${source.source}</strong>
                                        <div class="source-bar" style="width: ${source.percentage * 2}px"></div>
                                    </div>
                                    <div>
                                        <strong>${source.visitors}</strong>
                                        <small>(${source.percentage}%)</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Top Pages -->
                    <div class="analytics-card">
                        <div class="card-title">📄 Top Pages</div>
                        <ul class="page-list">
                            ${this.data.top_pages.map(page => `
                                <li class="page-item">
                                    <div>
                                        <div class="page-path">${page.page}</div>
                                        <small>Bounce: ${(page.bounce_rate * 100).toFixed(1)}%</small>
                                    </div>
                                    <div class="page-stats">
                                        <strong>${page.views.toLocaleString()}</strong><br>
                                        <small>views</small>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    </div>

                    <!-- Device Breakdown -->
                    <div class="analytics-card">
                        <div class="card-title">📱 Device Breakdown</div>
                        <div class="device-chart">
                            ${this.data.devices.map(device => `
                                <div class="device-bar">
                                    <div class="device-segment device-${device.device.toLowerCase()}"
                                         style="height: ${device.percentage * 2}px">
                                    </div>
                                    <div class="device-label">
                                        <strong>${device.device}</strong><br>
                                        ${device.percentage}%
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // Initialize when this component is loaded
    if (document.getElementById('analytics-content')) {
        new AnalyticsComponent();
    }
</script>
        """
        return web.Response(text=html, content_type="text/html")


class AnalyticsComponent(Component[GetAnalyticsData]):
    """Analytics component for data insights and reporting."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register analytics routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/analytics/data", view=AnalyticsAPIView))
                await ctx.process(RegisterView(route="/components/analytics", view=AnalyticsComponentView))

            self.registered = True
            print("Analytics component routes registered")

    async def handle(
        self, message: GetAnalyticsData, *, handler: Callable[[Message], Awaitable[None]], **_: Any
    ) -> None:
        """Handle analytics data requests."""
        # In a real application, this would query actual analytics data
        data = {
            "period": message.period,
            "total_pageviews": random.randint(40000, 50000),
            "unique_visitors": random.randint(3000, 4000),
            "generated_at": time.time(),
        }

        await handler(AnalyticsDataRetrieved(data=data))
