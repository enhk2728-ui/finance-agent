import sys, json, os
sys.path.insert(0, 'scripts')
os.environ['PYTHONIOENCODING'] = 'utf-8'
from analysis_engine import AnalysisEngine
from pathlib import Path

engine = AnalysisEngine()

# Re-prepare to get data context
prompts = engine.prepare(lookback_days=3)
if not prompts:
    print('FAILED: prepare returned None')
    sys.exit(1)

# Read agent JSON from file
agent_json_path = Path('agent_output.json')
if not agent_json_path.exists():
    print('FAILED: agent_output.json not found')
    sys.exit(1)

agent_json = agent_json_path.read_text(encoding='utf-8').strip()

# Finalize
analysis = engine.finalize(agent_json)
if analysis:
    skill_root = Path('.')
    result = {
        'symbol': analysis.symbol,
        'timeframe': analysis.timeframe,
        'generated_at': analysis.generated_at,
        'current_price': analysis.current_price,
        'atr': analysis.atr,
        'data_range': analysis.data_range,
        'raw_analysis': analysis.to_dict(),
    }
    (skill_root / 'analysis_result.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(f'OK: analysis_result.json saved')
    print(f'Price: {analysis.current_price}, Direction: {analysis.direction}')
    print(f'Structure: {analysis.structure.state}, Maturity: {analysis.trend_maturity.stage}')
    print(f'Zones: {len(analysis.key_zones)}, Signals: {len(analysis.signals)}, Narratives: {len(analysis.narratives)}')
else:
    print('FAILED: finalize returned None')
