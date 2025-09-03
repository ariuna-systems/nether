#!/usr/bin/env python3
"""
Simple runner script for nether-system-example
"""

import sys
import os

# Add the current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from nether_system_example import main

    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)
