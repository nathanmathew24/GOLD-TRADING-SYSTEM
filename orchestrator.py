"""
orchestrator.py — Master Orchestrator Agent

Role: The central coordinator of the entire trading system. It runs each agent
in the correct sequence, passes data between them, and handles any errors.
Think of it as the conductor of an orchestra — it doesn't play any instrument
itself, but it keeps all players in sync.

Pipeline:
  1. Regime Classifier → detect market state
  2. Momentum Agent    → generate trade signal (only if TRENDING)
  3. Risk Agent        → calculate position parameters
  4. Report Agent      → generate and display final report

Input:  None (self-contained)
Output: Final report printed to terminal; returns all results as a dict
"""

from rich.console import Console
from agents import regime_agent, momentum_agent, risk_agent, report_agent

console = Console()


def run_pipeline() -> dict:
    """
    Execute the full multi-agent pipeline from regime detection to final report.
    Returns all intermediate and final results for inspection.
    """

    console.print()
    console.rule("[bold gold1]  GOLD TRADING SYSTEM  |  Starting Pipeline  [/bold gold1]")

    results = {}

    # ── Stage 1: Regime Classification ───────────────────────────────────────
    # Always runs first — we need to know the market regime before anything else
    console.print("\n[bold cyan]Stage 1/4:[/bold cyan] Running Regime Classifier...")
    try:
        regime_result = regime_agent.run()
        results["regime"] = regime_result
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Regime Agent failed: {e}[/bold red]")
        raise

    regime = regime_result["regime"]
    console.print(f"[bold cyan][Orchestrator][/bold cyan] Regime detected: [bold]{regime}[/bold]")

    # ── Stage 2: Strategy Selection ──────────────────────────────────────────
    # Currently, we route TRENDING to the Momentum Agent.
    # VOLATILE and RANGING log a message — this is where other strategy agents
    # (e.g., a mean-reversion agent) would be plugged in.
    console.print(f"\n[bold cyan]Stage 2/4:[/bold cyan] Routing to appropriate strategy agent...")

    if regime == "TRENDING":
        console.print("[bold cyan][Orchestrator][/bold cyan] Activating Momentum Agent (TRENDING regime)...")
        try:
            momentum_result = momentum_agent.run(regime_result)
            results["momentum"] = momentum_result
        except Exception as e:
            console.print(f"[bold red][Orchestrator] Momentum Agent failed: {e}[/bold red]")
            raise

    elif regime == "VOLATILE":
        console.print("[bold yellow][Orchestrator] VOLATILE regime detected. No active strategy for this regime. Defaulting to NEUTRAL signal.[/bold yellow]")
        momentum_result = _neutral_signal(regime_result, "Market is too volatile for a defined strategy.")
        results["momentum"] = momentum_result

    else:  # RANGING
        console.print("[bold blue][Orchestrator] RANGING regime detected. No active strategy for this regime. Defaulting to NEUTRAL signal.[/bold blue]")
        momentum_result = _neutral_signal(regime_result, "Market is ranging — no clear directional bias.")
        results["momentum"] = momentum_result

    # ── Stage 3: Risk Calculation ─────────────────────────────────────────────
    console.print(f"\n[bold cyan]Stage 3/4:[/bold cyan] Running Risk Agent...")
    try:
        risk_result = risk_agent.run(momentum_result)
        results["risk"] = risk_result
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Risk Agent failed: {e}[/bold red]")
        raise

    # ── Stage 4: Report Generation ────────────────────────────────────────────
    console.print(f"\n[bold cyan]Stage 4/4:[/bold cyan] Running Report Agent...")
    try:
        report_text = report_agent.run(regime_result, momentum_result, risk_result)
        results["report"] = report_text
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Report Agent failed: {e}[/bold red]")
        raise

    console.print("[bold green][Orchestrator] Pipeline completed successfully.[/bold green]")
    return results


def _neutral_signal(regime_result: dict, reason: str) -> dict:
    """
    Returns a default NEUTRAL momentum result when no strategy agent is active.
    Used for VOLATILE and RANGING regimes.
    """
    price = regime_result["metrics"]["current_price"]
    atr   = regime_result["metrics"]["atr"]
    return {
        "signal": "NEUTRAL",
        "entry_zone": "No trade",
        "current_price": price,
        "reasoning": [reason],
        "indicators": {
            "ema9": "N/A", "ema21": "N/A", "ema_cross": "N/A",
            "macd": "N/A", "macd_histogram": "N/A", "rsi": "N/A",
        },
        "atr": atr,
    }
