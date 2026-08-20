"""
regime_agent.py — Market Regime Classifier Agent

Role: Fetches the last 90 days of Gold (XAU/USD) price data and uses technical
indicators (ADX, ATR, EMA) to classify the current market into one of three
regimes: TRENDING, VOLATILE, or RANGING.

Input:  None (fetches its own data from Yahoo Finance)
Output: A dictionary with regime label, confidence score, and key metric values
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from config import GOLD_TICKER, LOOKBACK_DAYS, ADX_TREND_THRESHOLD, ATR_VOLATILE_MULTIPLIER


def run() -> dict:
    """
    Main entry point for the Regime Classifier Agent.
    Returns a dict describing the detected market regime.
    """

    print("\n[Regime Agent] Starting market regime classification...")

    # ── Step 1: Fetch historical OHLCV data from Yahoo Finance ───────────────
    print(f"[Regime Agent] Fetching last {LOOKBACK_DAYS} days of Gold ({GOLD_TICKER}) data...")
    raw = yf.download(GOLD_TICKER, period=f"{LOOKBACK_DAYS}d", interval="1d", progress=False)

    # Flatten MultiIndex columns if present (yfinance sometimes returns them)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    if raw.empty or len(raw) < 30:
        raise ValueError("Not enough data returned from Yahoo Finance. Check ticker or internet connection.")

    df = raw.copy()
    print(f"[Regime Agent] Loaded {len(df)} trading days of data. Latest close: ${float(df['Close'].iloc[-1]):,.2f}")

    # ── Step 2: Compute ADX (Average Directional Index) ──────────────────────
    # ADX measures the STRENGTH of a trend (not direction). Range 0-100.
    # Values above 25 indicate a strong trend is present.
    adx_df = ta.adx(df["High"], df["Low"], df["Close"], length=14)
    df["ADX"] = adx_df["ADX_14"].values

    current_adx = float(df["ADX"].iloc[-1])
    print(f"[Regime Agent] ADX (14) = {current_adx:.2f}  (>25 = trending market)")

    # ── Step 3: Compute ATR (Average True Range) ──────────────────────────────
    # ATR measures VOLATILITY — how much price moves on average each day.
    # We compare today's ATR to its 20-day rolling average.
    atr_series = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["ATR"] = atr_series.values
    df["ATR_20avg"] = df["ATR"].rolling(20).mean()

    current_atr = float(df["ATR"].iloc[-1])
    avg_atr = float(df["ATR_20avg"].iloc[-1])
    atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
    print(f"[Regime Agent] ATR (14) = {current_atr:.2f} | 20-day avg ATR = {avg_atr:.2f} | Ratio = {atr_ratio:.2f}")

    # ── Step 4: Compute 50-day EMA (Exponential Moving Average) ──────────────
    # The 50 EMA smooths price to show the medium-term trend direction.
    # If price is above EMA50, the market is in an uptrend; below = downtrend.
    df["EMA50"] = ta.ema(df["Close"], length=50)

    current_price = float(df["Close"].iloc[-1])
    current_ema50 = float(df["EMA50"].iloc[-1])
    price_vs_ema = "ABOVE" if current_price > current_ema50 else "BELOW"
    print(f"[Regime Agent] Price ${current_price:,.2f} is {price_vs_ema} EMA50 (${current_ema50:,.2f})")

    # ── Step 5: Classify the regime ──────────────────────────────────────────
    # Priority order: VOLATILE > TRENDING > RANGING
    if atr_ratio >= ATR_VOLATILE_MULTIPLIER:
        regime = "VOLATILE"
        # Confidence is how far the ATR ratio exceeds the threshold (capped at 1.0)
        confidence = min(1.0, (atr_ratio - ATR_VOLATILE_MULTIPLIER) / ATR_VOLATILE_MULTIPLIER + 0.5)
        reason = f"ATR is {atr_ratio:.2f}x its 20-day average (threshold: {ATR_VOLATILE_MULTIPLIER}x)"

    elif current_adx > ADX_TREND_THRESHOLD:
        regime = "TRENDING"
        # Confidence scales with how strong the ADX reading is
        confidence = min(1.0, (current_adx - ADX_TREND_THRESHOLD) / 25 + 0.5)
        direction = "UPTREND" if price_vs_ema == "ABOVE" else "DOWNTREND"
        reason = f"ADX = {current_adx:.1f} (>{ADX_TREND_THRESHOLD}) and price is {price_vs_ema} EMA50 => {direction}"

    else:
        regime = "RANGING"
        # Confidence = how far ADX is from the trend threshold (lower ADX = more confident it's ranging)
        confidence = min(1.0, (ADX_TREND_THRESHOLD - current_adx) / ADX_TREND_THRESHOLD + 0.3)
        reason = f"ADX = {current_adx:.1f} (<{ADX_TREND_THRESHOLD}) and ATR ratio = {atr_ratio:.2f} (low volatility)"

    confidence = round(confidence, 2)
    print(f"[Regime Agent] Regime classified as: {regime} (confidence: {confidence:.0%})")
    print(f"[Regime Agent] Reason: {reason}")

    # ── Step 6: Return a structured result ───────────────────────────────────
    return {
        "regime": regime,
        "confidence": confidence,
        "reason": reason,
        "metrics": {
            "adx": round(current_adx, 2),
            "atr": round(current_atr, 2),
            "atr_20avg": round(avg_atr, 2),
            "atr_ratio": round(atr_ratio, 2),
            "current_price": round(current_price, 2),
            "ema50": round(current_ema50, 2),
            "price_vs_ema50": price_vs_ema,
        },
    }
