"""
main.py — Entry Point for the Gold Trading System

Run this file to execute the full multi-agent pipeline:
    python main.py

The system will:
  1. Classify the current Gold market regime (TRENDING / VOLATILE / RANGING)
  2. Route to the Momentum Agent if the regime is TRENDING
  3. Calculate risk parameters (stop loss, take profit, position size)
  4. Generate and display a professional trade report in the terminal
"""

import sys
import os

# Add the project root to Python's module search path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_pipeline


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n\n[Interrupted] Pipeline stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        sys.exit(1)
