"""
Vercel serverless entry point for Tennis Hub.
"""
import sys
import os
from pathlib import Path

# Add project root to path so app/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
