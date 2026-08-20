"""
momentum_agent.py — Momentum Strategy Agent

Role: Activated when the regime is TRENDING. Uses EMA crossover, MACD, and RSI
to determine the direction and strength of the trend and produce a trade signal.

Input:  regime_result dict from regime_agent.py
Output: A dictionary with signal (LONG/SHORT/NEUTRAL), entry zone, and reasoning
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from config import GOLD_TICKER, LOOKBACK_DAYS


def run(regime_result: dict) -> dict:
    """
    Main entry point for the Momentum Strategy Agent.
    Returns a dict with the trade signal and supporting analysis.
    """

    print("\n[Momentum Agent] Regime is TRENDING — running momentum analysis...")

    # ── Step 1: Re-fetch data (ensures freshness) ─────────────────────────────
    print(f"[Momentum Agent] Fetching Gold price data for indicator calculation...")
    raw = yf.download(GOLD_TICKER, period=f"{LOOKBACK_DAYS}d", interval="1d", progress=False)

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    df = raw.copy()

    # ── Step 2: Compute EMA 9 and EMA 21 (crossover) ─────────────────────────
    # When the fast EMA (9) crosses above the slow EMA (21) → bullish signal
    # When the fast EMA (9) crosses below the slow EMA (21) → bearish signal
    df["EMA9"]  = ta.ema(df["Close"], length=9)
    df["EMA21"] = ta.ema(df["Close"], length=21)

    ema9_now  = float(df["EMA9"].iloc[-1])
    ema21_now = float(df["EMA21"].iloc[-1])
    ema9_prev  = float(df["EMA9"].iloc[-2])
    ema21_prev = float(df["EMA21"].iloc[-2])

    # Detect crossover: did EMA9 just cross EMA21?
    bullish_cross = (ema9_prev < ema21_prev) and (ema9_now > ema21_now)
    bearish_cross = (ema9_prev > ema21_prev) and (ema9_now < ema21_now)
    ema_above = ema9_now > ema21_now  # True if fast EMA is above slow EMA

    print(f"[Momentum Agent] EMA9 = {ema9_now:.2f} | EMA21 = {ema21_now:.2f}")
    if bullish_cross:
        print("[Momentum Agent] EMA crossover: BULLISH CROSS detected")
    elif bearish_cross:
        print("[Momentum Agent] EMA crossover: BEARISH CROSS detected")
    else:
        pos = "above" if ema_above else "below"
        print(f"[Momentum Agent] EMA9 is {pos} EMA21 (no fresh cross)")

    # ── Step 3: Compute MACD ─────────────────────────────────────────────────
    # MACD = fast EMA (12) minus slow EMA (26). The histogram shows momentum.
    # A rising histogram = strengthening momentum in the current direction.
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    df["MACD"]        = macd_df["MACD_12_26_9"].values
    df["MACD_signal"] = macd_df["MACDs_12_26_9"].values
    df["MACD_hist"]   = macd_df["MACDh_12_26_9"].values

    macd_now  = float(df["MACD"].iloc[-1])
    hist_now  = float(df["MACD_hist"].iloc[-1])
    hist_prev = float(df["MACD_hist"].iloc[-2])
    macd_bullish = macd_now > 0 and hist_now > hist_prev  # MACD positive and growing
    macd_bearish = macd_now < 0 and hist_now < hist_prev  # MACD negative and falling

    print(f"[Momentum Agent] MACD = {macd_now:.2f} | Histogram = {hist_now:.2f} (prev: {hist_prev:.2f})")

    # ── Step 4: Compute RSI (14) ──────────────────────────────────────────────
    # RSI measures overbought/oversold conditions. Range 0–100.
    # Above 70 = overbought (avoid new LONG). Below 30 = oversold (avoid new SHORT).
    rsi_series = ta.rsi(df["Close"], length=14)
    df["RSI"] = rsi_series.values
    current_rsi = float(df["RSI"].iloc[-1])

    rsi_overbought = current_rsi > 70
    rsi_oversold   = current_rsi < 30
    print(f"[Momentum Agent] RSI (14) = {current_rsi:.2f} {'⚠ OVERBOUGHT' if rsi_overbought else '⚠ OVERSOLD' if rsi_oversold else '(neutral zone)'}")

    # ── Step 5: Determine trade signal ───────────────────────────────────────
    current_price = float(df["Close"].iloc[-1])
    reasons = []

    # Score bullish and bearish signals
    bullish_score = sum([
        ema_above,          # EMA9 above EMA21
        bullish_cross,      # Fresh bullish crossover
        macd_bullish,       # MACD above zero and rising
        not rsi_overbought, # RSI not in danger zone
    ])
    bearish_score = sum([
        not ema_above,      # EMA9 below EMA21
        bearish_cross,      # Fresh bearish crossover
        macd_bearish,       # MACD below zero and falling
        not rsi_oversold,   # RSI not in danger zone
    ])

    if bullish_score >= 3 and not rsi_overbought:
        signal = "LONG"
        entry_zone = f"${current_price - 5:.2f} – ${current_price + 5:.2f}"
        reasons.append("EMA9 above EMA21" if ema_above else "Bullish EMA cross")
        if macd_bullish:
            reasons.append("MACD positive and accelerating")
        reasons.append(f"RSI at {current_rsi:.1f} — room to run upward")

    elif bearish_score >= 3 and not rsi_oversold:
        signal = "SHORT"
        entry_zone = f"${current_price - 5:.2f} – ${current_price + 5:.2f}"
        reasons.append("EMA9 below EMA21" if not ema_above else "Bearish EMA cross")
        if macd_bearish:
            reasons.append("MACD negative and declining")
        reasons.append(f"RSI at {current_rsi:.1f} — room to fall further")

    else:
        signal = "NEUTRAL"
        entry_zone = "No trade — waiting for clearer signal"
        reasons.append("Mixed or conflicting indicator signals")
        if rsi_overbought:
            reasons.append(f"RSI = {current_rsi:.1f} — overbought, risky to enter LONG")
        if rsi_oversold:
            reasons.append(f"RSI = {current_rsi:.1f} — oversold, risky to enter SHORT")

    print(f"[Momentum Agent] Signal generated: {signal}")

    return {
        "signal": signal,
        "entry_zone": entry_zone,
        "current_price": round(current_price, 2),
        "reasoning": reasons,
        "indicators": {
            "ema9":  round(ema9_now, 2),
            "ema21": round(ema21_now, 2),
            "ema_cross": "BULLISH" if bullish_cross else "BEARISH" if bearish_cross else "NONE",
            "macd":  round(macd_now, 2),
            "macd_histogram": round(hist_now, 2),
            "rsi":   round(current_rsi, 2),
        },
        "atr": float(ta.atr(df["High"], df["Low"], df["Close"], length=14).iloc[-1]),
    }
