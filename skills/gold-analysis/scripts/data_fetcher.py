"""MT5 数据拉取 + 内存缓存。唯一与 MT5 交互的模块。

当 MT5 不可用时，自动回退到 assets/sample_data.csv（离线演示数据）。
"""
import logging
import time
from pathlib import Path
import pandas as pd
from typing import Optional, Dict

from config import MT5_TZ_OFFSET_HOURS

_SAMPLE_DATA_PATH = Path(__file__).resolve().parent.parent / "assets" / "sample_data.csv"

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
    logger.info("MetaTrader5 未安装，DataFetcher 将以离线模式运行")


COLUMNS = ["time", "open", "high", "low", "close"]


class DataFetcher:
    """从 MT5 获取多周期 K 线数据，内存缓存管理。"""

    def __init__(self, symbol: str = "XAUUSD", stale_seconds: int = 300):
        self.symbol = symbol
        self.connected = False
        self._offline = False  # True when using CSV fallback
        self._cache: Dict[str, pd.DataFrame] = {}
        self._last_update: Dict[str, float] = {}
        self._stale_seconds = stale_seconds
        self._connect()

    def _connect(self) -> bool:
        if mt5 is None:
            logger.info("MetaTrader5 未安装，尝试 CSV 离线模式")
            return self._try_offline()
        try:
            try:
                mt5.shutdown()
            except Exception:
                pass
            if not mt5.initialize():
                logger.warning("MT5 初始化失败——尝试 CSV 离线模式")
                return self._try_offline()

            # 打印终端信息辅助诊断
            info = mt5.terminal_info()
            if info is not None:
                logger.info(f"MT5 终端: {info.name}, 路径: {info.path}, 交易账户: {info.company}")

            # 查找可用的 XAUUSD symbol (可能带后缀如 XAUUSD., XAUUSDm, XAUUSD.i)
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                # 尝试带后缀的变体
                candidates = [s.name for s in mt5.symbols_get(group="*XAUUSD*") or []]
                if not candidates:
                    candidates = [s.name for s in mt5.symbols_get(group="*GOLD*") or []]
                logger.warning(
                    f"MT5 已连接但 {self.symbol} 不可用。"
                    f"可用 XAUUSD 变体: {candidates[:10]}"
                )
                if candidates:
                    self.symbol = candidates[0]
                    logger.info(f"自动切换到: {self.symbol}")
                    symbol_info = mt5.symbol_info(self.symbol)

            if symbol_info is None:
                logger.warning(f"所有 XAUUSD 变体均不可用——尝试 CSV 离线模式")
                return self._try_offline()

            self.connected = True
            logger.info(f"MT5 连接成功，{self.symbol} 可用")
            return True
        except Exception as e:
            logger.error(f"MT5 连接异常: {e}，尝试 CSV 离线模式")
            return self._try_offline()

    def _try_offline(self) -> bool:
        """尝试加载 CSV 离线数据作为回退。"""
        if _SAMPLE_DATA_PATH.exists():
            try:
                df = pd.read_csv(_SAMPLE_DATA_PATH, parse_dates=["time"])
                self._cache["M5"] = df
                self._last_update["M5"] = time.time()
                self._offline = True
                self.connected = True
                logger.info(
                    f"CSV 离线模式: 加载 {len(df)} 根 M5 K线, "
                    f"范围 {df['time'].iloc[0]} ~ {df['time'].iloc[-1]}, "
                    f"价格 {df['close'].iloc[-1]:.2f}"
                )
                return True
            except Exception as e:
                logger.error(f"CSV 加载失败: {e}")
        else:
            logger.info(f"离线数据不存在: {_SAMPLE_DATA_PATH}")
        self.connected = False
        return False

    def _is_stale(self, timeframe: str) -> bool:
        if timeframe not in self._last_update:
            return True
        return (time.time() - self._last_update[timeframe]) > self._stale_seconds

    def _mt5_timeframe(self, timeframe: str):
        tf_map = {
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
        }
        if timeframe not in tf_map:
            raise ValueError(f"不支持的时间周期: {timeframe}，可选: {list(tf_map.keys())}")
        return tf_map[timeframe]

    def _build_df(self, rates) -> pd.DataFrame:
        """将 MT5 rates 数组转为 DataFrame，时间戳统一转为北京时间。"""
        df = pd.DataFrame(rates)
        offset = pd.Timedelta(hours=MT5_TZ_OFFSET_HOURS)
        if isinstance(df.columns[0], int):
            return pd.DataFrame({
                "time": pd.to_datetime(df[0], unit="s") + offset,
                "open": df[1], "high": df[2], "low": df[3], "close": df[4],
            })
        return df.assign(
            time=pd.to_datetime(df["time"], unit="s") + offset
        )[COLUMNS]

    def fetch(self, timeframe: str, count: int = 200) -> Optional[pd.DataFrame]:
        """从 MT5 获取 K 线数据——多种策略回退确保拿到足够历史数据。

        当 MT5 不可用且已加载 CSV 离线数据时，直接返回缓存的 M5 数据。
        """
        if not self.connected and not self._connect():
            return None

        # 离线模式：直接返回 CSV 缓存数据
        if self._offline:
            df = self._cache.get(timeframe)
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                df = self._cache.get("M5")
            if df is not None and not (isinstance(df, pd.DataFrame) and df.empty):
                cutoff = min(len(df), count)
                return df.iloc[-cutoff:].reset_index(drop=True)
            return None

        import datetime as _dt
        mt5_tf = self._mt5_timeframe(timeframe)

        rates = None

        # 策略 1: copy_rates_from_pos (最快)
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5_tf, 0, count)
        except Exception:
            pass

        # 策略 2: copy_rates_from 按日期范围 (当策略 1 返回太少时)
        if rates is None or len(rates) < min(count, 30):
            try:
                end = _dt.datetime.now()
                # 根据周期回看不同的天数
                days_back = {"M5": 3, "M15": 7, "H1": 30, "H4": 60}.get(timeframe, 7)
                start = end - _dt.timedelta(days=days_back)
                rates = mt5.copy_rates_from(self.symbol, mt5_tf, start, count)
                if rates is not None and len(rates) > 0:
                    logger.info(
                        f"{self.symbol} {timeframe}: copy_rates_from_pos→{0 if rates is None else len(rates)}根, "
                        f"copy_rates_from→{len(rates)}根"
                    )
            except Exception:
                pass

        if rates is None or len(rates) == 0:
            logger.warning(f"{self.symbol} {timeframe} 无数据返回——请在 MT5 中打开 XAUUSD 图表")
            return None

        df = self._build_df(rates)
        self._cache[timeframe] = df
        self._last_update[timeframe] = time.time()
        return df

    def get_cached(self, timeframe: str) -> Optional[pd.DataFrame]:
        if not self._is_stale(timeframe) and timeframe in self._cache:
            return self._cache[timeframe]
        return self.fetch(timeframe)

    def has_enough_data(self, timeframe: str, min_bars: int = 50) -> bool:
        df = self._cache.get(timeframe)
        if df is None or self._is_stale(timeframe):
            return False
        return len(df) >= min_bars
