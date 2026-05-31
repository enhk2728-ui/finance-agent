"""全局配置——M5 价格行为读盘，Al Brooks 方法论。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if not _env_path.exists():
        _env_path = Path.cwd() / ".env"
    load_dotenv(_env_path) if _env_path.exists() else load_dotenv()
except Exception:
    pass

SYMBOL = "XAUUSD"
TIMEFRAME = "M5"

# 数据参数
LOOKBACK_DAYS = 3              # 默认拉取过去 3 天 M5 数据
M5_BARS_PER_DAY = 300          # M5 每天约 300 根 (24h 交易)
MT5_TZ_OFFSET_HOURS = 5        # MT5 服务器时间 → 北京时间

# 自动刷新选项（分钟）
REFRESH_OPTIONS = {
    "10 分钟": 600,
    "15 分钟": 900,
    "30 分钟": 1800,
    "1 小时": 3600,
    "4 小时": 14400,
}
DEFAULT_REFRESH = "15 分钟"

CACHE_STALE_SECONDS = 300

# 价格行为知识库路径（Al Brooks 著作）
KNOWLEDGE_DIR = os.getenv("GOLD_KNOWLEDGE_DIR", str(Path(__file__).resolve().parent.parent / "references"))
