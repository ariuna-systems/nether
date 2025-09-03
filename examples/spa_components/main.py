"""
Component-based SPA Application with Nether Framework - SECURE VERSION

This         # Dashboard Component
        dashboard = DashboardComponent(self)
        self.attach(dashboard)
        self.component_registry.register_component(
            "dashboard",
            dashboard,
            {
                "id": "dashboard",
                "name": "Dashboard",
                "description": "System overview and real-time metrics",
                "version": "1.0.0",
                "author": "system",
                "tag_name": "dashboard-component",
                "class_name": "DashboardWebComponent",
                "routes": {"api_base": "/api/dashboard", "web_component": "/components/dashboard", "module": "/modules/dashboard.js"},
                "menu": {"title": "Dashboard", "icon": "dashboard", "order": 1, "route": "/dashboard"},
                "permissions": ["read:dashboard"],
                "api_endpoints": ["/api/dashboard/data"]
            },
        )ates how to build a Single Page Application (SPA)
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
import time
from pathlib import Path
from typing import Any

from aiohttp import web
from components.analytics import AnalyticsComponent

# Import our components
from components.dashboard import DashboardComponent
from components.settings import SettingsComponent

import nether
from nether.component import Component
from nether.server import RegisterView, Server, ViewRegistered


class ComponentRegistry:
    """Registry for managing dynamic component discovery and lifecycle."""

    def __init__(self):
        self.components: dict[str, Component] = {}
        self.manifests: dict[str, dict[str, Any]] = {}

    def register_component(self, component_id: str, component: Component, manifest: dict[str, Any]):
        """Register a component with its manifest."""
        self.components[component_id] = component
        self.manifests[component_id] = manifest

    def get_manifest(self, component_id: str) -> dict[str, Any] | None:
        """Get component manifest by ID."""
        return self.manifests.get(component_id)

    def get_all_manifests(self) -> dict[str, dict[str, Any]]:
        """Get all component manifests."""
        return self.manifests.copy()

    def get_component(self, component_id: str) -> Component | None:
        """Get component instance by ID."""
        return self.components.get(component_id)


class MainApplication(nether.Nether):
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
                "routes": {"api_base": "/api/analytics", "web_component": "/components/analytics", "module": "/modules/analytics.js"},
                "menu": {"title": "Analytics", "icon": "analytics", "order": 3, "route": "/analytics"},
                "permissions": ["read:analytics"],
                "api_endpoints": ["/api/analytics/data"]
            },
        )        # Settings Component
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
                "routes": {"api_base": "/api/settings", "web_component": "/components/settings", "module": "/modules/settings.js"},
                "menu": {"title": "Settings", "icon": "settings", "order": 4, "route": "/settings"},
                "permissions": ["read:settings", "write:settings"],
                "api_endpoints": ["/api/settings/data", "/api/settings/update"]
            },
        )

    async def setup_secure_infrastructure(self) -> None:
        """Set up the secure component infrastructure."""
        # Import here to avoid circular imports
        from nether.component.registry import SecureComponentRegistry, ComponentRegistryView, ValidatedModuleView
        from nether.component.validator import ComponentValidationView
        from nether.component.loader import SecureComponentLoaderView

        # Create secure component registry
        secure_registry = SecureComponentRegistry()
        self.app['component_registry'] = secure_registry

        # Load any existing components from disk
        await secure_registry.load_components_from_disk()

        # Register secure component routes
        async with self.mediator.context() as ctx:
            # Component validation endpoint
            await ctx.process(RegisterView(route="/api/components/validate", view=ComponentValidationView))

            # Component registry endpoints
            await ctx.process(RegisterView(route="/api/components/registry", view=ComponentRegistryView))
            await ctx.process(RegisterView(route="/api/components/registry/{component_id}", view=ComponentRegistryView))

            # Validated module serving
            await ctx.process(RegisterView(route="/validated_modules/{module_name}", view=ValidatedModuleView))

            # Secure component loader
            await ctx.process(RegisterView(route="/js/secure-component-loader.js", view=SecureComponentLoaderView))

            print("🛡️ Secure component infrastructure initialized")

    async def main(self) -> None:
        """Main application setup."""
        # Set up secure component infrastructure first
        await self.setup_secure_infrastructure()

        # Set up components
        await self.setup_components()

        # Register static file serving
        await self.register_static_routes()

        print("🚀 Secure Component SPA Application started")
        print("📊 Dashboard: http://localhost:8080/")
        print("🛡️ Component Registry: http://localhost:8080/api/components/registry")
        print("🔒 Validator: http://localhost:8080/api/components/validate")


class SPAView(web.View):
    """Main SPA view that serves the frontend application."""

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
                this.showComponentsOverview();
            }

            async loadComponents() {
                try {
                    const response = await fetch('/api/components/manifests');
                    const manifests = await response.json();

                    for (const [id, manifest] of Object.entries(manifests)) {
                        this.components.set(id, manifest);
                        this.addToMenu(manifest);
                        await this.loadComponentUI(manifest);
                    }
                } catch (error) {
                    console.error('Failed to load components:', error);
                }
            }

            addToMenu(manifest) {
                const navMenu = document.getElementById('nav-menu');
                const menuItem = document.createElement('li');
                menuItem.className = 'nav-item';
                menuItem.innerHTML = `
                    <a href="#" class="nav-link" data-route="${manifest.id}">
                        ${manifest.menu.icon ? '🔧' : '•'} ${manifest.menu.title}
                    </a>
                `;
                navMenu.appendChild(menuItem);
            }

            async loadComponentUI(manifest) {
                try {
                    console.log(`� Loading secure component for ${manifest.id}...`);

                    // Use the secure component loader
                    const success = await window.loadSecureComponent(manifest.id, manifest);

                    if (success) {
                        // Create container for the component
                        const container = document.createElement('div');
                        container.id = `${manifest.id}-container`;
                        container.className = 'component-container';

                        // Create the secure component instance
                        const componentElement = window.createSecureComponent(manifest.id, {
                            'api-endpoint': manifest.routes.api_base + '/data'
                        });

                        if (componentElement) {
                            container.appendChild(componentElement);
                            document.getElementById('dynamic-components').appendChild(container);
                            console.log(`✅ Secure component ${manifest.id} loaded and ready`);
                        } else {
                            throw new Error('Failed to create component instance');
                        }
                    } else {
                        throw new Error('Component loading failed security validation');
                    }

                } catch (error) {
                    console.error(`❌ Failed to load secure component ${manifest.id}:`, error);

                    // Fallback to showing an error message
                    const container = document.createElement('div');
                    container.id = `${manifest.id}-container`;
                    container.className = 'component-container';
                    container.innerHTML = `
                        <div class="error">
                            <h3>Component Loading Failed</h3>
                            <p>Failed to load component "${manifest.id}": ${error.message}</p>
                            <p>Please ensure the component is properly registered and validated.</p>
                        </div>
                    `;
                    document.getElementById('dynamic-components').appendChild(container);
                }
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

            navigateTo(route) {
                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                document.querySelector(`[data-route="${route}"]`).classList.add('active');

                // Show/hide components - web components handle their own data loading
                document.querySelectorAll('.component-container').forEach(container => {
                    container.classList.remove('active');
                });

                const targetContainer = document.getElementById(`${route}-container`);
                if (targetContainer) {
                    targetContainer.classList.add('active');
                    this.currentRoute = route;

                    console.log(`✅ Navigated to ${route} - web component will handle its own data loading`);
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

        // Initialize the SPA when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            new ComponentSPA();
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
        app: MainApplication = self.request.app["system"]
        manifests = app.component_registry.get_all_manifests()
        return web.json_response(manifests)


class SPARegistrationComponent(Component[RegisterView | ViewRegistered]):
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
                server._http_server["system"] = self.application

            # Register main SPA view
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/", view=SPAView))
                await ctx.process(RegisterView(route="/api/components/manifests", view=ComponentManifestView))

            self.registered = True
            print("SPA routes registered")

    async def handle(self, message: RegisterView | ViewRegistered, *, handler, **_) -> None:
        if isinstance(message, ViewRegistered):
            # Handle successful view registration confirmation
            pass
        elif isinstance(message, RegisterView):
            # Handle view registration requests (if needed)
            pass


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Component-based SPA with Nether Framework")
    parser.add_argument("--port", type=int, default=8081, help="Server port (default: 8087)")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    args = parser.parse_args()

    app = MainApplication(configuration=args)

    server = Server(app, configuration=args)
    app.attach(server)

    spa_registration = SPARegistrationComponent(app)
    app.attach(spa_registration)

    print("Starting Component-based SPA Application")
    print("Registering components...")
    await app.register_components()
    print("✅ Component registration complete")

    from nether.server import StartServer

    async with app.mediator.context() as ctx:
        await ctx.process(StartServer(host=args.host, port=args.port))

    await app.start()


if __name__ == "__main__":
    try:
        nether.execute(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
