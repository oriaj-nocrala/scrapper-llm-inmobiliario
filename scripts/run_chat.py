#!/usr/bin/env python3
"""
Startup script for the interactive property chat CLI.
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli.property_chat import main

if __name__ == "__main__":
    main()