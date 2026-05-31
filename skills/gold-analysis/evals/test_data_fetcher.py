"""data_fetcher 模块的单元测试。"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from data_fetcher import DataFetcher


class TestDataFetcherInit:
    def test_default_symbol_is_xauusd(self):
        fetcher = DataFetcher()
        assert fetcher.symbol == "XAUUSD"

    @patch("data_fetcher.mt5", None)
    def test_mt5_not_available_does_not_crash(self):
        """MT5 不可用时初始化不崩溃。"""
        fetcher = DataFetcher()
        assert fetcher.connected is False


class TestDataFetcherCache:
    def test_is_stale_returns_true_for_old_cache(self):
        fetcher = DataFetcher()
        fetcher._last_update["M5"] = 0
        assert fetcher._is_stale("M5") is True

    def test_is_stale_returns_false_for_fresh_cache(self):
        import time
        fetcher = DataFetcher()
        fetcher._last_update["M5"] = time.time()
        assert fetcher._is_stale("M5") is False

    def test_has_enough_data_returns_false_for_empty_cache(self):
        fetcher = DataFetcher()
        assert fetcher.has_enough_data("M5") is False


class TestFetchWithMock:
    @patch("data_fetcher.mt5")
    def test_fetch_returns_dataframe(self, mock_mt5):
        mock_mt5.initialize.return_value = True
        mock_mt5.copy_rates_from_pos.return_value = [
            (1700000000, 2300.0, 2305.0, 2299.0, 2302.0, 100, 0, 0, 0),
            (1700000300, 2302.0, 2308.0, 2301.0, 2306.0, 120, 0, 0, 0),
        ]
        mock_mt5.TIMEFRAME_M5 = 1

        fetcher = DataFetcher()
        result = fetcher.fetch("M5", count=2)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["time", "open", "high", "low", "close"]

    @patch("data_fetcher.mt5")
    def test_fetch_returns_none_when_mt5_fails(self, mock_mt5):
        mock_mt5.initialize.return_value = False

        fetcher = DataFetcher()
        result = fetcher.fetch("M5")
        assert result is None

    @patch("data_fetcher.mt5")
    def test_get_cached_uses_cache(self, mock_mt5):
        import time
        mock_mt5.initialize.return_value = True

        fetcher = DataFetcher()
        fetcher._cache["M5"] = pd.DataFrame({"time": [], "open": [], "high": [], "low": [], "close": []})
        fetcher._last_update["M5"] = time.time()
        result = fetcher.get_cached("M5")
        assert result is not None
