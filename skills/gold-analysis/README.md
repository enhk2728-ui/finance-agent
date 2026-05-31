<!-- Language Switcher -->
<p align="right">
  <a href="README.md">🇬🇧 English</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="README.zh.md">🇨🇳 中文</a>
</p>

<h1 align="center">
  <img src="https://img.shields.io/badge/XAUUSD-Gold-ebc934?style=flat-square" alt="XAUUSD">
  Gold Analysis
</h1>

<p align="center">
  <strong>Comprehensive XAUUSD price action analysis powered by Al Brooks methodology and agent-driven AI.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-4.2-blue?style=flat-square" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/framework-Streamlit-ff4b4b?style=flat-square" alt="streamlit">
  <img src="https://img.shields.io/badge/data-MT5-00549e?style=flat-square" alt="MT5">
  <img src="https://img.shields.io/badge/methodology-Al%20Brooks-8b5cf6?style=flat-square" alt="Al Brooks">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" alt="license">
</p>

---

## Overview

Gold Analysis is a **four-stage pipeline** from raw market data to an interactive financial dashboard.
It ingests real-time XAUUSD data from MT5, applies deterministic algorithmic analysis based on
Al Brooks' price action methodology, generates AI-powered market narratives through an
agent-driven LLM stage, and renders everything in a professional Streamlit dashboard.

```
MT5 (M5 data, N days)
  │
  ▼
price_action_analyzer.full_report()     ← Pure algorithm (no LLM)
  ├─ Swing points (up to 40)
  ├─ Price zones (≥2 touches → key zone)
  ├─ Trend / traps / flips / gaps
  │
  ▼
engine.prepare()                        ← Builds prompts (no API call)
  ├─ system_prompt: 7 Brooks reference files + JSON schema
  ├─ user_prompt: OHLCV bars + algorithmic context
  └─ metadata: data range, current price, ATR
  │
  ▼
Dashboard (Phase 1 — Progress Loading)
  ├─ st.status() pipeline: connect → fetch → algo
  ├─ Saves prompts for agent consumption
  └─ Enters "Waiting for Agent" state with partial dashboard
  │
  ▼
Agent (Claude Code)                     ← Reads prompts, generates analysis
  ├─ Reasoning using its own model (no external API key needed)
  └─ Produces structured JSON matching output schema
  │
  ▼
engine.finalize(agent_output)           ← Parses agent JSON → GoldAnalysis
  │
  ▼
Dashboard (Phase 2 — Full Render)
  ├─ Detects analysis_result.json via file watch
  └─ Renders complete 9-section dashboard with AI narratives
```

### Key Architectural Decisions

- **Agent-driven LLM**: No external LLM API keys required — the agent uses its own model
- **Deterministic algorithm layer**: Swing detection, zone clustering, trap identification → all pure Python, no randomness
- **Strict data contract**: 10 Python dataclasses (`schema.py`) define the exact JSON contract between agent and dashboard
- **Two-phase dashboard**: Phase 1 renders immediately with algorithmic data; Phase 2 unlocks when the agent finishes

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **MT5 terminal** (optional) — required for live data only; offline CSV mode works anywhere
- **No external LLM API key** — the agent's built-in model handles all reasoning
- Windows required for MT5 (native COM bridge); Linux/macOS fine for non-MT5 usage

### Installation

```bash
pip install -r assets/requirements.txt
```

### Dashboard-First Workflow (Recommended)

```bash
# Step 1: Start the dashboard — it handles data + algorithm immediately
cd skills/gold-analysis
streamlit run scripts/dashboard.py
# → Opens at http://localhost:8501
# → Shows real-time progress: connect → fetch → algorithmic analysis
# → Enters "Waiting for Agent" state with partial dashboard

# Step 2: Agent reads prompts and generates LLM narratives
# → Reads prompts/system_prompt.md and prompts/user_prompt.md
# → Generates JSON analysis matching the output schema
# → Saves to analysis_result.json

# Step 3: Dashboard auto-detects the result and renders fully
# → Full 9-section dashboard with AI narratives
```

### Prepare-First Workflow (Alternative — batch/CLI)

```bash
# Generate analysis first, then view
python scripts/analysis_engine.py --days 3 --prompts-only
# → Agent generates JSON → saves analysis_result.json
streamlit run scripts/dashboard.py  # Reads the saved result
```

### Offline Demo (No MT5 Required)

The system automatically falls back to `assets/sample_data.csv` (~900 M5 bars, ~3 trading days) when MT5 is unavailable. The dashboard clearly indicates "Offline (CSV)" mode.

---

## Architecture

| Layer | Module | Output | Deterministic |
|-------|--------|--------|:---:|
| **Data** | `data_fetcher.py` | pandas DataFrame | ✅ |
| **Algorithm** | `price_action_analyzer.py` | dict with 9 analysis keys | ✅ |
| **Prompt Builder** | `llm_analyzer.py` (build_prompt) | system_prompt + user_prompt + metadata | ✅ |
| **LLM Reasoning** | Agent (Claude Code) | Structured JSON | ❌ |
| **Response Parser** | `llm_analyzer.py` (parse_response) | GoldAnalysis dataclass | ✅ |
| **Render** | `dashboard.py` + `dashboard_styles.py` | HTML/CSS | ✅ |

### Separation of Concerns

The critical insight of v4: **llm_analyzer.py makes zero network calls**. It is a pure
prompt-builder and response-parser. The agent sits between these two halves:

```
build_prompt(df, algo_result)   →   Agent (reads prompts, generates JSON)   →   parse_response(text, df)
```

No external API key, no vendor lock-in, no rate limits — the agent uses whatever model is
powering the current Claude Code session.

---

## Dashboard

### Liquid Metal Theme

Dark financial-terminal aesthetic with glass-morphism cards, neon glow animations, and gold-accented typography.

| Element | Style |
|---------|-------|
| Background | Deep cosmic navy `#080c14` with radial gradients + grid texture |
| Cards | Glass-morphism (`backdrop-filter: blur(12px)`) |
| Primary | Gold `#e2b04a` |
| Accent | Cyan `#00c8e8` |
| Bullish | Green `#00d978` |
| Bearish | Red `#ff3d5a` |
| Fonts | Rajdhani (titles) · Noto Sans SC (Chinese body) · JetBrains Mono (data) |

### 9 Rendering Sections

1. **Price Ticker** — Current price, ATR, MT5 status, data range
2. **Multi-Timeframe Display** — M5 / M15 / H1 / H4 direction badge cards
3. **Price Chart** — Plotly OHLCV with zone lines and bar mark annotations
4. **Daily Summaries** — Date, OHLCV, range%, body direction table
5. **Market Structure Card** — State badge, HH/HL/LL/LH evidence, swing points
6. **Key Price Zones** — Lower/upper, role, strength, touches, position
7. **Trading Signals** — Signal tags with evidence descriptions
8. **Trade Reference** — Direction, entry zone, stop, targets with reasoning
9. **AI Market Narratives** — 5+ Chinese narrative sections (agent-generated)

### Sidebar Controls

- Analysis lookback: 1 / 2 / 3 / 5 / 7 days
- Auto-refresh toggle + interval (10m / 15m / 30m / 1h / 4h)
- Manual Refresh & Reconnect buttons
- Session-state caching for performance

---

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `GOLD_KNOWLEDGE_DIR` | `references/` | Brooks knowledge base directory (override path) |
| `GOLD_MT5_SYMBOL` | `XAUUSD` | Trading symbol (change for different brokers) |
| `GOLD_LOOKBACK_DAYS` | `3` | Days of M5 data to fetch |
| `GOLD_CACHE_STALE_SECONDS` | `300` | Data cache TTL in seconds |

Constants in `config.py` (not env-configurable): `TIMEFRAME = "M5"`, `M5_BARS_PER_DAY = 300`, `MT5_TZ_OFFSET_HOURS = 5`.

---

## CLI Reference

```bash
# Full analysis (algorithm + agent prompts, requires MT5)
python scripts/analysis_engine.py --days 3 --print

# Algorithm-only (no agent prompts, no API key needed)
python scripts/analysis_engine.py --days 5 --skip-agent --print

# Generate prompts only (save to files for manual agent consumption)
python scripts/analysis_engine.py --days 3 --prompts-only --output-dir ./prompts

# Save analysis to JSON
python scripts/analysis_engine.py --days 3 --output result.json

# Standalone price action analysis on CSV
python scripts/price_action_analyzer.py data.csv
```

---

## Project Structure

```
gold-analysis/
├── SKILL.md                          # Complete 16-section skill documentation
├── README.md                         # ← You are here (English)
├── README.zh.md                      # Chinese README
├── finalize.py                       # Standalone finalize: agent output → analysis_result.json
├── gen_analysis_live.py              # Live agent-driven analysis runner
│
├── scripts/                          # 10 Python modules
│   ├── __init__.py                   # sys.path init + .env auto-loading
│   ├── config.py                     # Global configuration (env vars + constants)
│   ├── schema.py                     # 10 dataclasses + strict JSON output schema
│   ├── data_fetcher.py               # MT5 data retrieval, caching, multi-TF support
│   ├── price_action_analyzer.py      # Pure-algorithm structure extraction (884 lines, 11 functions)
│   ├── llm_analyzer.py               # build_prompt() + parse_response() — zero API calls
│   ├── analysis_engine.py            # Orchestration: fetch → algo → prepare/finalize → GoldAnalysis
│   ├── gen_analysis.py               # CLI entry point for standalone analysis generation
│   ├── dashboard.py                  # Streamlit web dashboard (18 render functions)
│   └── dashboard_styles.py           # Liquid Metal financial terminal CSS (677 lines)
│
├── references/                       # 7 Al Brooks methodology documents
│   ├── 01-market-structure.md        # HH/HL/LL/LH framework, trend/range/transition
│   ├── 02-breakouts.md               # Strong/weak/failed breakouts, breakout tests
│   ├── 03-mm-traps.md                # Fake breakouts, weak retracements, triple tests
│   ├── 04-sr-flips.md                # Support/resistance flips, zone strength grading
│   ├── 05-measured-moves.md          # Spike/range/wedge-based target projection
│   ├── 06-trend-maturity.md          # Three-stage lifecycle, climax recognition
│   └── 07-key-reversal-signals.md    # Reversal hierarchy, confirmation rules
│
├── assets/
│   ├── .env.example                  # Configuration template (GOLD_* env vars)
│   ├── requirements.txt              # Python package dependencies
│   └── sample_data.csv               # Offline demo data (~900 M5 bars)
│
├── evals/                            # Test suite
│   ├── conftest.py                   # Shared fixtures
│   ├── test_data_fetcher.py          # DataFetcher init, cache, mock fetch
│   └── test_llm_analyzer.py          # build_prompt() structure, parse_response()
│
└── prompts/                          # Runtime prompt storage (gitignored)
    ├── system_prompt.md              # Brooks methodology + JSON schema
    └── user_prompt.md                # OHLCV bars + algorithmic context
```

---

## Al Brooks Methodology

The seven reference documents encode core price action principles that drive the analysis:

| # | Document | Core Concept |
|---|----------|-------------|
| 01 | Market Structure | HH+HL confirms uptrend; LL+LH confirms downtrend; mixed = range/transition |
| 02 | Breakouts | "Always assume a breakout will fail unless it shows strength" |
| 03 | MM Traps | "Identify who is trapped — trapped traders fuel the next move" |
| 04 | SR Flips | Old support → new resistance (and vice versa); more touches = stronger flip |
| 05 | Measured Moves | Spike projection, gap magnets, trading range / wedge targets |
| 06 | Trend Maturity | Early (shallow pullbacks) → Mid (deeper, channel evolves) → Late (climax) |
| 07 | Key Reversals | Climax reversal (strongest) → wedge/3-push → double top/bottom → O/I bars |

> **Golden Rule**: "Never anticipate — wait for the signal bar to be broken by the entry bar."

---

## Data Contract

The complete JSON contract between agent and dashboard defined in `schema.py`:

| Dataclass | Purpose |
|-----------|---------|
| `GoldAnalysis` | Top-level container — complete analysis response |
| `MarketStructure` | State (uptrend/downtrend/range/transition), confidence, swing evidence |
| `TrendMaturity` | Lifecycle stage (early/mid/late), retrace depth, climax signs |
| `PriceZone` | Price range with touches, role (support/resistance/mixed), strength |
| `PriceSignal` | Trading signal with type (8 enum values), direction, evidence, confidence |
| `DailySummary` | One day's OHLCV + range% + body direction (bullish/bearish) |
| `TradeReference` | Direction, entry zone, stop, targets, reasoning, invalidation conditions |
| `NarrativeSection` | AI narrative chapter (title, content, icon, highlight) |
| `ChartData` | Complete OHLCV arrays + zones + bar marks for Plotly rendering |
| `BarMark` | Annotated candle on chart (bar type + price + note) |
| `PricePoint` | Single swing point (time, price, SH/SL type) |

---

## License

MIT

---

## Related

- [Al Brooks Price Action (4-book series)](https://www.brookstradingcourse.com/)
- [MetaTrader 5 Python Integration](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code)
