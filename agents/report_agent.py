"""
report_agent.py — Report Generation Agent

Role: Takes all outputs from the previous agents and makes a single call to the
OpenAI API (gpt-4o-mini) to generate a clean, human-readable trade thesis. The
final report is then printed to the terminal using the 'rich' library.

Input:  regime_result, momentum_result, risk_result dicts
Output: Prints a formatted report to terminal; returns the report text as a string
"""

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from config import API_KEY, MODEL_NAME


# Create a Rich console for beautiful terminal output
console = Console()


def _build_prompt(regime: dict, momentum: dict, risk: dict) -> str:
    """Construct the prompt we send to the LLM from structured agent outputs."""

    # Extract key values safely (handle NEUTRAL case)
    signal   = momentum.get("signal", "NEUTRAL")
    entry    = risk.get("entry", "N/A")
    sl       = risk.get("stop_loss", "N/A")
    tp       = risk.get("take_profit", "N/A")
    pos_size = risk.get("position_size_oz", "N/A")

    indicators = momentum.get("indicators", {})
    metrics    = regime.get("metrics", {})

    prompt = f"""
You are a professional gold market analyst. Based on the following data from a multi-agent trading system,
write a concise 3-4 sentence trade thesis in plain English that a non-expert could understand.

MARKET REGIME ANALYSIS:
- Detected regime: {regime['regime']} (confidence: {regime['confidence']:.0%})
- Reason: {regime['reason']}
- ADX: {metrics.get('adx', 'N/A')} | ATR: {metrics.get('atr', 'N/A')} | Price vs EMA50: {metrics.get('price_vs_ema50', 'N/A')}

MOMENTUM SIGNAL:
- Signal: {signal}
- Entry zone: {momentum.get('entry_zone', 'N/A')}
- EMA9: {indicators.get('ema9', 'N/A')} | EMA21: {indicators.get('ema21', 'N/A')} | Cross: {indicators.get('ema_cross', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')} | RSI: {indicators.get('rsi', 'N/A')}
- Reasoning: {', '.join(momentum.get('reasoning', ['N/A']))}

RISK PARAMETERS:
- Entry: ${entry}
- Stop Loss: ${sl}
- Take Profit: ${tp}
- Position Size: {pos_size} oz
- Risk Summary: {risk.get('summary', 'N/A')}

Write the thesis as 3-4 flowing sentences. Start with what the market is doing, then explain the trade opportunity,
then mention the key risk level. Keep it concise, professional but accessible.
"""
    return prompt.strip()


def run(regime_result: dict, momentum_result: dict, risk_result: dict) -> str:
    """
    Main entry point for the Report Agent.
    Calls OpenAI API and prints formatted report to terminal.
    """

    print("\n[Report Agent] Generating final trade report via LLM...")

    # ── Step 1: Call OpenAI API ───────────────────────────────────────────────
    client = OpenAI(api_key=API_KEY)
    prompt = _build_prompt(regime_result, momentum_result, risk_result)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a concise, professional gold market analyst."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=300,
        temperature=0.4,
    )

    thesis = response.choices[0].message.content.strip()
    print("[Report Agent] LLM thesis received. Rendering final report...")

    # ── Step 2: Extract values for display ───────────────────────────────────
    signal      = momentum_result.get("signal", "NEUTRAL")
    regime      = regime_result.get("regime", "UNKNOWN")
    confidence  = regime_result.get("confidence", 0)
    metrics     = regime_result.get("metrics", {})
    indicators  = momentum_result.get("indicators", {})
    entry       = risk_result.get("entry", "N/A")
    stop_loss   = risk_result.get("stop_loss", "N/A")
    take_profit = risk_result.get("take_profit", "N/A")
    pos_size    = risk_result.get("position_size_oz", "N/A")
    dollar_risk = risk_result.get("dollar_risk", "N/A")
    rr_ratio    = risk_result.get("risk_reward_ratio", "2:1")

    # Choose a color scheme based on signal
    signal_color = {"LONG": "green", "SHORT": "red", "NEUTRAL": "yellow"}.get(signal, "white")
    regime_color = {"TRENDING": "cyan", "VOLATILE": "magenta", "RANGING": "blue"}.get(regime, "white")

    # ── Step 3: Print the report using Rich ───────────────────────────────────
    console.print()
    console.rule("[bold gold1]  GOLD TRADING SYSTEM — FINAL REPORT  [/bold gold1]")
    console.print()

    # — Regime Section —
    console.print(Panel(
        f"[bold {regime_color}]{regime}[/bold {regime_color}]  |  Confidence: [bold]{confidence:.0%}[/bold]\n\n"
        f"[dim]{regime_result.get('reason', '')}[/dim]",
        title="[bold]MARKET REGIME[/bold]",
        border_style=regime_color,
        padding=(1, 2),
    ))

    # — Indicators Table —
    ind_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold white")
    ind_table.add_column("Indicator", style="dim", width=18)
    ind_table.add_column("Value", justify="right")
    ind_table.add_column("Indicator", style="dim", width=18)
    ind_table.add_column("Value", justify="right")

    ind_table.add_row(
        "ADX (14)",    f"[bold]{metrics.get('adx', 'N/A')}[/bold]",
        "RSI (14)",    f"[bold]{indicators.get('rsi', 'N/A')}[/bold]",
    )
    ind_table.add_row(
        "ATR (14)",    f"{metrics.get('atr', 'N/A')}",
        "MACD",        f"{indicators.get('macd', 'N/A')}",
    )
    ind_table.add_row(
        "EMA9",        f"{indicators.get('ema9', 'N/A')}",
        "EMA21",       f"{indicators.get('ema21', 'N/A')}",
    )
    ind_table.add_row(
        "EMA50",       f"{metrics.get('ema50', 'N/A')}",
        "EMA Cross",   f"{indicators.get('ema_cross', 'N/A')}",
    )
    console.print(Panel(ind_table, title="[bold]KEY INDICATORS[/bold]", border_style="dim white", padding=(0, 1)))

    # — Signal & Risk Table —
    risk_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold white")
    risk_table.add_column("Parameter", style="dim", width=22)
    risk_table.add_column("Value", justify="right", width=16)

    risk_table.add_row("Signal",        f"[bold {signal_color}]{signal}[/bold {signal_color}]")
    risk_table.add_row("Entry Price",   f"[bold]${entry:,.2f}[/bold]" if isinstance(entry, float) else f"${entry}")
    risk_table.add_row(
        "Stop Loss",
        f"[bold red]${stop_loss:,.2f}[/bold red]" if isinstance(stop_loss, float) else "N/A"
    )
    risk_table.add_row(
        "Take Profit",
        f"[bold green]${take_profit:,.2f}[/bold green]" if isinstance(take_profit, float) else "N/A"
    )
    risk_table.add_row("Risk : Reward", f"[bold]{rr_ratio}[/bold]")
    risk_table.add_row(
        "Position Size",
        f"[bold]{pos_size} oz[/bold]" if pos_size != "N/A" else "N/A"
    )
    risk_table.add_row(
        "Max Dollar Risk",
        f"[bold yellow]${dollar_risk:,.0f}[/bold yellow]" if isinstance(dollar_risk, float) else "N/A"
    )
    console.print(Panel(risk_table, title="[bold]TRADE PARAMETERS[/bold]", border_style=signal_color, padding=(0, 1)))

    # — Trade Thesis (LLM Generated) —
    console.print(Panel(
        f"[italic]{thesis}[/italic]",
        title="[bold]TRADE THESIS[/bold]",
        border_style="gold1",
        padding=(1, 2),
    ))

    console.print()
    console.rule("[dim]End of Report[/dim]")
    console.print()

    return thesis
