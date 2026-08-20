"""
config.py — Central configuration for the Gold Trading System.
Stores the API key, model name, and any shared constants used across agents.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── OpenAI API settings ──────────────────────────────────────────────────────
# Set OPENAI_API_KEY in your environment or in a local .env file (not committed).
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-4o-mini"

# ── Market data settings ─────────────────────────────────────────────────────
GOLD_TICKER = "GC=F"          # Yahoo Finance ticker for Gold Futures
LOOKBACK_DAYS = 90            # How many days of historical data to fetch

# ── Regime classification thresholds ────────────────────────────────────────
ADX_TREND_THRESHOLD = 25      # ADX above this value = trending market
ATR_VOLATILE_MULTIPLIER = 1.5 # ATR > 1.5x its 20-day average = volatile

# ── Risk management constants ────────────────────────────────────────────────
PORTFOLIO_SIZE = 100_000      # Assumed portfolio size in USD for position sizing
RISK_PER_TRADE = 0.02         # 2% of portfolio at risk per trade
ATR_STOP_MULTIPLIER = 1.5     # Stop loss = 1.5 x ATR from entry
RISK_REWARD_RATIO = 2.0       # Take profit = 2x the risk distance
