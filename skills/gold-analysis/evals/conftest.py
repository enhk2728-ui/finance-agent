"""共享测试夹具——合成 OHLC 数据 + 模拟 LLM 响应。"""
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import pandas as pd
import numpy as np
import pytest


def make_ohlc(prices: list, freq: str = "5min") -> pd.DataFrame:
    """从收盘价列表生成模拟 OHLC DataFrame。"""
    n = len(prices)
    times = pd.date_range("2026-01-05 08:00", periods=n, freq=freq)
    closes = np.array(prices, dtype=float)
    rng = np.random.default_rng(42)
    noises = rng.normal(0, 0.3, n)
    opens = closes + noises
    highs = np.maximum(opens, closes) + np.abs(rng.normal(0, 0.5, n))
    lows = np.minimum(opens, closes) - np.abs(rng.normal(0, 0.5, n))
    return pd.DataFrame({
        "time": times, "open": opens, "high": highs, "low": lows, "close": closes,
    })


@pytest.fixture
def uptrend_data():
    """清晰上升趋势数据。"""
    prices = []
    base = 2300.0
    for i in range(100):
        prices.append(base + i * 0.5 + np.random.default_rng(100 + i).normal(0, 0.8))
    return make_ohlc(prices)


@pytest.fixture
def ranging_data():
    """横盘整理数据。"""
    prices = []
    center = 2330.0
    for i in range(100):
        phase = (i / 25.0) * 2 * np.pi
        prices.append(center + np.sin(phase) * 15.0 + np.random.default_rng(200 + i).normal(0, 1.0))
    return make_ohlc(prices)

