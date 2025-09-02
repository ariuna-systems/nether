# Component-based SPA with Nether Framework

This example demonstrates how to build a Single Page Application (SPA) with dynamic component discovery and registration using the Nether framework.

## Features

- **Dynamic Component Discovery**: Components are automatically discovered and registered
- **Component API Routes**: Each component exposes its own REST API endpoints
- **Web Components**: Components serve their own web interfaces/widgets
- **Manifest System**: JSON-based component metadata for discovery
- **SPA Frontend**: Main application dynamically loads and displays components
- **Menu System**: Navigation menu is automatically populated from component manifests

## Architecture

### Component Structure

Each component is self-contained and provides:

- **API Endpoints**: REST API for data operations (`/api/{component}/data`)
- **Web Interface**: HTML/CSS/JS widget (`/components/{component}`)
- **Manifest**: JSON metadata describing the component
- **Message Handlers**: Nether framework message processing

### Components Included

1. **Dashboard** (`/dashboard`)
   - System overview and metrics
   - Real-time data visualization
   - Performance indicators

2. **User Management** (`/users`)
   - User account management
   - Role-based permissions
   - User creation and editing

3. **Analytics** (`/analytics`)
   - Traffic analytics
   - Page view statistics
   - Device breakdown

4. **Settings** (`/settings`)
   - Application configuration
   - System preferences
   - Integration settings

## Running the Application

1. **Start the server**:

   ```bash
   cd examples/spa_components
   python main.py
   ```

2. **Access the application**:
   - Open your browser to `http://localhost:8085`
   - The SPA will automatically discover and load all components

3. **API Endpoints**:
   - Component manifests: `GET /api/components/manifests`
   - Dashboard data: `GET /api/dashboard/data`
   - User data: `GET /api/users/data`
   - Analytics data: `GET /api/analytics/data`
   - Settings data: `GET /api/settings/data`

## Adding New Components

To add a new component:

1. **Create component file** in `components/` directory:

   ```python
   from nether.component import Component
   from nether.server import RegisterView
   
   class MyComponent(Component[MyMessage]):
       async def on_start(self):
           # Register routes
           pass
       
       async def handle(self, message, *, handler, **_):
           # Handle messages
           pass
   ```

2. **Register in main.py**:

   ```python
   my_component = MyComponent(self)
   self.attach(my_component)
   self.component_registry.register_component("my_component", my_component, {
       "id": "my_component",
       "name": "My Component",
       "routes": {
           "api_base": "/api/my_component",
           "web_component": "/components/my_component"
       },
       "menu": {
           "title": "My Component",
           "order": 5,
           "route": "/my_component"
       }
   })
   ```

3. **Component automatically appears** in the SPA navigation and loads its interface.

## Key Concepts

### Component Registry

Manages component discovery and metadata:

```python
class ComponentRegistry:
    def register_component(self, component_id, component, manifest)
    def get_manifest(self, component_id)
    def get_all_manifests()
```

### Component Manifest

JSON metadata describing component capabilities:

```json
{
    "id": "dashboard",
    "name": "Dashboard",
    "description": "System overview and metrics",
    "routes": {
        "api_base": "/api/dashboard",
        "web_component": "/components/dashboard"
    },
    "menu": {
        "title": "Dashboard",
        "icon": "dashboard",
        "order": 1,
        "route": "/dashboard"
    },
    "permissions": ["read:dashboard"]
}
```

### Frontend Architecture

- **Component Discovery**: Fetches manifests on startup
- **Dynamic Loading**: Loads component HTML/CSS/JS on demand
- **Event System**: Components communicate via custom events
- **Navigation**: Menu automatically populated from manifests

## Extending the Framework

### Custom Message Types

Define domain-specific messages:

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class MyCustomCommand(Command):
    data: str
```

### Component Communication

Components can communicate via the mediator:

```python
async with self.application.mediator.context() as ctx:
    await ctx.process(MyCustomCommand(data="example"))
```

### Frontend Integration

Components can expose custom JavaScript APIs:

```javascript
window.addEventListener('component-my-component-loaded', (event) => {
    // Handle component-specific events
});
```

This architecture provides a scalable foundation for building modular applications where new components can be added without modifying the core application structure.
