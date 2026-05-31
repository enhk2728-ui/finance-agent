"""LLM 分析引擎单元测试——Prompt 构建 + 响应解析。"""
import json

import numpy as np
import pandas as pd
import pytest

from llm_analyzer import build_prompt, parse_response, calc_atr, _build_daily_summary


class TestCalcATR:
    def test_returns_positive(self, uptrend_data):
        atr = calc_atr(uptrend_data)
        assert atr > 0

    def test_atr_increases_with_volatility(self):
        np.random.seed(42)
        n = 50
        base = 2300
        calm = pd.DataFrame({
            "time": pd.date_range("2026-01-01", periods=n, freq="5min"),
            "open": [base + i * 0.1 for i in range(n)],
            "high": [base + i * 0.1 + 1 for i in range(n)],
            "low": [base + i * 0.1 - 1 for i in range(n)],
            "close": [base + (i + 0.5) * 0.1 for i in range(n)],
        })
        volatile = pd.DataFrame({
            "time": pd.date_range("2026-01-01", periods=n, freq="5min"),
            "open": [base + i * 0.1 for i in range(n)],
            "high": [base + i * 0.1 + 8 for i in range(n)],
            "low": [base + i * 0.1 - 8 for i in range(n)],
            "close": [base + (i + 0.5) * 0.1 for i in range(n)],
        })
        assert calc_atr(volatile) > calc_atr(calm)


class TestBuildDailySummary:
    def test_returns_string_with_dates(self, uptrend_data):
        result = _build_daily_summary(uptrend_data)
        assert isinstance(result, str)
        assert len(result) > 0


class TestBuildPrompt:
    def test_returns_dict_with_required_keys(self, uptrend_data):
        algo = {
            "trend": {"direction": "up"},
            "zones": [], "flips": [], "gaps": [], "traps": [], "swings": [],
        }
        result = build_prompt(uptrend_data, algo, lookback_days=1)
        assert isinstance(result, dict)
        for key in ("system_prompt", "user_prompt", "metadata"):
            assert key in result
        assert len(result["system_prompt"]) > 0
        assert len(result["user_prompt"]) > 0
        assert "symbol" in result["metadata"]

    def test_metadata_has_expected_fields(self, uptrend_data):
        algo = {
            "trend": {"direction": "up"},
            "zones": [], "flips": [], "gaps": [], "traps": [], "swings": [],
        }
        result = build_prompt(uptrend_data, algo)
        meta = result["metadata"]
        assert meta["symbol"] == "XAUUSD"
        assert meta["timeframe"] == "M5"
        assert meta["current_price"] > 0
        assert meta["atr"] > 0


class TestParseResponse:
    def test_valid_json_returns_gold_analysis(self, uptrend_data):
        from schema import GoldAnalysis

        response = json.dumps({
            "structure": {
                "state": "uptrend", "confidence": "高",
                "summary": "上升趋势", "hh": True, "hl": True, "ll": False, "lh": False,
            },
            "trend_maturity": {
                "stage": "中期", "channel_slope": "正常",
                "climax_signs": [], "description": "",
            },
            "direction": "bullish",
            "multi_tf": {"M5": "bullish", "M15": "neutral", "H1": "neutral", "H4": "neutral"},
            "key_zones": [],
            "signals": [],
            "daily_summaries": [],
            "trade_reference": {"direction": "观望"},
            "narratives": [{"title": "测试", "content": "内容"}],
            "chart_marks": [],
        })
        result = parse_response(response, uptrend_data)
        assert isinstance(result, GoldAnalysis)
        assert result.direction == "bullish"
        assert result.current_price > 0
        assert result.atr > 0

    def test_extracts_json_from_markdown_block(self, uptrend_data):
        from schema import GoldAnalysis

        response = """好的，以下是分析结果：

```json
{
    "structure": {"state": "range", "confidence": "中", "summary": "区间震荡", "hh": false, "hl": false, "ll": false, "lh": false},
    "trend_maturity": {"stage": "中期", "channel_slope": "正常", "climax_signs": [], "description": ""},
    "direction": "neutral",
    "multi_tf": {"M5": "neutral", "M15": "neutral", "H1": "neutral", "H4": "neutral"},
    "key_zones": [],
    "signals": [],
    "daily_summaries": [],
    "trade_reference": {"direction": "观望"},
    "narratives": [{"title": "测试", "content": "内容"}],
    "chart_marks": []
}
```

这就是当前的分析。
"""
        result = parse_response(response, uptrend_data)
        assert isinstance(result, GoldAnalysis)
        assert result.direction == "neutral"

    def test_invalid_text_returns_none(self, uptrend_data):
        result = parse_response("这不是有效的 JSON，没有任何分析内容", uptrend_data)
        assert result is None

    def test_empty_text_returns_none(self, uptrend_data):
        result = parse_response("", uptrend_data)
        assert result is None
