# Changelog

## [v4.2] — 2026-05-31

### Added
- `gen_analysis_live.py` — Live agent-driven analysis runner for direct integration
- `finalize.py` — Standalone finalize script for processing agent output JSON
- `prompts/` directory — Runtime prompt storage (system_prompt.md + user_prompt.md)
- Dashboard-first workflow with `st.status()` progress pipeline
- Two-phase dashboard rendering (Phase 1: loading → Phase 2: full render)

### Changed
- **SKILL.md** — Updated workflow docs with dashboard-first + prepare-first dual paths
- **analysis_engine.py** — Added `--prompts-only` CLI flag, improved prompt building
- **dashboard.py** — Simplified two-phase rendering with resilient loading
- **dashboard_styles.py** — Updated styling for progress indicators
- **config.py** — Updated configuration handling
- **data_fetcher.py** — Improved MT5 connection resilience
- **price_action_analyzer.py** — Refined algorithm parameters
- **llm_analyzer.py** — Updated to use agent-driven approach
- **schema.py** — Schema refinements for v4 data structures
- **gen_analysis.py** — Updated for agent-driven workflow

### Fixed
- Dashboard now correctly detects `analysis_result.json` for Phase 2 rendering
- Progress indicators show real-time pipeline stages during data loading

### Architecture
- Agent-driven LLM analysis (no external API key needed)
- Two-phase dashboard: Phase 1 shows algorithmic results immediately, Phase 2 adds LLM narratives
- Separate prompt files enable decoupled agent execution

---

## [v3] — 2026-05-11 (Initial Release)

### Added
- Gold XAUUSD price action analysis skill
- MT5 data fetcher with CSV fallback
- Al Brooks price action algorithm (swings, zones, traps, flips)
- LLM analyzer with structured JSON output
- Streamlit dashboard with 9-section analysis view
- 7 Brooks methodology reference documents
- Evaluation test suite (data_fetcher, llm_analyzer)
