# Nether Settings Module

Independent settings module for Nether applications with modern frontend development workflow.

## Structure

```
nether-module-settings/
├── frontend/              # Frontend development (Vite + Modern JS)
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── components/
│   │   │   └── settings-component.js
│   │   └── styles/
│   └── dist/             # Build output
├── python_module/        # Python module
│   ├── __init__.py
│   ├── settings.py       # Nether component
│   └── static/          # Bundled frontend assets
└── build_tools/
    └── bundle.py        # Frontend -> Python bundling
```

## Development Workflow

1. **Frontend Development**: Use `npm run dev` in `frontend/` for hot reload
2. **Build Frontend**: `npm run build` to create `dist/`
3. **Bundle to Python**: `python build_tools/bundle.py` to copy assets
4. **Test Integration**: Import and use the Python module

## Features

- ⚡ Modern frontend development with Vite
- 🔧 Independent component development
- 📦 Bundled distribution as Python package
- 🎨 Modern web components with ES6 modules
- 🔒 Secure asset serving through Python
