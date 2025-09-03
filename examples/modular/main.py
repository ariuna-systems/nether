"""
Component-based SPA Application with Nether Framework - SECURE VERSION

This example demonstrates how to build a Single Page Application (SPA)
with dynamic component discovery and registration using the Nether framework.
NOW WITH ENHANCED SECURITY for external component loading.

Features:
- Secure dynamic component discovery and registration
- Component validation and security scoring
- ES6 module-based component architecture
- Each component exposes its own API routes
- Components serve their own web interfaces
- Main SPA frontend that discovers and loads components securely
- Component manifest system (JSON metadata) with validation
- Menu system that dynamically adds component sections
- Content Security Policy (CSP) enforcement
- Component sandboxing and validation

Architecture:
- Components are self-contained ES6 modules with API + UI
- Each component provides a manifest (JSON) with metadata and security info
- Server validates all components before allowing registration
- SPA frontend uses secure loader to import validated modules only
- Components can be added/removed without modifying main app
- All external content is validated and sandboxed
"""

import argparse
import asyncio
import json
import time
from typing import Any

from aiohttp import web

import nether
from components.analytics import AnalyticsComponent
from components.dashboard import DashboardComponent
from components.settings import SettingsComponent
from nether.component import Component
from nether.server import RegisterView, Server, ViewRegistered


class ComponentRegistry:
    """Registry manages dynamic component discovery and lifecycle."""

    def __init__(self):
        self.components: dict[str, Component] = {}
        self.manifests: dict[str, dict[str, Any]] = {}
        self.sse_clients: set = set()  # Store SSE clients for live updates
        self.background_tasks: set = set()  # Store background tasks

    def add_sse_client(self, response):
        """Add a new SSE client for component updates."""
        self.sse_clients.add(response)

    def remove_sse_client(self, response):
        """Remove an SSE client."""
        self.sse_clients.discard(response)

    async def notify_component_registered(self, component_id: str, manifest: dict[str, Any]):
        """Notify all SSE clients about a new component registration."""
        message = f"data: {json.dumps({'type': 'component_registered', 'id': component_id, 'manifest': manifest})}\n\n"

        # Send to all connected SSE clients
        disconnected_clients = set()
        for client in self.sse_clients:
            try:
                await client.write(message.encode())
            except Exception:
                # Client disconnected, mark for removal
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.sse_clients.discard(client)

    def register_component(self, component_id: str, component: Component, manifest: dict[str, Any]):
        """Register a component with its manifest."""
        self.components[component_id] = component
        self.manifests[component_id] = manifest

        # Trigger SSE notification for real-time menu updates
        task = asyncio.create_task(self.notify_component_registered(component_id, manifest))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    def get_manifest(self, component_id: str) -> dict[str, Any] | None:
        """Get component manifest by ID."""
        return self.manifests.get(component_id)

    def get_manifests(self) -> dict[str, dict[str, Any]]:
        """Get all component manifests."""
        return self.manifests.copy()

    def get_component(self, component_id: str) -> Component | None:
        """Get component instance by ID."""
        return self.components.get(component_id)

    def get_components(self) -> dict:
        return self.components.copy()


class SystemView(web.View):
    """Main system view that serves the SPA frontend."""

    async def get(self) -> web.Response:
        """Serve the main SPA HTML page."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Component-Based SPA with Secure Loading</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }

        .app-container { display: flex; height: 100vh; }
        .sidebar { width: 250px; background: #2c3e50; color: white; padding: 20px; }
        .main-content { flex: 1; padding: 20px; background: #ecf0f1; }

        .logo { font-size: 20px; font-weight: bold; margin-bottom: 30px; }
        .nav-menu { list-style: none; }
        .nav-item { margin-bottom: 10px; }
        .nav-link {
            display: block; padding: 10px 15px; color: white;
            text-decoration: none; border-radius: 5px; transition: background 0.3s;
        }
        .nav-link:hover, .nav-link.active { background: #34495e; }

        .component-container { display: none; }
        .component-container.active { display: block; }

        .loading { text-align: center; padding: 40px; color: #7f8c8d; }
        .error { color: #e74c3c; padding: 20px; background: #f8f9fa; border-radius: 5px; border: 1px solid #e74c3c; }

        .component-header { border-bottom: 2px solid #3498db; margin-bottom: 20px; padding-bottom: 10px; }
        .component-title { color: #2c3e50; font-size: 24px; }
        .component-description { color: #7f8c8d; margin-top: 5px; }
    </style>

    <!-- Load the secure component loader -->
    <script type="module" src="/js/secure-component-loader.js"></script>
</head>
<body>
    <div class="app-container">
        <nav class="sidebar">
            <div class="logo">Component SPA</div>
            <ul class="nav-menu" id="nav-menu">
                <li class="nav-item">
                    <a href="#" class="nav-link active" data-route="home">🏠 Home</a>
                </li>
            </ul>
        </nav>

        <main class="main-content">
            <div id="home-container" class="component-container active">
                <div class="component-header">
                    <h1 class="component-title">Welcome to Component-based SPA</h1>
                    <p class="component-description">Dynamic component discovery and loading</p>
                </div>
                <div id="components-overview"></div>
            </div>

            <div id="dynamic-components"></div>
        </main>
    </div>

    <script>
        class ComponentSPA {
            constructor() {
                this.components = new Map();
                this.currentRoute = 'home';
                this.init();
            }

            async init() {
                await this.loadComponents();
                this.setupNavigation();
                this.setupSSE();  // Set up real-time component updates
                this.showComponentsOverview();
            }

            async loadComponents() {
                try {
                    console.log('Loading components...');
                    const response = await fetch('/api/components/manifests');
                    const manifests = await response.json();

                    console.log('Manifests received:', manifests);

                    for (const [id, manifest] of Object.entries(manifests)) {
                        console.log(`Adding component: ${manifest.id}`, manifest);
                        this.components.set(manifest.id, manifest);
                        this.addToMenu(manifest);
                        await this.loadComponentUI(manifest);
                    }

                    console.log('Final components Map:', this.components);
                    console.log('Components Map size:', this.components.size);
                } catch (error) {
                    console.error('Failed to load components:', error);
                }
            }

            addToMenu(manifest) {
                const navMenu = document.getElementById('nav-menu');
                const menuItem = document.createElement('li');
                menuItem.className = 'nav-item';

                // Use icon from manifest or default
                const icon = manifest.menu?.icon || 'component';
                const iconMap = {
                    'dashboard': '📊',
                    'analytics': '📈',
                    'settings': '⚙️',
                    'component': '🔧'
                };

                menuItem.innerHTML = `
                    <a href="#" class="nav-link" data-route="${manifest.id}">
                        ${iconMap[icon] || iconMap.component} ${manifest.menu?.title || manifest.name}
                    </a>
                `;
                navMenu.appendChild(menuItem);
            }

            async loadComponentUI(manifest) {
                try {
                    console.log(`Loading component ${manifest.id}...`);

                    // Create container for the component
                    const container = document.createElement('div');
                    container.id = `${manifest.id}-container`;
                    container.className = 'component-container';

                    // Try to load component content from its API
                    let componentContent = '';

                    try {
                        // First try to get component's HTML content
                        const htmlResponse = await fetch(`${manifest.routes?.web_component || '/components/' + manifest.id}`);
                        if (htmlResponse.ok) {
                            componentContent = await htmlResponse.text();
                        } else {
                            throw new Error('Component HTML not found');
                        }
                    } catch (error) {
                        // Fallback: Create a basic component interface
                        componentContent = this.createBasicComponentUI(manifest);
                    }

                    container.innerHTML = componentContent;
                    document.getElementById('dynamic-components').appendChild(container);

                    // Initialize component if it has initialization code
                    if (window[`init${manifest.id.charAt(0).toUpperCase() + manifest.id.slice(1)}Component`]) {
                        window[`init${manifest.id.charAt(0).toUpperCase() + manifest.id.slice(1)}Component`](container);
                    }

                    console.log(`Component ${manifest.id} loaded successfully`);

                } catch (error) {
                    console.error(`Failed to load component ${manifest.id}:`, error);

                    // Error fallback
                    const container = document.createElement('div');
                    container.id = `${manifest.id}-container`;
                    container.className = 'component-container';
                    container.innerHTML = this.createErrorComponentUI(manifest, error);
                    document.getElementById('dynamic-components').appendChild(container);
                }
            }

            createBasicComponentUI(manifest) {
                return `
                    <div class="component-header">
                        <h1 class="component-title">${manifest.name}</h1>
                        <p class="component-description">${manifest.description}</p>
                    </div>
                    <div class="component-content">
                        <div class="component-info">
                            <h3>Component Information</h3>
                            <ul>
                                <li><strong>Version:</strong> ${manifest.version}</li>
                                <li><strong>Author:</strong> ${manifest.author || 'System'}</li>
                                <li><strong>Permissions:</strong> ${manifest.permissions?.join(', ') || 'None'}</li>
                            </ul>
                        </div>

                        ${manifest.api_endpoints ? `
                        <div class="api-section">
                            <h3>API Endpoints</h3>
                            <ul class="api-list">
                                ${manifest.api_endpoints.map(endpoint => `
                                    <li>
                                        <code>GET ${endpoint}</code>
                                        <button onclick="testEndpoint('${endpoint}')" class="test-btn">Test</button>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        <div class="component-data" id="${manifest.id}-data">
                            <h3>Component Data</h3>
                            <div class="loading">Loading component data...</div>
                        </div>
                    </div>

                    <style>
                        .component-info ul { margin: 10px 0; padding-left: 20px; }
                        .api-section { margin: 20px 0; }
                        .api-list { list-style: none; padding: 0; }
                        .api-list li {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            padding: 8px;
                            margin: 5px 0;
                            background: #f8f9fa;
                            border-radius: 4px;
                        }
                        .test-btn {
                            padding: 4px 8px;
                            background: #007bff;
                            color: white;
                            border: none;
                            border-radius: 3px;
                            cursor: pointer;
                        }
                        .test-btn:hover { background: #0056b3; }
                        .component-data {
                            margin: 20px 0;
                            padding: 15px;
                            background: #f8f9fa;
                            border-radius: 5px;
                        }
                    </style>
                `;
            }

            createErrorComponentUI(manifest, error) {
                return `
                    <div class="component-header">
                        <h1 class="component-title">${manifest.name}</h1>
                        <p class="component-description">Component failed to load</p>
                    </div>
                    <div class="error">
                        <h3>Loading Error</h3>
                        <p>Failed to load component "${manifest.id}": ${error.message}</p>
                        <p>The component may not have a custom UI implementation.</p>
                        <button onclick="location.reload()" class="retry-btn">Retry</button>
                    </div>

                    <style>
                        .retry-btn {
                            padding: 8px 16px;
                            background: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            margin-top: 10px;
                        }
                        .retry-btn:hover { background: #218838; }
                    </style>
                `;
            }

            setupNavigation() {
                document.getElementById('nav-menu').addEventListener('click', (e) => {
                    if (e.target.classList.contains('nav-link')) {
                        e.preventDefault();
                        const route = e.target.dataset.route;
                        this.navigateTo(route);
                    }
                });
            }

            setupSSE() {
                // Set up Server-Sent Events for real-time component updates
                const eventSource = new EventSource('/api/components/events');

                eventSource.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);

                        if (data.type === 'component_registered') {
                            console.log('New component registered:', data.id);

                            // Add to components map
                            this.components.set(data.id, data.manifest);

                            // Add to menu automatically
                            this.addToMenu(data.manifest);

                            // Load component UI
                            this.loadComponentUI(data.manifest);

                            // Show notification
                            this.showNotification(`New component "${data.manifest.name}" added!`);
                        }
                    } catch (error) {
                        console.error('Error processing SSE message:', error);
                    }
                };

                eventSource.onerror = (error) => {
                    console.error('SSE connection error:', error);
                };

                console.log('SSE connection established for real-time component updates');
            }

            showNotification(message) {
                // Simple notification system
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed; top: 20px; right: 20px; background: #4CAF50;
                    color: white; padding: 12px 20px; border-radius: 4px; z-index: 1000;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 14px;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);

                // Auto-remove after 3 seconds
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 3000);
            }

            navigateTo(route) {
                console.log(`Navigating to route: ${route}`);

                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                document.querySelector(`[data-route="${route}"]`).classList.add('active');

                // Show/hide components
                document.querySelectorAll('.component-container').forEach(container => {
                    container.classList.remove('active');
                });

                const targetContainer = document.getElementById(`${route}-container`);
                console.log(`Target container for ${route}:`, targetContainer);

                if (targetContainer) {
                    targetContainer.classList.add('active');
                    this.currentRoute = route;

                    // Load component data when navigating to it
                    console.log(`Triggering data load for route: ${route}`);
                    this.loadComponentData(route);

                    console.log(`Navigated to ${route}`);
                }
            }

            async loadComponentData(componentId) {
                console.log(`Loading data for component: ${componentId}`);
                console.log(`Available components in Map:`, Array.from(this.components.keys()));
                console.log(`Components Map size:`, this.components.size);

                const component = this.components.get(componentId);
                console.log(`Component found:`, component);

                if (!component || !component.api_endpoints) {
                    console.log(`No component or api_endpoints found for ${componentId}`);
                    return;
                }

                const dataContainer = document.getElementById(`${componentId}-data`);
                console.log(`Data container found:`, dataContainer);

                if (!dataContainer) {
                    console.log(`No data container found for ${componentId}-data`);
                    return;
                }

                try {
                    // Try to load data from the first API endpoint
                    const endpoint = component.api_endpoints[0];
                    console.log(`Fetching from endpoint: ${endpoint}`);

                    const response = await fetch(endpoint);
                    console.log(`Response status: ${response.status}`);

                    if (response.ok) {
                        const data = await response.json();
                        console.log(`Data loaded successfully:`, data);

                        dataContainer.innerHTML = `
                            <h3>Component Data</h3>
                            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">
${JSON.stringify(data, null, 2)}
                            </pre>
                        `;
                    } else {
                        throw new Error(`HTTP ${response.status}`);
                    }
                } catch (error) {
                    console.error(`Error loading data for ${componentId}:`, error);

                    dataContainer.innerHTML = `
                        <h3>Component Data</h3>
                        <div class="error">
                            <p>Failed to load data: ${error.message}</p>
                            <button onclick="app.loadComponentData('${componentId}')" class="retry-btn">Retry</button>
                        </div>
                    `;
                }
            }

            showComponentsOverview() {
                const overview = document.getElementById('components-overview');
                const componentsArray = Array.from(this.components.values());

                overview.innerHTML = `
                    <h3>System Overview</h3>
                    <p>Discovered ${componentsArray.length} components:</p>
                    <ul style="margin: 20px 0; padding-left: 20px;">
                        ${componentsArray.map(c => `
                            <li style="margin: 10px 0;">
                                <strong>${c.name}</strong> (v${c.version})
                                <br><small style="color: #7f8c8d;">${c.description}</small>
                            </li>
                        `).join('')}
                    </ul>
                    <p>Use the navigation menu to explore each component.</p>
                `;
            }
        }

        // Global utility functions for component interaction
        window.testEndpoint = async function(endpoint) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();

                // Show result in a modal-like overlay
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); display: flex; align-items: center;
                    justify-content: center; z-index: 1000;
                `;

                overlay.innerHTML = `
                    <div style="background: white; padding: 20px; border-radius: 8px; max-width: 600px; max-height: 80vh; overflow: auto;">
                        <h3>API Response: ${endpoint}</h3>
                        <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;">
${JSON.stringify(data, null, 2)}
                        </pre>
                        <button onclick="this.parentElement.parentElement.remove()"
                                style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Close
                        </button>
                    </div>
                `;

                document.body.appendChild(overlay);

                // Close on click outside
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) overlay.remove();
                });

            } catch (error) {
                alert(`Failed to test endpoint ${endpoint}: ${error.message}`);
            }
        };

        // Global reference to the app instance
        let app;

        // Initialize the SPA when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            app = new ComponentSPA();

            // Make app instance globally accessible for components
            window.app = app;
        });
    </script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type="text/html")


class ComponentManifestView(web.View):
    """API endpoint that returns all component manifests."""

    async def get(self) -> web.Response:
        """Return all component manifests as JSON."""
        try:
            app: System = self.request.app["nether_app"]
            manifests = app.component_registry.get_manifests()
            return web.json_response(manifests)
        except KeyError:
            return web.json_response({"error": "Application not properly initialized"}, status=500)
        except Exception as e:
            return web.json_response({"error": f"Failed to retrieve manifests: {e!s}"}, status=500)


class APIDiscoveryView(web.View):
    """API endpoint that returns all discovered HTTP endpoints and routes."""

    async def get(self) -> web.Response:
        """Return all registered API endpoints and routes."""
        try:
            app: System = self.request.app["nether_app"]

            # Get all registered routes from the HTTP server
            registered_routes = []

            # Find the server component to access HTTP routes
            server_component = None
            for component in app.mediator.components:
                if hasattr(component, "_http_server"):
                    server_component = component
                    break

            if server_component and hasattr(server_component, "_http_server"):
                # Extract routes from aiohttp router
                for resource in server_component._http_server.router.resources():
                    route_info = {
                        "path": getattr(resource, "_path", str(resource)),
                        "name": getattr(resource, "_name", None),
                        "methods": [],
                    }

                    # Get HTTP methods for this route
                    for route in resource:
                        if hasattr(route, "method"):
                            route_info["methods"].append(route.method)

                    registered_routes.append(route_info)

            # Get component-specific API endpoints
            component_endpoints = []
            for component_id, manifest in app.component_registry.get_manifests().items():
                if "api_endpoints" in manifest:
                    for endpoint in manifest["api_endpoints"]:
                        component_endpoints.append(
                            {
                                "component": component_id,
                                "endpoint": endpoint,
                                "component_name": manifest.get("name", component_id),
                                "description": manifest.get("description", ""),
                                "permissions": manifest.get("permissions", []),
                            }
                        )

            # System information
            host = getattr(app.configuration, "host", "localhost")
            port = getattr(app.configuration, "port", 8080)
            base_url = f"http://{host}:{port}"

            discovery_info = {
                "service_info": {
                    "name": "Component-based SPA System",
                    "version": "1.0.0",
                    "base_url": base_url,
                    "timestamp": app.start_time,
                },
                "system_routes": [
                    {"path": "/", "method": "GET", "description": "Main SPA application", "type": "ui"},
                    {"path": "/api/discovery", "method": "GET", "description": "API endpoint discovery", "type": "api"},
                    {
                        "path": "/api/components/manifests",
                        "method": "GET",
                        "description": "Component manifests",
                        "type": "api",
                    },
                    {
                        "path": "/api/components",
                        "method": "GET",
                        "description": "Secure component registry",
                        "type": "api",
                    },
                    {
                        "path": "/api/components/validate",
                        "method": "GET",
                        "description": "Component validation",
                        "type": "api",
                    },
                ],
                "registered_routes": registered_routes,
                "component_endpoints": component_endpoints,
                "components": list(app.component_registry.get_manifests().keys()),
            }

            return web.json_response(discovery_info)

        except Exception as e:
            return web.json_response({"error": f"Failed to discover endpoints: {e!s}"}, status=500)


class ComponentSSEView(web.View):
    """Server-Sent Events endpoint for real-time component updates."""

    async def get(self) -> web.StreamResponse:
        """Handle SSE connection for component updates."""
        response = web.StreamResponse()
        response.headers["Content-Type"] = "text/event-stream"
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        response.headers["Access-Control-Allow-Origin"] = "*"

        await response.prepare(self.request)

        # Get the app instance from request
        app = self.request.app.get("nether_app")
        if app and hasattr(app, "component_registry"):
            # Add this SSE client to the registry
            app.component_registry.add_sse_client(response)

            # Send initial connection message
            initial_message = f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established'})}\n\n"
            await response.write(initial_message.encode())

            try:
                # Keep connection alive until client disconnects
                while True:
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    heartbeat = f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                    await response.write(heartbeat.encode())
            except Exception:
                # Client disconnected or other error
                pass
            finally:
                # Remove client from registry when disconnected
                if app and hasattr(app, "component_registry"):
                    app.component_registry.remove_sse_client(response)

        return response


class ComponentManager(Component[RegisterView | ViewRegistered]):
    """Component to register SPA views and routes."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Get server component to access the HTTP app
            server = None
            for component in self.application.mediator.components:
                if hasattr(component, "_http_server"):
                    server = component
                    break

            if server:
                # Store system reference in the HTTP app for views
                server._http_server["nether_app"] = self.application  # Store the actual System instance

            # Register main SPA view
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/", view=SystemView))
                await ctx.process(RegisterView(route="/api/components/manifests", view=ComponentManifestView))
                await ctx.process(RegisterView(route="/api/discovery", view=APIDiscoveryView))
                await ctx.process(RegisterView(route="/api/components/events", view=ComponentSSEView))

            self.registered = True
            print("SPA routes registered")

    async def handle(self, message: RegisterView | ViewRegistered, *, handler, **_) -> None:
        if isinstance(message, ViewRegistered):
            # Handle successful view registration confirmation
            pass
        elif isinstance(message, RegisterView):
            # Handle view registration requests (if needed)
            pass


class System(nether.Nether):
    """Main SPA application that manages component discovery and registration."""

    def __init__(self, configuration):
        super().__init__(configuration=configuration)
        self.start_time = time.time()
        self.component_registry = ComponentRegistry()

    async def register_components(self):
        """Register all available components with the system."""

        # Dashboard Component
        dashboard = DashboardComponent(self)
        self.attach(dashboard)
        self.component_registry.register_component(
            "dashboard",
            dashboard,
            {
                "id": "dashboard",
                "name": "Dashboard",
                "description": "System overview and metrics dashboard",
                "version": "1.0.0",
                "routes": {"api_base": "/api/dashboard", "web_component": "/components/dashboard"},
                "menu": {"title": "Dashboard", "icon": "dashboard", "order": 1, "route": "/dashboard"},
                "permissions": ["read:dashboard"],
                "api_endpoints": ["/api/dashboard/data"],
            },
        )

        # Analytics Component
        analytics = AnalyticsComponent(self)
        self.attach(analytics)
        self.component_registry.register_component(
            "analytics",
            analytics,
            {
                "id": "analytics",
                "name": "Analytics",
                "description": "Data analytics and reporting",
                "version": "1.0.0",
                "author": "system",
                "tag_name": "analytics-component",
                "class_name": "AnalyticsWebComponent",
                "routes": {
                    "api_base": "/api/analytics",
                    "web_component": "/components/analytics",
                    "module": "/modules/analytics.js",
                },
                "menu": {"title": "Analytics", "icon": "analytics", "order": 3, "route": "/analytics"},
                "permissions": ["read:analytics"],
                "api_endpoints": ["/api/analytics/data"],
            },
        )

        # Settings Component
        settings = SettingsComponent(self)
        self.attach(settings)
        self.component_registry.register_component(
            "settings",
            settings,
            {
                "id": "settings",
                "name": "Settings",
                "description": "Application configuration and settings",
                "version": "1.0.0",
                "author": "system",
                "tag_name": "settings-component",
                "class_name": "SettingsWebComponent",
                "routes": {
                    "api_base": "/api/settings",
                    "web_component": "/components/settings",
                    "module": "/modules/settings.js",
                },
                "menu": {"title": "Settings", "icon": "settings", "order": 4, "route": "/settings"},
                "permissions": ["read:settings", "write:settings"],
                "api_endpoints": ["/api/settings/data", "/api/settings/update"],
            },
        )

    async def sync_components_to_secure_registry(self) -> None:
        """Sync components from the regular registry to the secure registry."""
        if not hasattr(self, "secure_registry"):
            return

        from nether.component.validator import ComponentManifest

        for component_id, manifest in self.component_registry.get_manifests().items():
            try:
                # Create a ComponentManifest for the secure registry
                secure_manifest = ComponentManifest(
                    id=component_id,
                    name=manifest.get("name", component_id),
                    version=manifest.get("version", "1.0.0"),
                    description=manifest.get("description", ""),
                    author=manifest.get("author", "system"),
                    tag_name=manifest.get("tag_name", f"{component_id}-component"),
                    module_url=f"/modules/{component_id}.js",
                    permissions=manifest.get("permissions", []),
                    api_endpoints=manifest.get("api_endpoints", []),
                )

                # Directly add to the secure registry's registered_components
                # This bypasses validation since these are internal components
                self.secure_registry.registered_components[component_id] = secure_manifest
                print(f"✓ Synced {component_id} to secure registry")

            except Exception as e:
                print(f"⚠️ Failed to sync {component_id} to secure registry: {e}")

    async def setup_secure_infrastructure(self) -> None:
        """Set up the secure component infrastructure."""
        # Import here to avoid circular imports
        from nether.component.loader import SecureComponentLoaderView
        from nether.component.registry import ComponentRegistryView, SecureComponentRegistry, ValidatedModuleView
        from nether.component.validator import ComponentValidationView

        secure_registry = SecureComponentRegistry()
        self.app["component_registry"] = secure_registry
        # Store reference to secure registry for later use
        self.secure_registry = secure_registry

        # Also set it on the HTTP server's app if available
        for component in self.mediator.components:
            if hasattr(component, "_http_server"):
                component._http_server["component_registry"] = secure_registry
                break

        await secure_registry.load_components_from_disk()

        async with self.mediator.context() as ctx:
            await ctx.process(RegisterView(route="/api/components/validate", view=ComponentValidationView))
            await ctx.process(RegisterView(route="/api/components", view=ComponentRegistryView))
            await ctx.process(RegisterView(route="/api/components/{component_id}", view=ComponentRegistryView))

            await ctx.process(RegisterView(route="/validated_modules/{module_name}", view=ValidatedModuleView))

            await ctx.process(RegisterView(route="/js/secure-component-loader.js", view=SecureComponentLoaderView))

            print("🛡️ Secure component infrastructure initialized")

    async def main(self) -> None:
        """Main application setup."""
        await self.setup_secure_infrastructure()
        await self.register_components()
        await self.sync_components_to_secure_registry()

        host = getattr(self.configuration, "host", "localhost")
        port = getattr(self.configuration, "port", 8080)

        print("Secure Component SPA Application started")
        print(f"Dashboard: http://{host}:{port}/")
        print(f"API Discovery: http://{host}:{port}/api/discovery")
        print(f"Component Registry: http://{host}:{port}/api/components")
        print(f"Validator: http://{host}:{port}/api/components/validate")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Component-based SPA with Nether Framework")
    parser.add_argument("--port", type=int, default=8081, help="Server port (default: 8081)")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="ERROR",
        help="Set the logging level (default: ERROR)",
    )

    args = parser.parse_args()

    app = System(configuration=args)

    server = Server(app, configuration=args)
    app.attach(server)

    spa_registration = ComponentManager(app)
    app.attach(spa_registration)

    print("Starting Component-based SPA Application")
    print("Registering components...")
    await app.register_components()
    print("Component registration complete")

    print("Registering SPA routes...")
    await spa_registration.on_start()
    print("SPA routes registration complete")

    from nether.server import StartServer

    async with app.mediator.context() as ctx:
        await ctx.process(StartServer(host=args.host, port=args.port))

    await app.start()


if __name__ == "__main__":
    try:
        nether.execute(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
