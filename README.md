# Gold Trading System

A multi-agent pipeline that analyzes Gold (XAU/USD futures, `GC=F`) and produces a rules-based, AI-narrated trade thesis — regime detection, signal generation, risk sizing, and a formatted report, all from one command.

```bash
python main.py
```

## How it works

The system routes through four agents, coordinated by [`orchestrator.py`](orchestrator.py):

```
Regime Agent  →  Momentum Agent  →  Risk Agent  →  Report Agent
```

1. **[Regime Agent](agents/regime_agent.py)** — pulls the last 90 days of daily Gold data from Yahoo Finance and classifies the market as `TRENDING`, `VOLATILE`, or `RANGING` using ADX (trend strength), ATR (volatility), and price vs. EMA50 (direction).
2. **[Momentum Agent](agents/momentum_agent.py)** — only runs when the regime is `TRENDING`. Generates a `LONG` / `SHORT` signal from EMA9/EMA21 crossovers, MACD, and RSI. For `VOLATILE` or `RANGING` regimes, the orchestrator skips this and returns a `NEUTRAL` signal instead — there's no defined strategy for those conditions yet.
3. **[Risk Agent](agents/risk_agent.py)** — turns a signal into concrete trade parameters: stop loss (1.5× ATR from entry), take profit (2:1 risk-reward), and position size using a 2%-of-portfolio risk rule ($100k assumed portfolio by default).
4. **[Report Agent](agents/report_agent.py)** — sends the combined output to OpenAI (`gpt-4o-mini`) to write a plain-English trade thesis, then renders everything as a formatted terminal report using `rich`.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root (see [`.env.example`](.env.example)) with your OpenAI key:

```
OPENAI_API_KEY=sk-your-key-here
```

The key is loaded from the environment at runtime — it is never hardcoded in source.

## Run

```bash
python main.py
```

Output is a live-updating terminal report showing the detected regime, signal, entry/stop/target levels, position size, and an AI-generated summary of the reasoning.

## Configuration

Tunable constants live in [`config.py`](config.py):

| Setting | Purpose |
|---|---|
| `GOLD_TICKER`, `LOOKBACK_DAYS` | Data source and history window |
| `ADX_TREND_THRESHOLD` | ADX above this = trending market |
| `ATR_VOLATILE_MULTIPLIER` | ATR above this multiple of its 20-day average = volatile market |
| `PORTFOLIO_SIZE`, `RISK_PER_TRADE` | Assumed portfolio size and % risked per trade |
| `ATR_STOP_MULTIPLIER`, `RISK_REWARD_RATIO` | Stop-loss distance and take-profit target |

## Project structure

```
trading_system/
├── main.py                 # Entry point
├── orchestrator.py         # Runs the 4-stage pipeline
├── config.py                # Settings, thresholds, API key loading
├── agents/
│   ├── regime_agent.py      # Market regime classification
│   ├── momentum_agent.py    # Trend-following signal generation
│   ├── risk_agent.py        # Stop loss / take profit / position sizing
│   └── report_agent.py      # AI-written report, rendered with `rich`
├── docs/
│   └── generate_docs.py     # Generates system_explanation.docx
└── requirements.txt
```

## Disclaimer

This is a hackathon / educational project. It is not financial advice, and the signals it produces should not be used to make real trading decisions without independent verification.
