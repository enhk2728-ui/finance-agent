---
name: gold-analysis
description: Gold XAUUSD price action analysis using Al Brooks methodology. Full pipeline from MT5 data acquisition through algorithmic structure extraction and agent-driven narrative generation to Streamlit dashboard rendering. Use when the user wants to analyze gold price action, run the gold trading dashboard, study market structure for XAUUSD, or discuss gold trading strategy.
when_to_use: Gold trading analysis, XAUUSD technical analysis, price action structure detection, market maker trap identification, support/resistance analysis, trend maturity assessment, gold dashboard launch, trading strategy discussion, gold price interpretation
---

# Gold Analysis Skill

Comprehensive XAUUSD price action analysis system integrating MT5 data, Al Brooks
methodology, agent-driven narrative generation, and a Streamlit financial dashboard.

## 1. Overview

Four-stage pipeline from raw market data to rendered dashboard. The LLM reasoning
stage is now **agent-driven**: the analysis engine prepares prompts, the agent
(Claude Code) reads them and generates the analysis using its own model, and the
engine parses the agent's output back into structured data.

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
  ├─ Shows st.status() pipeline: connect → fetch → algo
  ├─ Saves prompts to prompts/*.md (for agent)
  ├─ Saves intermediate_result.json (for partial display)
  └─ Enters "Waiting for Agent" state with partial dashboard
  │
  ▼
Agent (Claude Code)                     ← Reads prompts, generates analysis
  ├─ Reads prompts/system_prompt.md and prompts/user_prompt.md
  ├─ Reasons using its own model (no external API key needed)
  └─ Produces JSON matching LLM_OUTPUT_SCHEMA
  │
  ▼
engine.finalize(agent_output)           ← Parses agent JSON → GoldAnalysis
  │
  ▼
  GoldAnalysis (strict JSON via schema.py, 10 dataclasses)
      │
      ▼
Dashboard (Phase 2 — Full Render)
  ├─ Detects analysis_result.json via file watch
  ├─ Clears waiting state → renders all 9 sections
  └─ Auto-refresh support (10m/15m/30m/1h/4h)
```

The AnalysisEngine (`scripts/analysis_engine.py`) orchestrates stages 1-3.
The dashboard (`scripts/dashboard.py`) handles stage 4 and auto-refresh.

## 2. Quick Start

```bash
pip install -r assets/requirements.txt
```

**Dashboard-First Workflow (Recommended):**

```bash
# Step 1: Start dashboard — it immediately shows header + sidebar,
# then runs the loading pipeline with real-time progress display
cd skills/gold-analysis
streamlit run scripts/dashboard.py
# → Dashboard opens at http://localhost:8501
# → Shows progress: connect → fetch data → algorithmic analysis
# → Enters "等待 Agent 分析" state with partial dashboard (chart, zones, structure)
# → Prompts auto-saved to prompts/system_prompt.md and prompts/user_prompt.md

# Step 2: Agent (Claude Code) reads prompts and generates analysis
# → Agent reads prompts/system_prompt.md and prompts/user_prompt.md
# → Agent generates JSON analysis matching LLM_OUTPUT_SCHEMA
# → Agent calls engine.finalize() and writes analysis_result.json

# Step 3: Dashboard auto-detects analysis_result.json
# → Clears waiting state → renders full 9-section dashboard with narratives
```

**Alternative (Prepare-First for batch/CLI):**

```bash
# Step 1: Generate analysis (agent reads prompts, generates JSON)
cd skills/gold-analysis
python scripts/analysis_engine.py --days 3 --prompts-only
# → agent reads system_prompt + user_prompt
# → agent generates analysis JSON matching LLM_OUTPUT_SCHEMA
# → agent saves result to analysis_result.json

# Step 2: Launch dashboard (reads pre-generated analysis)
streamlit run scripts/dashboard.py  # → http://localhost:8501
```

**Data source priority:**
1. `analysis_result.json` — agent-pregenerated complete analysis (LLM narratives + chart data)
2. Real-time algorithm analysis — if MT5 is connected and no JSON file exists
3. `assets/sample_data.csv` — offline fallback when MT5 is unavailable

No external LLM API key is required — the agent uses its own model.

## 3. Prerequisites

- Python 3.10+
- **MT5 terminal** (optional) — required for live data; offline/CSV mode available
- **No external LLM API key needed** — analysis uses the agent's built-in model
- Windows required for MT5 (native COM); Linux/macOS fine for non-MT5 usage
- Google Fonts CDN access (Rajdhani, Noto Sans SC, JetBrains Mono loaded at runtime)

## 4. Architecture

### Component Diagram

```
┌──────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ data_fetcher │───▶│ price_action_analyzer │───▶│  analysis_engine     │
│  (MT5→DF)   │    │   (swings/zones/etc)  │    │  prepare()/finalize()│
└──────────────┘    └──────────────────────┘    └──────────┬───────────┘
       ▲                                                   │
       │              AnalysisEngine                       ▼
       │         (orchestrates all three)           ┌──────────────┐
       └────────────────────────────────────────────│    Agent     │
                                                    │ (Claude Code)│
                                                    └──────┬───────┘
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │  dashboard   │
                                                    │ (Streamlit)  │
                                                    └──────────────┘
```

### Separation of Concerns

| Layer | Module | Output | Deterministic? |
|-------|--------|--------|----------------|
| Data | data_fetcher.py | pandas DataFrame | Yes |
| Algorithm | price_action_analyzer.py | dict with 9 keys | Yes |
| Prompt Building | llm_analyzer.py (build_prompt) | dict {system_prompt, user_prompt, metadata} | Yes |
| LLM Reasoning | Agent (Claude Code) | JSON string | No |
| Response Parsing | llm_analyzer.py (parse_response) | GoldAnalysis | Yes |
| Render | dashboard.py + dashboard_styles.py | HTML/CSS | Yes |

### Agent-Driven Architecture

The key architectural change: **llm_analyzer.py no longer calls any external LLM API**.
Instead, it provides two pure functions:

- **`build_prompt(df, algo_result)`** — Constructs the system prompt (Brooks references
  + JSON output schema) and user prompt (OHLCV bars + algorithmic context). Returns a
  dict with `system_prompt`, `user_prompt`, and `metadata`. No network calls.

- **`parse_response(text, df)`** — Takes the agent's raw text output, extracts JSON
  from it, validates against the schema, and converts it into a `GoldAnalysis`
  dataclass. Returns `Optional[GoldAnalysis]`.

The **agent** (this Claude Code session) sits between these two functions:
1. Call `engine.prepare()` to get the prompts
2. Read the `system_prompt` and `user_prompt`
3. Generate the analysis JSON using its own model
4. Pass the output to `engine.finalize()` to get `GoldAnalysis`

### Data Contract

`schema.py` defines the complete JSON contract as Python dataclasses. Every
field the agent outputs and the dashboard renders is typed here. The top-level
`GoldAnalysis` aggregates all sub-models:

```
GoldAnalysis
├── MarketStructure      (state, HH/HL/LL/LH, swing points)
├── TrendMaturity        (stage, retrace depth, channel slope, climax signs)
├── PriceZone[]          (lower/upper/mid, touches, role, strength)
├── PriceSignal[]        (type, direction, title, description, price level)
├── DailySummary[]       (date, OHLCV, range%, body direction)
├── TradeReference       (direction, entry zone, stop, targets, reasoning)
├── NarrativeSection[]   (title, content, icon, highlight)
├── ChartData            (OHLCV arrays, zones, bar marks)
├── PricePoint           (time, price, type SH/SL)
└── BarMark              (time, bar_type, price, note)
```

### Rendering Rule (CRITICAL)

- **HTML containers/tables/badges** → `st.markdown(html, unsafe_allow_html=True)` — only for trusted data (numbers, enums, dataclass fields)
- **Agent-generated text** → independent `st.markdown(content)` — NEVER inject agent text into HTML strings
- **Charts** → `st.plotly_chart(fig)`

## 5. Stage 1 — Data Acquisition

File: `scripts/data_fetcher.py`

### Class DataFetcher(symbol="XAUUSD", stale_seconds=300)

**MT5 Connection** (`_connect`):
1. Call `mt5.initialize()` — fail gracefully if MT5 not running
2. Try `mt5.symbol_info("XAUUSD")`
3. If not found, search variants: `symbols_get(group="*XAUUSD*")` then `*GOLD*`
4. Auto-select first available (handles broker suffixes: `.`, `m`, `.i`)
5. Print terminal info for diagnostics

**Data Fetching** (`fetch(timeframe, count)`):
- Strategy 1: `mt5.copy_rates_from_pos(symbol, tf, 0, count)` — fastest
- Strategy 2: `mt5.copy_rates_from(symbol, tf, start, count)` — date range fallback
  - M5 → 3 days back, M15 → 7 days, H1 → 30 days, H4 → 60 days
- Returns `pd.DataFrame` with columns: `[time, open, high, low, close]`
- Timezone: MT5 server time → Beijing time (+5 hours offset)

**Caching**:
- Per-timeframe in-memory cache (`_cache` dict)
- Staleness: 300 seconds (configurable via `GOLD_CACHE_STALE_SECONDS`)
- `get_cached(timeframe)` → returns cached if fresh, else calls `fetch()`
- `has_enough_data(timeframe, min_bars=50)` → quick availability check

**Multi-timeframe**: M5, M15, H1, H4 (via TIMEFRAME_M5/M15/H1/H4 constants)

**Offline mode**: When MT5 is unavailable, the system automatically falls back to
`assets/sample_data.csv` — a pre-saved snapshot of ~900 M5 bars (~3 trading days).
The dashboard shows "离线 (CSV)" mode and uses this historical data for demonstration.

**When MT5 is unavailable**, the agent should:
1. Load from `assets/sample_data.csv` automatically (handled by `DataFetcher._try_offline()`)
2. Note in the analysis that data is from a snapshot (not live)
3. Invite the user to connect MT5 for real-time analysis

## 6. Stage 2 — Algorithmic Analysis

File: `scripts/price_action_analyzer.py` (884 lines, pure Python, no LLM)

All analysis is deterministic. No API calls, no randomness.

### Function Reference

**`find_swings(df, lookback=5)`** — Swing Highs/Lows
- A swing high: `high[i]` is max of `[i-lookback, i+lookback]`
- A swing low: `low[i]` is min of `[i-lookback, i+lookback]`
- Returns list of `{idx, time, price, type: 'SH'|'SL'}` sorted by time

**`filter_significant_swings(swings, min_range_pct=0.003)`** — Noise Filter
- Keeps only swings where the preceding opposite swing's amplitude >= 0.3%
- For XAUUSD at ~4700: 0.3% ~ 14 points
- Filters out micro-fluctuations while preserving meaningful turning points

**`detect_trend(swings)`** — Trend Direction
- Uptrend: last 2 SH form HH AND last 2 SL form HL
- Downtrend: last 2 SL form LL AND last 2 SH form LH
- Range: any other combination (HH+LL, LH+HL, etc.)
- Returns: `{direction, hh, hl, ll, lh, last_sh, prev_sh, last_sl, prev_sl}`

**`find_price_zones(swings, tolerance_pct=0.0015, min_touches=2)`** — Support/Resistance
- Greedy clustering: sort swings by price, group if gap <= tolerance
- tolerance_pct=0.0015 (0.15%) ~ 7 points at XAUUSD 4700
- Role assignment: all SH → resistance, all SL → support, mixed → flip zone
- Returns list of `{lower, upper, mid, touches, role, strength, points[]}`

**`detect_sr_flips(zones, swings)`** — Support<->Resistance Flips
- A zone with `role='mixed'` where earliest and latest touch types differ
- Returns: `{..., flip_type: 'support_to_resistance'|'resistance_to_support'}`

**`detect_gaps(df, gap_threshold_pct=0.002)`** — Price Gaps
- Intraday gap: current open outside previous bar's high-low range
- Cross-session gap: time gap > 1 hour between consecutive bars
- Threshold: 0.2% ~ 9 points at XAUUSD 4700

**`detect_mm_traps(df, swings, zones)`** — Market Maker Traps
Three patterns detected:
1. **Fake breakout**: price breaks zone then immediately reverses back inside
2. **Weak retracement**: retracement < 38.2% of prior leg (shows no counter-pressure)
3. **Triple test failure**: zone tested >=3 times without breaking (pent-up energy)

### Main Entry Points

**`full_report(df)`** — Runs all detectors, returns dict with 9 keys:
```python
{
    'report': str,        # Human-readable Chinese text report
    'df': DataFrame,      # Input data
    'swings': list,       # All swing points
    'sig_swings': list,   # Filtered significant swings
    'trend': dict,        # Trend structure
    'zones': list,        # Key price zones
    'flips': list,        # SR flips detected
    'gaps': list,         # Price gaps
    'traps': list         # MM trap signals
}
```

**`prepare_llm_context(result)`** — Formats the `full_report` dict into structured
Chinese text for the agent's user prompt (daily summaries, trend, swings, zones,
flips, gaps, traps).

## 7. Stage 3 — Agent-Driven Analysis

Files: `scripts/llm_analyzer.py`, `scripts/analysis_engine.py`

The LLM analysis stage is now split into two halves with the agent sitting
in the middle. llm_analyzer.py no longer makes any network calls — it is a
pure prompt-builder and response-parser.

### build_prompt(df, algo_result) -> dict

Constructs the full prompt context that the agent needs. Returns a dict with
three keys:

```python
{
    'system_prompt': str,   # Brooks methodology references + JSON output schema
    'user_prompt': str,     # OHLCV bar data + algorithmic analysis context
    'metadata': dict        # Data range, current price, ATR, bar count, etc.
}
```

**system_prompt contents:**
1. All 7 `references/*.md` files concatenated (market structure, breakouts,
   MM traps, SR flips, measured moves, trend maturity, key reversal signals)
2. The `LLM_OUTPUT_SCHEMA` from `schema.py` — strict JSON format specification
3. Instructions for the agent: role, methodology to apply, output requirements

**user_prompt contents:**
1. 24-hour bar-by-bar OHLCV data with bar-type tagging (大阳/大阴/十字星/长尾线/强趋势棒/外包棒/内包棒)
2. Daily OHLCV summaries (date, OHLCV, range%, body direction)
3. Algorithmic context: trend structure, swing points (up to 40), price zones,
   market maker traps, SR flips

**metadata contents:**
- `data_range`: (start_time, end_time) of the price data
- `current_price`: latest close price
- `atr`: average true range for volatility context
- `bar_count`: number of bars in the dataset
- `symbol`, `timeframe`: instrument identifiers

### Agent Workflow (Claude Code)

The agent is responsible for the LLM reasoning step. The recommended workflow
is **dashboard-first**: start the dashboard immediately, let it show loading
progress while it fetches data and runs algorithmic analysis, then have the
agent generate the LLM narrative while the dashboard displays partial results.

**Recommended workflow (dashboard-first):**

1. **Start dashboard immediately** — `streamlit run scripts/dashboard.py`
   - The dashboard launches instantly, showing the header and sidebar
   - A progress pipeline (`st.status()`) shows real-time loading stages:
     - 📡 正在连接数据源
     - 📊 正在获取 XAUUSD M5 行情数据
     - 🔍 正在运行价格行为算法分析
   - The dashboard saves algorithm results to `intermediate_result.json`
     and prompts to `prompts/system_prompt.md` and `prompts/user_prompt.md`

2. **Dashboard enters waiting state** — After algorithm analysis completes:
   - Shows partial dashboard (price ticker, chart, zones, structure) with
     real data from the algorithm stage
   - Displays "⏳ 等待 Agent 生成 LLM 市场解读" status card
   - Indicates whether prompts are ready for agent consumption
   - Polls for `analysis_result.json` to detect agent completion

3. **Agent reads prompts** — From `prompts/system_prompt.md` and
   `prompts/user_prompt.md`:
   - system_prompt: Brooks references + JSON output schema
   - user_prompt: OHLCV bars + algorithmic analysis context

4. **Agent generates analysis** — Using its own model, reasons through:
   - Market structure assessment (uptrend/downtrend/range/transition)
   - Trend maturity evaluation (early/mid/late with climax detection)
   - Key price zone identification with strength grading
   - Signal detection with evidence (fake breakouts, traps, flips, etc.)
   - Narrative synthesis (5+ sections in Chinese)
   - Trade reference construction (direction, entry, stop, targets)

5. **Output JSON** — The agent produces a JSON object strictly matching
   `LLM_OUTPUT_SCHEMA`. The JSON must be the final output with no prefix
   or suffix text.

6. **Write analysis_result.json** — Save the complete analysis using
   `engine.finalize(agent_output)` and write to `analysis_result.json`
   (see Section 11 for the exact saving code).

7. **Dashboard auto-detects** — The dashboard's file-watch mechanism
   detects `analysis_result.json`, clears the waiting state, and
   renders the full 9-section dashboard with LLM narratives.

**Alternative workflow (prepare-first, for batch/CLI usage):**

1. **Receive prompts** — Call `engine.prepare()` which runs data fetch +
   algorithmic analysis + `build_prompt()`, returning the three-prompt dict

2. **Read and understand** — The agent reads both `system_prompt` and
   `user_prompt`

3. **Generate analysis** — Same reasoning process as above

4. **Finalize** — Pass the agent's output to `engine.finalize(agent_output)`
   to get a `GoldAnalysis` dataclass

### parse_response(text, df) -> Optional[GoldAnalysis]

Parses the agent's raw text output into a structured `GoldAnalysis` object:

1. **JSON extraction** — Tries code block first (```json ... ```), falls back
   to first `{` to last `}` in the text
2. **JSON repair** — 5-level fallback: direct parse → BOM strip → trailing
   comma fix → array trailing comma fix → raw_decode
3. **Schema validation** — Validates against `GoldAnalysis` dataclass structure
4. **Type conversion** — Maps the parsed dict to `GoldAnalysis` via
   `_json_to_analysis(data)`
5. **Metadata enrichment** — Fills symbol, timeframe, generated_at,
   data_range, current_price, ATR, chart data computed from `df`

If parsing fails at any stage, returns `None`. The caller should handle this
by falling back to an algorithm-only GoldAnalysis.

### analysis_engine.py Orchestration

The `AnalysisEngine` class provides two key methods that bracket the agent:

**`engine.prepare(days=3) -> dict`**
1. Fetches M5 data via `DataFetcher`
2. Runs `price_action_analyzer.full_report(df)`
3. Calls `llm_analyzer.build_prompt(df, algo_result)`
4. Returns the prompt dict `{system_prompt, user_prompt, metadata}`

**`engine.finalize(agent_output: str) -> Optional[GoldAnalysis]`**
1. Calls `llm_analyzer.parse_response(agent_output, df)`
2. Returns the `GoldAnalysis` object (or `None` on parse failure)

## 8. Stage 4 — Dashboard Rendering

Files: `scripts/dashboard.py` + `scripts/dashboard_styles.py`

### Two-Phase Dashboard Architecture (v4.1)

The dashboard now uses a **two-phase rendering** approach with progress tracking:

**Phase 1 — Progress Pipeline (instant, no data needed):**
- Renders header bar and sidebar controls immediately
- Uses `st.status()` to show real-time pipeline stages:
  - 📡 正在连接数据源 (MT5 / offline CSV)
  - 📊 正在获取 XAUUSD M5 行情数据
  - 🔍 正在运行价格行为算法分析
  - ⏳ 等待 Agent 生成 LLM 解读 (when no pre-generated analysis exists)
- Saves prompts to `prompts/system_prompt.md` and `prompts/user_prompt.md`
- Saves intermediate algorithm results to `intermediate_result.json`

**Phase 2 — Full Render (after data is ready):**
- If `analysis_result.json` exists → loads and renders complete 9-section dashboard
- If no agent analysis yet → renders partial dashboard (chart, zones, structure)
  with "等待 Agent" status card + file watch polling
- `_watch_for_analysis_file()` polls for `analysis_result.json` appearing
  and triggers auto-reload when detected

```python
# Inside dashboard.py main() — simplified two-phase flow
engine = AnalysisEngine()

# Phase 1: Progress pipeline with st.status()
with st.status("正在启动黄金分析引擎…", expanded=True) as status:
    status.update(label="📡 正在连接数据源...")
    # … data fetch + algorithm analysis …
    status.update(label="✅ 分析就绪" if pregenerated else
                   "⏳ 等待 Agent 生成 LLM 解读", state="running")

# Phase 2: Render
if analysis and has_narratives:
    render_full_dashboard(analysis)
else:
    render_partial_dashboard(analysis)
    _watch_for_analysis_file()  # polls for analysis_result.json
```

### Data Source Priority (unchanged)

1. `analysis_result.json` — agent-pregenerated complete analysis (LLM narratives + chart data)
2. Real-time algorithm analysis — if MT5 is connected and no JSON file exists
3. `assets/sample_data.csv` — offline fallback when MT5 is unavailable

### Rendering Pipeline (18 functions)

The `main()` function in `dashboard.py` executes:

```
render_price_ticker()        → 行情条: current price, ATR, MT5 status, data range
render_multi_tf_display()    → 多周期方向: M5/M15/H1/H4 direction badge cards
render_chart()               → Plotly 走势图: price line + zone hlines + bar marks
render_daily_summaries()     → 每日总览表: date, OHLCV, range%, body direction
render_structure_card()      → 市场结构卡: state badge, HH/HL/LL/LH, swing points
render_zones_table()         → 关键价位表: lower-upper, role, strength, touches, position
render_signals()             → 交易信号: signal tags (HTML) + descriptions (markdown)
render_trade_reference()     → 交易参考卡: direction, entry, stop, targets (HTML)
render_narratives()          → AI 市场解读: 7 section cards (HTML) + content (markdown)
```

### Sidebar Controls
- Analysis days: 1/2/3/5/7 (default 3)
- Auto-refresh toggle + interval selector (10m/15m/30m/1h/4h)
- Manual "Refresh" and "Reconnect" buttons
- Session-state caching (avoids redundant computation on rerun)

### Liquid Metal Theme (v4.0)

Dark financial terminal aesthetic:
- Background: `#080c14` deep cosmic navy + radial gradients + grid texture
- Cards: glass-morphism (`backdrop-filter: blur(12px)`, semi-transparent backgrounds)
- Colors: gold `#e2b04a` (primary), cyan `#00c8e8` (accent), green `#00d978` (bullish), red `#ff3d5a` (bearish), amber `#f08c2a` (neutral)
- Fonts: Rajdhani (titles, uppercase, tight letter-spacing), Noto Sans SC (body, Chinese), JetBrains Mono (data, numbers, monospace)
- Effects: neon glow animations (live status dot), hover lift, gradient borders, custom scrollbars

### Error States
- **MT5 disconnected**: Warning card with reconnect instructions
- **Insufficient data** (<30 bars): Warning with MT5 chart-open instructions
- **Agent parse failure**: Falls back to algorithm-only GoldAnalysis with a
  highlighted warning narrative ("分析生成失败，请重试...")

## 9. Configuration Reference

All settings via environment variables (`.env` file or system env).

| Env Var | Default | Description |
|---------|---------|-------------|
| `GOLD_KNOWLEDGE_DIR` | references/ | Extra Brooks book files (optional override) |
| `GOLD_MT5_SYMBOL` | XAUUSD | Trading symbol (change for different brokers) |
| `GOLD_LOOKBACK_DAYS` | 3 | Days of M5 data to fetch |
| `GOLD_CACHE_STALE_SECONDS` | 300 | Data cache TTL in seconds |

Constants in `config.py` (not env-configurable, edit file to change):
- `SYMBOL = "XAUUSD"`, `TIMEFRAME = "M5"`
- `M5_BARS_PER_DAY = 300`, `MT5_TZ_OFFSET_HOURS = 5`

Note: There are no LLM API configuration variables. The agent uses its own
model and API key automatically. No `GOLD_LLM_*` environment variables needed.

## 10. CLI Usage

```bash
# Full analysis (algorithm + agent prompts, requires MT5)
cd skills/gold-analysis
python scripts/analysis_engine.py --days 3 --print

# Algorithm-only analysis (no agent prompts, no API key needed)
python scripts/analysis_engine.py --days 5 --skip-agent --print

# Generate prompts only (save to files for manual agent consumption)
python scripts/analysis_engine.py --days 3 --prompts-only --output-dir ./prompts
# Writes: ./prompts/system_prompt.md and ./prompts/user_prompt.md

# Run engine prepare + print prompts to stdout
python scripts/analysis_engine.py --days 3 --prompts-only

# Save analysis to JSON file
python scripts/analysis_engine.py --days 3 --output result.json

# View help
python scripts/analysis_engine.py --help

# Standalone price action analysis on CSV
python scripts/price_action_analyzer.py data.csv
```

## 11. Agent Usage Guide

This section explains how an agent (Claude Code) should use the gold analysis
pipeline to produce a complete analysis.

### Dashboard-First Workflow (Recommended)

This is the preferred approach — the dashboard starts immediately and shows
progress in real-time:

**Step 1: Launch the dashboard (it handles data and algorithm itself)**

```bash
cd skills/gold-analysis
streamlit run scripts/dashboard.py  # → http://localhost:8501
```

The dashboard will:
- Show header + sidebar immediately
- Run a progress pipeline (st.status): connect → fetch → algorithmic analysis
- Save prompts to `prompts/system_prompt.md` and `prompts/user_prompt.md`
- Display a partial dashboard (chart, zones, structure) with live data
- Show "⏳ 等待 Agent 生成 LLM 市场解读" status

**Step 2: Agent reads prompts and generates analysis**

Read the prompts the dashboard saved:
- `Read(skills/gold-analysis/prompts/system_prompt.md)` — Brooks methodology + JSON schema
- `Read(skills/gold-analysis/prompts/user_prompt.md)` — OHLCV bars + algorithmic context

Then generate the analysis JSON matching `LLM_OUTPUT_SCHEMA`.

**Step 3: Agent finalizes and writes result**

```python
import json
from pathlib import Path
from scripts.analysis_engine import AnalysisEngine

engine = AnalysisEngine()
# engine needs the data context — load from intermediate result
intermediate = Path("intermediate_result.json")
if intermediate.exists():
    data = json.loads(intermediate.read_text(encoding="utf-8"))
    # Re-prepare to set engine state
    engine.prepare(days=data.get("_lookback_days", 3))

# Parse agent's output
agent_json_output = '{"symbol": "XAUUSD", ...}'  # the JSON you generated
analysis = engine.finalize(agent_json_output)

if analysis:
    # Write the result for the dashboard to detect
    skill_root = Path(".")
    result = {
        "symbol": analysis.symbol,
        "timeframe": analysis.timeframe,
        "generated_at": analysis.generated_at,
        "current_price": analysis.current_price,
        "atr": analysis.atr,
        "data_range": analysis.data_range,
        "raw_analysis": analysis.to_dict(),
        "chart": analysis.chart.to_dict() if analysis.chart else {},
    }
    (skill_root / "analysis_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("✅ analysis_result.json saved — dashboard will auto-detect and render")
else:
    print("❌ Analysis generation failed")
```

**Step 4: Dashboard auto-detects and renders**

The dashboard's `_watch_for_analysis_file()` loop detects
`analysis_result.json`, clears the waiting state, and renders the
full 9-section dashboard with LLM narratives.

### Prepare-First Workflow (Alternative, for batch/CLI)

Use this when you need to prepare before launching the dashboard:

```python
from scripts.analysis_engine import AnalysisEngine

engine = AnalysisEngine()

# Step 1 — Prepare: fetch data, run algorithm, build prompts
prompts = engine.prepare(days=3)
# prompts is a dict with:
#   prompts['system_prompt']   — Brooks methodology + JSON schema
#   prompts['user_prompt']     — OHLCV bars + algorithmic context
#   prompts['metadata']        — data range, current price, ATR, etc.

# Step 2 — The agent itself reads:
#   - prompts['system_prompt'] (PROCESS THIS FIRST — it defines the role and schema)
#   - prompts['user_prompt']   (PROCESS THIS SECOND — it contains the market data)
# The agent then generates a JSON analysis matching LLM_OUTPUT_SCHEMA.

# Step 3 — Finalize: parse the agent's output
agent_json_output = '{"symbol": "XAUUSD", ...}'  # from agent's response
analysis = engine.finalize(agent_json_output)

if analysis:
    print(f"Direction: {analysis.direction}")
    print(f"Structure: {analysis.structure.state}")
    for narrative in analysis.narratives:
        print(f"[{narrative.title}] {narrative.content}")
else:
    print("Analysis generation failed — falling back to algorithm-only")
```

### Agent Reasoning Guidelines

When the agent reads the prompts and generates the analysis, it should:

1. **Read system_prompt first** — This contains all Brooks methodology
   references and the exact JSON schema. The agent must internalize these
   rules before analyzing the market data.

2. **Apply Brooks methodology** — Use the frameworks described in the
   reference files (market structure, breakouts, traps, SR flips, measured
   moves, trend maturity, reversal signals) to interpret the algorithmic
   data in the user prompt.

3. **Output strict JSON** — The final output must be pure JSON matching
   `LLM_OUTPUT_SCHEMA`. No markdown wrapping, no prefix/suffix text, no
   explanatory notes outside the JSON structure.

4. **Use Chinese for narratives** — All `NarrativeSection.content` and
   `description` fields should be in Chinese (中文), as the dashboard is
   designed for Chinese-reading traders.

5. **Be evidence-based** — Every signal, zone assessment, and structure
   call must reference specific data from the user prompt (swing points,
   price levels, bar patterns).

### Error Handling

- If the agent cannot parse the market data, it should still produce a valid
  JSON with `structure.state: "range"` and a warning in the first narrative.
- If the agent's output fails `parse_response()`, the system falls back to
  algorithm-only mode (structured data without narrative sections).

### Saving Results

**For dashboard viewing**, save as `analysis_result.json` in the skill root:

```python
import json
from pathlib import Path

skill_root = Path("skills/gold-analysis")
result = {
    "symbol": analysis.symbol,
    "timeframe": analysis.timeframe,
    "generated_at": analysis.generated_at,
    "current_price": analysis.current_price,
    "atr": analysis.atr,
    "data_range": analysis.data_range,
    "raw_analysis": analysis.to_dict(),  # the full GoldAnalysis dict
    "chart": analysis.chart.to_dict() if analysis.chart else {},
}
(skill_root / "analysis_result.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("analysis_result.json saved — dashboard ready to launch")
```

### Launching the Dashboard

After writing `analysis_result.json`, the agent launches the dashboard:

```bash
streamlit run scripts/dashboard.py
```

The dashboard's `main()` function:
1. Checks for `analysis_result.json` first (agent-generated, has full narratives)
2. Falls back to real-time algorithm analysis if no JSON found
3. Falls back to `assets/sample_data.csv` if MT5 is unavailable
4. Renders the complete 9-section display from whichever data source was loaded

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| MT5 not connecting | Terminal not running or XAUUSD chart closed | Auto-fallback to `assets/sample_data.csv` (offline demo data). Connect MT5 for live data. |
| Using offline data | MT5 not available on this machine | `DataFetcher` auto-loads `assets/sample_data.csv`. Note in analysis that data is a snapshot, not live. |
| No offline data available | `sample_data.csv` missing from assets/ | Re-run `python scripts/analysis_engine.py --prompts-only` and save prompts for agent analysis. |
| Data insufficient (<30 bars) | MT5 chart not opened for XAUUSD | Open XAUUSD M5 chart in MT5, wait for bars to load, refresh |
| Agent parse failure | Agent output not valid JSON or schema mismatch | Check agent output format; ensure it matches LLM_OUTPUT_SCHEMA exactly |
| Dashboard won't start | streamlit not installed or port 8501 busy | `pip install streamlit`, check `lsof -i :8501` |
| Import errors | Running from wrong directory | Always run from the skill root (`skills/gold-analysis/`) |
| Fonts not loading | No internet / CDN blocked | Fonts load from Google Fonts CDN; offline: pre-install fonts locally |

## 13. Knowledge Base Index

Seven curated reference files in `references/` encapsulate Al Brooks' price action
methodology. They are loaded at runtime into the agent's system prompt.

1. **01-market-structure.md** — Market states: uptrend (HH+HL), downtrend (LL+LH),
   trading range, transition. Swing point identification rules. The framework for
   reading market structure from pure price.

2. **02-breakouts.md** — Breakout theory: strong vs weak vs failed breakouts (FBO).
   The core Brooks principle: "the market always tries to make every breakout fail."
   Breakout confirmation signals and retest patterns.

3. **03-mm-traps.md** — Market maker trap typology: fake breakouts (price breaks
   level then reverses), weak retracements (<38.2% of prior leg), triple test
   failures (energy builds, release is explosive). The "Always In" concept.

4. **04-sr-flips.md** — Support becomes resistance, resistance becomes support.
   Flip strength grading (strong/medium/weak). Breakout retest as high-probability
   entry. "The more touches a zone has, the stronger its flipped role."

5. **05-measured-moves.md** — Target projection: spike-based measured moves, gap
   magnets, trading range projections, wedge-based targets. Magnet levels: prior
   swing points, round numbers, prior day highs/lows.

6. **06-trend-maturity.md** — Three-stage trend lifecycle: early (shallow pullbacks,
   trade with trend), mid (deeper pullbacks, channel evolves), late/climax (climax
   bars, trend exhaustion). Channel slope evolution as maturity indicator.

7. **07-key-reversal-signals.md** — Reversal signal hierarchy: climax reversal
   (strongest), wedge/three pushes, double top/bottom, outside/inside bars, doji,
   20 gap bars. Confirmation rules: "never anticipate — wait for signal bar to
   be broken by entry bar."

## 14. Trading Methodology Summary

Core Al Brooks concepts for agents to apply when generating analysis:

**Market Structure**: HH+HL confirms uptrend. LL+LH confirms downtrend. Mixed
signals (HH+LL or LH+HL) indicate trading range or transition. Structure always
takes precedence over individual signals.

**Breakouts**: "Always assume a breakout will fail unless it shows strength."
Strength = large bodies, short tails/wicks, follow-through bars. Failed breakouts
often become the best trades — the failure itself is the signal.

**MM Traps**: "Identify who is trapped — trapped traders fuel the next move."
A failed breakout traps breakout traders on the wrong side; their stop-running
drives the reversal. Weak retracements (<38.2%) show the market won't give traders
a good entry — the trend is strong.

**SR Flips**: Old support becomes new resistance (and vice versa). The flip is
confirmed when price tests the flipped side and holds. "The more touches, the
stronger the flip." A zone tested 5+ times that flips is highly significant.

**Measured Moves**: Project spike height from breakout point for magnet targets.
Gap size -> measured move. Trading range height -> breakout projection. Wedge
width -> breakdown target.

**Trend Maturity**: Early trend (shallow pullbacks, tight channel) -> trade with
trend. Mid trend (deeper pullbacks, wider channel) -> trade pullbacks to trend line.
Late trend (climax bars, parabolic moves) -> prepare for reversal, don't add to
position.

**Reversals**: Never anticipate. Wait for the signal bar (shows reversal attempt)
to be broken by the entry bar (confirms reversal). Climax reversals are the
strongest signal. "The first reversal is usually a trap — wait for the test."

## 15. Files Index

```
scripts/__init__.py              — sys.path initialization + .env auto-loading
scripts/config.py                — Global configuration from env vars + constants
scripts/schema.py                — 10 dataclasses + strict JSON Schema for agent output
scripts/data_fetcher.py          — MT5 data retrieval, memory cache, multi-TF support
scripts/price_action_analyzer.py — Pure-algorithm structure extraction (11 functions, 884 lines)
scripts/llm_analyzer.py          — build_prompt() and parse_response() (no API calls)
scripts/analysis_engine.py       — Orchestration: fetch → algo → prepare/finalize → GoldAnalysis
scripts/dashboard.py             — Streamlit web dashboard (18 render functions)
scripts/dashboard_styles.py      — Liquid Metal financial terminal CSS (677 lines)

references/01-market-structure.md    — HH/HL/LL/LH framework, trend/range/transition
references/02-breakouts.md           — Strong/weak/failed breakouts, breakout tests
references/03-mm-traps.md            — Fake breakouts, weak retracements, triple tests
references/04-sr-flips.md            — Support/resistance flips, zone strength grading
references/05-measured-moves.md      — Spike/range/wedge-based target projection
references/06-trend-maturity.md      — Three-stage lifecycle, climax recognition
references/07-key-reversal-signals.md — Reversal hierarchy, confirmation rules

assets/.env.example              — Config template with GOLD_* env vars documented
assets/requirements.txt          — Python package dependencies
assets/sample_data.csv           — Offline demo data: ~900 M5 bars snapshot

evals/conftest.py                — Shared test fixtures (make_ohlc, uptrend/ranging data)
evals/test_data_fetcher.py       — DataFetcher init, cache, mock fetch tests
evals/test_llm_analyzer.py       — build_prompt() structure, parse_response() tests
```

## 16. Schema Reference

Full type hierarchy for `GoldAnalysis` — the JSON contract between agent and dashboard:

| Dataclass | Fields | Purpose |
|-----------|--------|---------|
| **GoldAnalysis** | symbol, timeframe, generated_at, data_range, current_price, atr, spread, direction, multi_tf, structure, trend_maturity, key_zones[], signals[], daily_summaries[], trade_reference, chart, narratives[] | Top-level container — this is the complete API response |
| **MarketStructure** | state (uptrend/downtrend/range/transition), confidence (高/中/低), summary, hh, hl, ll, lh, last_swing_high, last_swing_low | Current market structure with swing point evidence |
| **TrendMaturity** | stage (初期/中期/末期), retrace_depth_pct, channel_slope (平缓/正常/陡峭), climax_signs[], description | Where the trend is in its lifecycle |
| **PriceZone** | lower, upper, mid, touches, role (support/resistance/mixed), strength (强/中/弱), description, points[] | A price range tested multiple times |
| **PriceSignal** | type (8 SignalTypes), direction (bullish/bearish), title, description, price_level, time, confidence | A detected trading signal with evidence |
| **DailySummary** | date, weekday, open, high, low, close, range_pct, body_direction (阳/阴), note | One day's OHLCV summary |
| **TradeReference** | direction (多头/空头/观望), entry_zone, stop_level, target_levels[], reasoning, invalidation | Actionable trade setup |
| **NarrativeSection** | title, content, icon, highlight | One chapter of the AI narrative report |
| **ChartData** | times[], opens[], highs[], lows[], closes[], zones[], marks[] | Complete chart data for Plotly rendering |
| **BarMark** | time, bar_type (大阳/大阴/十字星/长尾线/强趋势棒/外包棒/内包棒), price, note | A marked candle on the chart |
| **PricePoint** | time, price, type (SH/SL) | A single swing point |

**SignalType enum values**: `fake_breakout`, `weak_retrace`, `triple_test_failure`,
`sr_flip`, `wedge`, `double_top_bottom`, `climax_reversal`, `gap`
