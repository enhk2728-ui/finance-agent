"""Gold Analysis JSON Schema —— 严格定义 LLM 输出与前端渲染的数据契约。

所有字段使用 Python dataclass 定义，同时提供 JSON Schema 用于 LLM 约束。
前端渲染与此 Schema 一一对应映射，保证可迁移性。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


# ═══════════════════════════════════════════
# 枚举类型
# ═══════════════════════════════════════════

class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class MarketState(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGE = "range"
    TRANSITION = "transition"


class ZoneRole(str, Enum):
    SUPPORT = "support"
    RESISTANCE = "resistance"
    MIXED = "mixed"


class SignalType(str, Enum):
    FAKE_BREAKOUT = "fake_breakout"
    WEAK_RETRACE = "weak_retrace"
    TRIPLE_TEST = "triple_test_failure"
    SR_FLIP = "sr_flip"
    WEDGE = "wedge"
    DOUBLE_TOP_BOTTOM = "double_top_bottom"
    CLIMAX = "climax_reversal"
    GAP = "gap"


# ═══════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════

@dataclass
class PricePoint:
    time: str          # "MM-DD HH:MM"
    price: float
    type: str          # "SH" | "SL"


@dataclass
class PriceZone:
    lower: float
    upper: float
    mid: float
    touches: int
    role: str          # "support" | "resistance" | "mixed"
    strength: str      # "强" | "中" | "弱"
    description: str   # 为什么这个区间重要
    points: list[PricePoint] = field(default_factory=list)


@dataclass
class MarketStructure:
    state: str                              # "uptrend" | "downtrend" | "range" | "transition"
    confidence: str                         # "高" | "中" | "低"
    summary: str                            # 一句话市场格局描述（≤200字）
    hh: Optional[bool] = None
    hl: Optional[bool] = None
    ll: Optional[bool] = None
    lh: Optional[bool] = None
    last_swing_high: Optional[PricePoint] = None
    last_swing_low: Optional[PricePoint] = None


@dataclass
class TrendMaturity:
    stage: str          # "初期" | "中期" | "末期"
    retrace_depth_pct: Optional[float] = None   # 最近回调深度百分比
    channel_slope: str = "正常"                   # "平缓" | "正常" | "陡峭"
    climax_signs: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class PriceSignal:
    type: str           # SignalType 值
    direction: str      # "bullish" | "bearish"
    title: str          # 信号标题（中文）
    description: str    # 详细描述
    price_level: Optional[float] = None
    time: Optional[str] = None
    confidence: str = "中"  # "高" | "中" | "低"


@dataclass
class DailySummary:
    date: str           # "YYYY-MM-DD"
    weekday: str        # "周一" ~ "周日"
    open: float
    high: float
    low: float
    close: float
    range_pct: float    # 波幅百分比
    body_direction: str # "阳" | "阴"
    note: str = ""      # 一句话特征


@dataclass
class TradeReference:
    direction: str              # "多头" | "空头" | "观望"
    entry_zone: Optional[str] = None    # 入场区间描述
    stop_level: Optional[float] = None  # 止损价位
    target_levels: list[float] = field(default_factory=list)  # 目标价位
    reasoning: str = ""         # 交易逻辑
    invalidation: str = ""      # 什么条件证伪


@dataclass
class NarrativeSection:
    """叙事报告的单个章节 —— 对应 HTML 渲染的一个卡片。"""
    title: str          # 章节标题
    content: str        # 正文内容
    icon: str = ""      # 可选的 emoji/图标标识
    highlight: bool = False  # 是否高亮此卡片


@dataclass
class BarMark:
    """单根 K 线标记（用于图表标注）。"""
    time: str
    bar_type: str       # "大阳" | "大阴" | "十字星" | "长尾线" | "强趋势棒" | "外包棒" | "内包棒"
    price: float
    note: str = ""


@dataclass
class ChartData:
    """图表数据 —— 供前端 Plotly 渲染。"""
    times: list[str] = field(default_factory=list)
    opens: list[float] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    closes: list[float] = field(default_factory=list)
    zones: list[PriceZone] = field(default_factory=list)
    marks: list[BarMark] = field(default_factory=list)


@dataclass
class GoldAnalysis:
    """黄金分析完整输出 —— 顶层数据模型。

    这是 API 返回的完整 JSON 结构。前端仅依赖此结构渲染。
    """

    # 元信息
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    generated_at: str = ""          # ISO timestamp
    data_range: str = ""            # "MM-DD HH:MM ~ MM-DD HH:MM"

    # 实时行情
    current_price: float = 0.0
    atr: float = 0.0
    spread: float = 0.0             # 点差（如 MT5 可用）

    # 核心分析
    structure: Optional[MarketStructure] = None
    trend_maturity: Optional[TrendMaturity] = None
    direction: str = "neutral"      # 综合方向: "bullish" | "bearish" | "neutral"

    # 多周期速览
    multi_tf: dict[str, str] = field(default_factory=dict)  # {"M5": "bullish", "M15": "neutral", ...}

    # 关键价位
    key_zones: list[PriceZone] = field(default_factory=list)

    # 交易信号
    signals: list[PriceSignal] = field(default_factory=list)

    # 每日总览
    daily_summaries: list[DailySummary] = field(default_factory=list)

    # 交易参考
    trade_reference: Optional[TradeReference] = None

    # 图表数据
    chart: Optional[ChartData] = None

    # 叙事解读（多个章节）
    narratives: list[NarrativeSection] = field(default_factory=list)

    def to_dict(self) -> dict:
        """递归转为纯 dict，用于 JSON 序列化。"""
        return _to_dict(self)

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _to_dict(obj):
    """递归 dataclass → dict，处理嵌套和 None。"""
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for f_name in obj.__dataclass_fields__:
            val = getattr(obj, f_name)
            result[f_name] = _to_dict(val)
        return result
    return obj


# ═══════════════════════════════════════════
# LLM JSON Schema 约束（用于 prompt）
# ═══════════════════════════════════════════

LLM_OUTPUT_SCHEMA = r"""
你必须严格按照以下 JSON Schema 输出，不要输出任何 JSON 以外的内容。

```json
{
  "structure": {
    "state": "uptrend | downtrend | range | transition",
    "confidence": "高 | 中 | 低",
    "summary": "一句话市场格局描述，≤200字",
    "hh": true/false,
    "hl": true/false,
    "ll": true/false,
    "lh": true/false,
    "last_swing_high": {"time": "MM-DD HH:MM", "price": 0.0, "type": "SH"},
    "last_swing_low": {"time": "MM-DD HH:MM", "price": 0.0, "type": "SL"}
  },
  "trend_maturity": {
    "stage": "初期 | 中期 | 末期",
    "retrace_depth_pct": 0.0,
    "channel_slope": "平缓 | 正常 | 陡峭",
    "climax_signs": [],
    "description": "成熟度判断依据"
  },
  "direction": "bullish | bearish | neutral",
  "multi_tf": {
    "M5": "bullish | bearish | neutral",
    "M15": "bullish | bearish | neutral",
    "H1": "bullish | bearish | neutral",
    "H4": "bullish | bearish | neutral"
  },
  "key_zones": [
    {
      "lower": 0.0,
      "upper": 0.0,
      "mid": 0.0,
      "touches": 0,
      "role": "support | resistance | mixed",
      "strength": "强 | 中 | 弱",
      "description": "该区间为什么重要，与当前价格的关系"
    }
  ],
  "signals": [
    {
      "type": "fake_breakout | weak_retrace | triple_test_failure | sr_flip | wedge | double_top_bottom | climax_reversal | gap",
      "direction": "bullish | bearish",
      "title": "信号标题",
      "description": "详细描述信号，含价格行为依据",
      "price_level": 0.0,
      "time": "MM-DD HH:MM",
      "confidence": "高 | 中 | 低"
    }
  ],
  "daily_summaries": [
    {
      "date": "YYYY-MM-DD",
      "weekday": "周一",
      "open": 0.0,
      "high": 0.0,
      "low": 0.0,
      "close": 0.0,
      "range_pct": 0.0,
      "body_direction": "阳 | 阴",
      "note": "一句话概括当天特征"
    }
  ],
  "trade_reference": {
    "direction": "多头 | 空头 | 观望",
    "entry_zone": "入场区间描述",
    "stop_level": 0.0,
    "target_levels": [],
    "reasoning": "交易逻辑和价格行为依据",
    "invalidation": "证伪条件"
  },
  "narratives": [
    {
      "title": "章节标题",
      "content": "正文内容，使用中文叙事化表达",
      "icon": "📊",
      "highlight": false
    }
  ],
  "chart_marks": [
    {
      "time": "MM-DD HH:MM",
      "bar_type": "大阳 | 大阴 | 十字星 | 长尾线 | 强趋势棒 | 外包棒 | 内包棒",
      "price": 0.0,
      "note": "为什么标记这根棒"
    }
  ]
}
```

重要规则：
1. 严格按上述结构输出，不要添加或删除字段
2. 所有数值字段必须填具体数字，不要用字符串替代
3. direction 必须用小写英文
4. narratives 至少包含 5 个章节：(1)日线总览 (2)市场状态 (3)关键区间 (4)24h结构演变 (5)总结与交易参考
5. 每个数组字段至少包含 1 个元素（除 chart_marks 可为空数组）
6. 输出纯 JSON，不要包裹在 ```json 中，不要任何前缀或后缀文字
"""
