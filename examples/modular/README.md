# Secure Component-based SPA with Nether Framework

A production-ready Single Page Application demonstrating secure dynamic component discovery and registration using the Nether framework.

## Features

### Security-First Architecture

- Component validation and security scoring
- Content Security Policy (CSP) enforcement  
- Component sandboxing and validation
- Secure ES6 module loading

### Dynamic Component System

- Automatic component discovery and registration
- Self-contained components with API + UI
- JSON manifest-based metadata system
- Hot-swappable components without app restart

### Built-in Components

- **Dashboard**: System overview and real-time metrics
- **Analytics**: Traffic analytics and data visualization  
- **Settings**: Application configuration management

## Quick Start

```powershell
cd examples\modular
```

```powershell
python main.py --port 8081 --host localhost
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main SPA application |
| `GET /api/discovery` | Complete API endpoint discovery |
| `GET /api/components` | Secure component registry |
| `GET /api/components/manifests` | Component manifests |
| `GET /api/components/validate` | Component validation |

## Architecture

### Component Structure

Each component is self-contained providing:

- **REST API**: Data operations (`/api/{component}/data`)
- **Web Interface**: Frontend widget with secure loading
- **Manifest**: JSON metadata with security information
- **Message Handlers**: Nether framework integration

### Security Features

- **Validation Pipeline**: All components validated before registration
- **Secure Loading**: ES6 modules loaded through validated endpoints
- **Permission System**: Role-based access control
- **CSP Protection**: Content Security Policy enforcement

### Discovery System

- **Service Discovery**: `/api/discovery` provides complete endpoint mapping
- **Dynamic Routes**: Automatic route registration and discovery
- **Component Registry**: Centralized component management
- **Manifest System**: Standardized component metadata

## Configuration

```powershell
python main.py --help
```

**Options:**

- `--port 8081`: Server port (default: 8081)
- `--host localhost`: Server host (default: localhost)  
- `--log-level INFO`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Development

### Adding Components

1. Create component class extending `nether.Component`
2. Register in `System.register_components()`
3. Provide manifest with security metadata
4. Component automatically discovered and loaded

### Security Considerations

- All external components validated before registration
- CSP headers prevent unauthorized script execution
- Component permissions enforced at runtime
- Secure module loading prevents code injection

## Production Deployment

This example demonstrates production-ready patterns:

- Comprehensive error handling
- Security validation pipeline
- Service discovery mechanisms
- Component isolation and sandboxing

Built with [Nether Framework](https://github.com/wavelet-space/nether) - A modern Python framework for building distributed systems.
