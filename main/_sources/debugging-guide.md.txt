# Enhanced HTTP Server Debugging

The nether HTTP server now includes comprehensive debugging capabilities to help you troubleshoot 404 errors and routing issues.

## Features

When running with `--log-level DEBUG`, the server will provide detailed logging for:

### 1. Request Tracking

- All incoming requests with method, path, and query parameters
- Request headers
- Response status codes
- Request processing flow

### 2. Route Resolution

- Detailed route matching attempts
- Available route prefixes
- Dynamic vs static route handling
- Method availability checks

### 3. 404 Error Debugging

- Detailed 404 error information including:
  - Requested path and query parameters
  - Request headers
  - All registered dynamic routes
  - All registered static routes
  - Suggested similar paths (if any)

### 4. Method Not Allowed (405) Debugging

- Which methods are allowed for a given path
- Which methods are implemented by view classes

### 5. Route Registration Logging

- When routes are added (both static and dynamic)
- Complete route dump at server startup
- Distinction between frozen app routes and regular routes

## Usage

### Basic Usage

```bash
python your_app.py --log-level DEBUG
```

### Using the Debug Example

A debug server example is provided to test the debugging capabilities:

```bash
cd examples
python debug_server.py --log-level DEBUG
```

This will start a server with some example routes and static files. Try accessing these URLs to see the debug output:

**Valid routes:**

- `http://localhost:8080/hello` - Simple hello world
- `http://localhost:8080/api` - JSON API (GET/POST)
- `http://localhost:8080/static/test.txt` - Static file

**Invalid routes (to see 404 debugging):**

- `http://localhost:8080/nonexistent`
- `http://localhost:8080/api/v1/users`
- `http://localhost:8080/hello/world`

**Method not allowed (to see 405 debugging):**

- `POST http://localhost:8080/hello` (only GET is supported)

## Debug Output Examples

### Server Startup (DEBUG level)

```
2025-09-03 10:30:00.123 +00:00 - nether.server - INFO - Server started on localhost:8080.
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG - === Registered Routes ===
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG - Main router routes:
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG -   /hello
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG -   /api
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG - Static routes:
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG -   /static -> /path/to/static
2025-09-03 10:30:00.124 +00:00 - nether.server - DEBUG - === End Routes ===
```

### Successful Request (DEBUG level)

```
2025-09-03 10:30:15.456 +00:00 - nether.server - DEBUG - Incoming request: GET /hello
2025-09-03 10:30:15.456 +00:00 - nether.server - DEBUG - Processing request: GET /hello from 127.0.0.1
2025-09-03 10:30:15.456 +00:00 - nether.server - DEBUG - Route matched: /hello -> <class 'HelloView'>
2025-09-03 10:30:15.457 +00:00 - nether.server - DEBUG - View HelloView served: /hello -> 200
2025-09-03 10:30:15.457 +00:00 - nether.server - DEBUG - Response: 200 for GET /hello
```

### 404 Error (DEBUG level)

```
2025-09-03 10:30:30.789 +00:00 - nether.server - DEBUG - Incoming request: GET /nonexistent
2025-09-03 10:30:30.789 +00:00 - nether.server - DEBUG - Processing request: GET /nonexistent from 127.0.0.1
2025-09-03 10:30:30.789 +00:00 - nether.server - DEBUG - Available route prefixes: ['/', '/hello', '/api']
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG - 404 NOT FOUND: GET /nonexistent
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG - Query string: 
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG - Headers: {'Host': 'localhost:8080', 'User-Agent': 'curl/7.68.0', 'Accept': '*/*'}
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG - Registered dynamic routes:
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG -   / -> /hello
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG -   / -> /api
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG - Registered static routes:
2025-09-03 10:30:30.790 +00:00 - nether.server - DEBUG -   /static -> /path/to/static
```

### Method Not Allowed (DEBUG level)

```
2025-09-03 10:30:45.123 +00:00 - nether.server - DEBUG - Incoming request: POST /hello
2025-09-03 10:30:45.123 +00:00 - nether.server - DEBUG - Processing request: POST /hello from 127.0.0.1
2025-09-03 10:30:45.123 +00:00 - nether.server - DEBUG - Route matched: /hello -> <class 'HelloView'>
2025-09-03 10:30:45.123 +00:00 - nether.server - DEBUG - Method POST not implemented by HelloView. Available methods: ['get']
```

## Integration with Existing Applications

The enhanced debugging is automatically enabled when you:

1. Set the log level to DEBUG (`--log-level DEBUG`)
2. Use the nether Server class
3. Have proper logging configuration

No code changes are required in your existing applications. Just run with DEBUG logging to get comprehensive debugging information.

## Tips for Debugging 404 Errors

1. **Check route registration**: Look for "View assigned to route" messages at startup
2. **Verify route patterns**: Dynamic routes use `{param}` syntax
3. **Check static file paths**: Ensure static directories exist and are readable
4. **Compare similar paths**: The debug output suggests similar registered paths
5. **Verify middleware order**: Middlewares are processed in order, which can affect routing

## Configuration

The debug logging respects the standard Python logging configuration. You can also configure it programmatically:

```python
from nether.logging import configure_global_logging

# Configure with DEBUG level
configure_global_logging(log_level="DEBUG")

# Or configure to a file
configure_global_logging(log_level="DEBUG", log_file=Path("server.log"))
```
