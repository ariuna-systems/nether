#!/usr/bin/env python3
"""
Build script for nether-module-settings.

This script:
1. Builds the frontend using Vite
2. Copies the built assets to the Python module's static directory
3. Optionally creates a Python package
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command: str, cwd: Path = None) -> bool:
    """Run a shell command and return success status."""
    try:
        print(f"Running: {command}")
        result = subprocess.run(
            command, shell=True, cwd=cwd, check=True, capture_output=True, text=True
        )
        print(f"✅ Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {command}:")
        print(f"  Return code: {e.returncode}")
        print(f"  STDOUT: {e.stdout}")
        print(f"  STDERR: {e.stderr}")
        return False


def main():
    """Main build process."""
    # Get project root
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    python_module_dir = project_root / "python_module"
    static_dir = python_module_dir / "static"

    print("🏗️  Building Nether Settings Module")
    print(f"Project root: {project_root}")
    print(f"Frontend dir: {frontend_dir}")
    print(f"Python module dir: {python_module_dir}")
    print()

    # Step 1: Install frontend dependencies
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        if not run_command("npm install", cwd=frontend_dir):
            print("❌ Failed to install dependencies")
            return False
    else:
        print("✅ Dependencies already installed")

    # Step 2: Build frontend
    print("🔨 Building frontend...")
    if not run_command("npm run build", cwd=frontend_dir):
        print("❌ Frontend build failed")
        return False

    # Step 3: Copy built assets to Python module
    print("📁 Copying assets to Python module...")

    dist_dir = frontend_dir / "dist"
    if not dist_dir.exists():
        print("❌ Frontend dist directory not found")
        return False

    # Clean and recreate static directory
    if static_dir.exists():
        shutil.rmtree(static_dir)
    static_dir.mkdir(parents=True)

    # Copy all files from dist to static
    for item in dist_dir.iterdir():
        if item.is_file():
            destination = static_dir / item.name
            shutil.copy2(item, destination)
            print(f"  📄 Copied: {item.name}")
        elif item.is_dir():
            destination = static_dir / item.name
            shutil.copytree(item, destination)
            print(f"  📁 Copied directory: {item.name}")

    # Step 4: Verify main module file exists
    main_module_file = static_dir / "settings-component.js"
    if main_module_file.exists():
        print(f"✅ Main module file created: {main_module_file}")

        # Show file size
        size = main_module_file.stat().st_size
        print(f"   Size: {size:,} bytes")

        # Show first few lines
        with open(main_module_file, "r", encoding="utf-8") as f:
            first_lines = "".join(f.readlines()[:3])
            print(f"   Preview: {first_lines.strip()[:100]}...")
    else:
        print("⚠️  Warning: Main module file not found")

    print()
    print("🎉 Build completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Test the Python module:")
    print(
        "   python -c \"from python_module import SettingsComponent; print('Import successful')\""
    )
    print("2. Use the component in your Nether application:")
    print("   from nether_module_settings import SettingsComponent")
    print("3. Access the frontend at: /modules/settings.js")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
