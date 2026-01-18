"""
Vercel Serverless Function Entry Point for TradeWise
This file imports and exports the FastAPI app for Vercel deployment
"""
import sys
from pathlib import Path

# Add parent directory to Python path to import main
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from main import app

# Vercel expects the app to be available at the module level
# The main.py file contains the actual FastAPI application
__all__ = ['app']

