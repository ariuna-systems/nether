# Copilot Guidelines

## Environment & Tools

- **PowerShell only**: Use PowerShell commands, never Bash/Unix
- **Virtual environments**: Always use `uv venv` and activate before Python work
- **Package management**: Use `uv pip` for all operations
- **Build system**: Use `uv build`, never `python -m build`
- **Windows native**: Stick to Windows-compatible solutions only

## Prohibited Commands & Tools

- **NEVER use**: `kill`, `curl`, `grep`, `sed`, `awk`, Linux/Unix tools
- **NEVER use**: `python -m build`, `pip install`, `pip list` - use `uv` equivalents
- **NEVER use**: `rm`, `cp`, `mv` - use PowerShell: `Remove-Item`, `Copy-Item`, `Move-Item`
- **NEVER use**: Emojis in code, comments, documentation

## Python Development Workflow

- **Virtual env**: `uv venv` then `.\.venv\Scripts\activate`
- **Install**: `uv pip install -r requirements.txt` or `uv pip install package`
- **Build**: `uv build` (creates wheel + source distribution)
- **Test install**: `uv pip install .\dist\package.whl` then test import
- **List packages**: `uv pip list`

## File Operations

- **PowerShell commands**: `Remove-Item`, `Copy-Item`, `Move-Item`, `New-Item`
- **Navigation**: Use `cd` (not `pushd`/`popd`)
- **Listing**: Use `ls` or `Get-ChildItem`
- **Content**: Use `cat` or `Get-Content`

## Code Style & Quality

- **No emojis**: Never in code, comments, docs, commits
- **Imports**: Absolute imports, avoid relative where possible
- **Type hints**: Include for function parameters and return values
- **Docstrings**: Google-style for all public functions
- **Error handling**: Specific exceptions, avoid bare `except:`

## Testing & Validation

- **Test after changes**: Always test code changes immediately
- **Import testing**: Verify modules import without errors
- **Function testing**: Test key functions with sample inputs
- **Build testing**: Test package builds and installations

## Communication Style

- **Direct and concise**: Brief but clear, avoid unnecessary explanations
- **Action-oriented**: Focus on what to do, not why
- **No filler words**: Avoid "actually", "basically", "you know", etc.
- **Technical focus**: Stay technical, avoid casual language

## Project Structure

- **Clean separation**: Keep stub packages separate from main code
- **Minimal files**: Only essential files in packages
- **Proper metadata**: Use organization info, not personal details
- **Version sync**: Keep versions consistent between files
- **requirements.txt**: Development-only dependencies, not essential for distribution
- **.editorconfig**: Development-only editor configuration, not essential for distribution
- **Package excludes**: Always exclude tests from setuptools.packages.find with `exclude = ["tests*"]`

## Security & Privacy

- **No personal info**: Never expose emails, API keys, sensitive data
- **Email choice**: Ask which email to use in projects (organization or personal)
- **Clean commits**: No sensitive data or large files in git history

## Common Pitfalls to Avoid

- **Don't suggest Linux commands** on Windows systems
- **Don't use pip directly** when uv is available
- **Don't include dev files** in package distributions
- **Don't use personal information** in public packages
- **Don't suggest untested workflows** without validation

## Preferred Response Format

- **Step-by-step**: Break complex tasks into numbered steps
- **Code blocks**: Proper syntax highlighting for all code
- **Validation**: Always include verification steps
- **Error handling**: Anticipate common errors and provide solutions
