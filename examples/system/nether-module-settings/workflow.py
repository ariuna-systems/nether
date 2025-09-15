#!/usr/bin/env python3
"""
Development workflow for nether-module-settings.

This script demonstrates the complete development workflow:
1. Frontend development and building
2. Asset bundling to Python module
3. Testing the integration
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run the complete development workflow."""
    project_root = Path(__file__).parent

    print("🚀 Nether Settings Module Development Workflow")
    print("=" * 50)

    print("\n📝 Project Structure:")
    print(f"   Root: {project_root}")
    print(f"   Frontend: {project_root / 'frontend'}")
    print(f"   Python: {project_root / 'python_module'}")
    print(f"   Build Tools: {project_root / 'build_tools'}")

    print("\n🎯 Workflow Steps:")

    # Step 1: Frontend Development
    print("\n1️⃣  Frontend Development")
    print("   → Run: cd frontend && npm install && npm run dev")
    print("   → Edit: frontend/src/components/settings-component.js")
    print("   → Test: Open http://localhost:3000 in browser")

    # Step 2: Build Frontend
    print("\n2️⃣  Build Frontend")
    print("   → Run: cd frontend && npm run build")
    print("   → Output: frontend/dist/settings-component.js")

    # Step 3: Bundle to Python
    print("\n3️⃣  Bundle to Python Module")
    print("   → Run: python build_tools/bundle.py")
    print("   → Output: python_module/static/settings-component.js")

    # Step 4: Test Integration
    print("\n4️⃣  Test Python Integration")
    print("   → Import: from python_module import SettingsComponent")
    print("   → API: GET /api/settings")
    print("   → Module: GET /modules/settings.js")

    # Step 5: Distribution
    print("\n5️⃣  Create Distribution")
    print("   → Run: python -m build")
    print("   → Output: dist/nether_module_settings-1.0.0.tar.gz")
    print("   → Install: pip install dist/nether_module_settings-1.0.0.tar.gz")

    print("\n🛠️  Available Commands:")
    commands = {
        "dev": "Start frontend development server",
        "build": "Build frontend and bundle to Python",
        "test": "Test Python module import",
        "package": "Create distributable package",
        "clean": "Clean build artifacts",
    }

    for cmd, desc in commands.items():
        print(f"   python workflow.py {cmd}  # {desc}")

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        handle_command(command, project_root)
    else:
        print(f"\n💡 Quick Start:")
        print(f"   1. cd {project_root}")
        print(f"   2. python workflow.py dev")
        print(f"   3. Open another terminal and run: python workflow.py build")
        print(f"   4. Test with: python workflow.py test")


def handle_command(command: str, project_root: Path):
    """Handle specific workflow commands."""
    try:
        if command == "dev":
            print("\n🔥 Starting frontend development server...")
            os.chdir(project_root / "frontend")

            # Install dependencies if needed
            if not (project_root / "frontend" / "node_modules").exists():
                print("📦 Installing dependencies...")
                subprocess.run(["npm", "install"], check=True)

            # Start dev server
            subprocess.run(["npm", "run", "dev"], check=True)

        elif command == "build":
            print("\n🔨 Building and bundling...")
            subprocess.run(
                [sys.executable, str(project_root / "build_tools" / "bundle.py")],
                check=True,
            )

        elif command == "test":
            print("\n🧪 Testing Python module...")
            sys.path.insert(0, str(project_root))

            try:
                from python_module import SettingsComponent

                print("✅ Module import successful")
                print(f"   Module: {SettingsComponent}")

                # Check if static files exist
                static_dir = project_root / "python_module" / "static"
                if static_dir.exists():
                    files = list(static_dir.glob("*"))
                    print(f"✅ Static files found: {len(files)} files")
                    for file in files:
                        print(f"   📄 {file.name}")
                else:
                    print("⚠️  No static files found - run 'build' first")

            except ImportError as e:
                print(f"❌ Import failed: {e}")

        elif command == "package":
            print("\n📦 Creating distributable package...")
            subprocess.run(
                [sys.executable, "-m", "build"], cwd=project_root, check=True
            )
            print("✅ Package created in dist/")

        elif command == "clean":
            print("\n🧹 Cleaning build artifacts...")
            artifacts = [
                "frontend/dist",
                "frontend/node_modules",
                "python_module/static",
                "dist",
                "*.egg-info",
            ]

            for pattern in artifacts:
                for path in project_root.glob(pattern):
                    if path.exists():
                        if path.is_dir():
                            import shutil

                            shutil.rmtree(path)
                            print(f"   🗑️  Removed directory: {path}")
                        else:
                            path.unlink()
                            print(f"   🗑️  Removed file: {path}")

        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: dev, build, test, package, clean")

    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
