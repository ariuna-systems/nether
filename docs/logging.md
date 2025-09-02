# Nether Framework Logging

The Nether framework now includes comprehensive logging capabilities that allow you to track every message going through the mediator. This logging system supports both stdout and file logging with configurable log levels and verbosity.

## Features

- **Comprehensive Message Logging**: Every message processed by the mediator is logged with detailed information
- **Dual Output**: Log to both stdout and file simultaneously
- **Configurable Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, and CRITICAL levels
- **Command Line Configuration**: Easy setup via CLI arguments
- **Structured Logging**: Consistent timestamp format with timezone information
- **Component Tracking**: Logs component attachment/detachment and message routing
- **Context Management**: Tracks message processing contexts and their lifecycle

## CLI Arguments

When creating a Nether application, you can configure logging using these command-line arguments:

- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set the logging level (default: INFO)
- `--log-file LOG_FILE`: Path to the log file for file logging (optional)
- `--verbose`, `-v`: Increase verbosity level (can be used multiple times)

## Usage Examples

### Basic Usage (stdout only)

```bash
python your_app.py --log-level INFO
```

### Enable DEBUG logging

```bash
python your_app.py --log-level DEBUG
```

### Log to file and stdout

```bash
python your_app.py --log-level INFO --log-file logs/app.log
```

### Maximum verbosity with file logging

```bash
python your_app.py --log-level DEBUG --log-file logs/debug.log -v -v
```

## What Gets Logged

### Message Processing

- **Message Reception**: When a message enters the mediator
- **Message Type**: Command, Query, or Event classification
- **Component Matching**: Which components can handle the message
- **Message Dispatch**: Routing information to handlers
- **Processing Results**: Success or failure of message handling

### Component Lifecycle

- **Component Attachment**: When components are registered
- **Component Detachment**: When components are unregistered
- **Supported Message Types**: What messages each component handles

### Context Management

- **Context Creation**: New processing contexts (units of work)
- **Context Lifecycle**: Context attachment, processing, and cleanup
- **Error Handling**: Exceptions and error conditions

## Log Format

Each log entry includes:

- **Timestamp**: ISO format with timezone (e.g., `2025-09-02 17:29:08.283 +02:00`)
- **Logger Name**: Module or component name (e.g., `nether.mediator`)
- **Log Level**: DEBUG, INFO, WARNING, ERROR, or CRITICAL
- **Message**: Detailed information about the event

Example:

```
2025-09-02 17:29:08.284 +02:00 - nether.mediator - INFO - Component LoggingDemoComponent attached (supports: LogTestCommand | LogTestQuery)
```

## Implementation in Your Application

To use the new logging system in your Nether application:

1. **Import the Nether system**:

   ```python
   import nether
   ```

2. **Create a configuration with logging arguments**:

   ```python
   import argparse
   
   parser = argparse.ArgumentParser()
   parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO")
   parser.add_argument("--log-file", help="Path to log file")
   parser.add_argument("--verbose", "-v", action="count", default=0)
   args = parser.parse_args()
   
   config = argparse.Namespace(
       log_level=args.log_level,
       log_file=args.log_file,
       verbose=args.verbose
   )
   ```

3. **Create your Nether application**:

   ```python
   class MyApp(nether.Nether):
       async def main(self):
           # Your application logic here
           pass
   
   app = MyApp(configuration=config)
   nether.execute(app.start())
   ```

## Demo Application

The `examples/logging_demo.py` file provides a complete demonstration of the logging capabilities. Run it with different options to see the logging in action:

```bash
# Basic demo
python examples/logging_demo.py

# Debug level with file logging
python examples/logging_demo.py --log-level DEBUG --log-file logs/demo.log

# Maximum verbosity
python examples/logging_demo.py --log-level DEBUG --log-file logs/verbose.log -v -v
```

## Benefits

1. **Debugging**: Easily trace message flow through your application
2. **Monitoring**: Track application behavior in production
3. **Audit Trail**: Complete record of all message processing
4. **Performance Analysis**: Identify bottlenecks and processing patterns
5. **Error Diagnosis**: Detailed context for troubleshooting issues

## File Logging

When using file logging:

- Log files are created with UTF-8 encoding
- Parent directories are created automatically if they don't exist
- Logs are appended to existing files
- Both stdout and file receive the same log entries
- File logging errors are reported but don't stop the application

## Performance

The logging system is designed to be efficient:

- Uses structured logging with lazy evaluation
- Configurable log levels to control output volume
- Minimal performance impact on message processing
- File I/O is handled asynchronously where possible

This logging system provides complete visibility into your Nether application's message processing, making debugging, monitoring, and maintenance much easier.
