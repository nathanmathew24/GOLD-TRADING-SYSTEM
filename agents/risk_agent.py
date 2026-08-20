"""
risk_agent.py — Risk Management Agent

Role: Takes the momentum signal, current price, and ATR to calculate safe trade
parameters including stop loss, take profit, and position sizing using the 2% rule.

Input:  momentum_result dict from momentum_agent.py + ATR value
Output: A dictionary with stop loss, take profit, position size, and risk summary
"""

from config import (
    PORTFOLIO_SIZE,
    RISK_PER_TRADE,
    ATR_STOP_MULTIPLIER,
    RISK_REWARD_RATIO,
)


def run(momentum_result: dict) -> dict:
    """
    Main entry point for the Risk Management Agent.
    Returns structured risk parameters for the trade.
    """

    print("\n[Risk Agent] Calculating risk parameters...")

    signal = momentum_result["signal"]
    current_price = momentum_result["current_price"]
    atr = momentum_result["atr"]

    print(f"[Risk Agent] Signal: {signal} | Entry price: ${current_price:,.2f} | ATR: {atr:.2f}")

    # If signal is NEUTRAL, no trade parameters needed
    if signal == "NEUTRAL":
        print("[Risk Agent] Signal is NEUTRAL — no risk parameters to calculate.")
        return {
            "signal": "NEUTRAL",
            "entry": current_price,
            "stop_loss": None,
            "take_profit": None,
            "risk_per_unit": None,
            "position_size_oz": None,
            "dollar_risk": None,
            "summary": "No trade recommended — signal is NEUTRAL.",
        }

    # ── Step 1: Calculate Stop Loss ───────────────────────────────────────────
    # Stop loss is placed 1.5x ATR away from entry.
    # For LONG trades: stop is BELOW entry (we exit if price drops too far)
    # For SHORT trades: stop is ABOVE entry (we exit if price rises too far)
    stop_distance = ATR_STOP_MULTIPLIER * atr  # e.g., 1.5 x $18 = $27 away from entry

    if signal == "LONG":
        stop_loss   = current_price - stop_distance
        take_profit = current_price + (stop_distance * RISK_REWARD_RATIO)
    else:  # SHORT
        stop_loss   = current_price + stop_distance
        take_profit = current_price - (stop_distance * RISK_REWARD_RATIO)

    print(f"[Risk Agent] Stop distance (1.5x ATR): ${stop_distance:.2f}")
    print(f"[Risk Agent] Stop Loss: ${stop_loss:,.2f} | Take Profit: ${take_profit:,.2f}")

    # ── Step 2: Position Sizing (2% Rule) ────────────────────────────────────
    # We only risk 2% of our portfolio on any single trade.
    # Dollar amount we're willing to lose = 2% x portfolio size
    # Number of ounces we can trade = dollar risk / risk per ounce (stop distance)
    dollar_risk      = PORTFOLIO_SIZE * RISK_PER_TRADE       # e.g., $100,000 x 2% = $2,000
    position_size_oz = dollar_risk / stop_distance            # e.g., $2,000 / $27 = ~74 oz

    print(f"[Risk Agent] Portfolio: ${PORTFOLIO_SIZE:,} | Max risk: ${dollar_risk:,.0f} (2%)")
    print(f"[Risk Agent] Suggested position size: {position_size_oz:.1f} oz of Gold")

    # ── Step 3: Build risk summary string ────────────────────────────────────
    rr_label = f"{RISK_REWARD_RATIO:.0f}:1"
    summary = (
        f"Trade: {signal} Gold at ~${current_price:,.2f}. "
        f"Stop Loss at ${stop_loss:,.2f} ({ATR_STOP_MULTIPLIER}x ATR = ${stop_distance:.2f} away). "
        f"Take Profit at ${take_profit:,.2f} ({rr_label} risk-reward). "
        f"Position size: {position_size_oz:.1f} oz to risk ${dollar_risk:,.0f} (2% of portfolio)."
    )

    return {
        "signal": signal,
        "entry": round(current_price, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
        "risk_per_unit": round(stop_distance, 2),
        "position_size_oz": round(position_size_oz, 1),
        "dollar_risk": round(dollar_risk, 2),
        "risk_reward_ratio": rr_label,
        "summary": summary,
    }
