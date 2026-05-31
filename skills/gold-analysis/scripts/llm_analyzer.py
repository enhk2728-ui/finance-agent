"""LLM 价格行为分析引擎 —— Prompt 构建 + 响应解析。

此模块**不负责**调用外部 LLM API。它负责：
1. 构建系统提示词（加载 Al Brooks 参考文件 + JSON Schema）
2. 构建用户提示词（逐根 K 线数据 + 算法结构分析结果）
3. 从 LLM 输出文本中提取并解析 JSON → 强类型 GoldAnalysis

LLM 调用由 agent（Claude Code 自身模型）完成：
- agent 读取 build_prompt() 返回的 prompts
- agent 用自己的模型能力生成价格行为分析
- agent 将生成的文本交给 parse_response() 解析为 GoldAnalysis
"""

import json
import logging
import re
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from config import SYMBOL
from schema import (
    GoldAnalysis, MarketStructure, TrendMaturity, PriceZone,
    PriceSignal, DailySummary, TradeReference, NarrativeSection,
    PricePoint, BarMark, ChartData,
)

logger = logging.getLogger(__name__)

# 参考文件目录
_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"
if not _REFERENCES_DIR.exists():
    import os as _os
    _alt = _os.getenv("GOLD_KNOWLEDGE_DIR", "")
    if _alt and _os.path.isdir(_alt):
        _REFERENCES_DIR = Path(_alt)


def calc_atr(df, period=14):
    """计算平均真实波幅 ATR(14)。"""
    if df is None or len(df) < 2:
        return 0
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = np.maximum(high - low, np.maximum(
        (high - prev_close).abs(), (low - prev_close).abs()))
    atr = tr.rolling(window=period, min_periods=1).mean()
    return float(atr.iloc[-1])


def _load_references() -> str:
    """加载所有价格行为参考文件，拼接为系统提示词的知识基础。"""
    ref_files = sorted(_REFERENCES_DIR.glob("*.md")) if _REFERENCES_DIR.exists() else []
    if not ref_files:
        return ""

    parts = ["以下为 Al Brooks 价格行为方法论参考知识库：\n"]
    for fpath in ref_files:
        content = fpath.read_text(encoding="utf-8")
        parts.append(content)
        parts.append("\n---\n")
    return "\n".join(parts)


# ═══════════════════════════════════════════
# 系统提示词
# ═══════════════════════════════════════════

SYSTEM_PROMPT_TEMPLATE = """你是一位资深的价格行为交易分析师，严格遵循 Al Brooks 的方法论进行逐棒市场解读。

## 知识基础

{references}

## 输出要求

你必须输出**严格的 JSON**，按照以下 Schema。不要输出 Markdown，不要输出解释文字，只输出 JSON。

{json_schema}

## 写作原则

1. **教材级分析**：每个结论都有价格行为依据，解释因果关系
2. **叙事优先**：讲述价格运动的故事——"谁在控盘，为什么，接下来可能怎样"
3. **使用价格行为语言**：HH/HL、LL/LH、假突破、回测、供给区、需求区、楔形、高潮、三推、紧凑通道。不用 MACD/RSI/布林带等指标语言
4. **给出明确判断**：必须有方向判断，关键价位必须是具体数字
5. **中文输出**：所有文案用中文，专业术语保留英文缩写
"""


def _build_system_prompt() -> str:
    """构建完整的系统提示词（参考文件 + JSON Schema）。"""
    from schema import LLM_OUTPUT_SCHEMA
    references = _load_references()
    return SYSTEM_PROMPT_TEMPLATE.format(
        references=references if references else "（无外部参考文件，使用内置知识）",
        json_schema=LLM_OUTPUT_SCHEMA,
    )


# ═══════════════════════════════════════════
# 用户提示词构建
# ═══════════════════════════════════════════

def _build_daily_summary(df):
    """构建每日 OHLCV 总览文本。"""
    df = df.copy()
    df.loc[:, "date"] = df["time"].dt.date
    lines = []
    for date, day_df in df.groupby("date"):
        o = float(day_df["open"].iloc[0])
        h = float(day_df["high"].max())
        l = float(day_df["low"].min())
        c = float(day_df["close"].iloc[-1])
        rng = h - l
        body = c - o
        direction = "阳" if body > 0 else "阴"
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()]
        avg = (h + l) / 2
        rng_pct = round(rng / avg * 100, 2) if avg > 0 else 0
        lines.append(f"  {date} ({weekday})  O:{o:.2f} H:{h:.2f} L:{l:.2f} C:{c:.2f}  "
                     f"波幅{rng:.1f}点({rng_pct}%)  {direction}")
    return "\n".join(lines)


def _build_24h_bars(df, atr):
    """构建最近 24h 的逐根 K 线数据。"""
    if df is None or len(df) == 0:
        return "（无数据）"
    cutoff = df["time"].max() - pd.Timedelta(hours=24)
    recent = df[df["time"] >= cutoff].copy()
    if len(recent) == 0:
        recent = df.copy()
    lines = [f"最近 24h 共 {len(recent)} 根 M5 K线，ATR={atr:.1f}点。逐根如下："]
    lines.append(f"{'时间':<19s} {'开':>8s} {'高':>8s} {'低':>8s} {'收':>8s} {'实体':>6s}  标记")
    lines.append("-" * 85)
    for _, row in recent.iterrows():
        t = row["time"].strftime("%m-%d %H:%M")
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        direction = "阳" if c > o else ("阴" if c < o else "十")
        tags = []
        if body > atr * 0.6:
            tags.append("大" + ("阳" if c > o else "阴"))
        elif body < atr * 0.08:
            tags.append("十字星")
        if upper_wick > body * 1.5 and upper_wick > atr * 0.3:
            tags.append("长上尾")
        if lower_wick > body * 1.5 and lower_wick > atr * 0.3:
            tags.append("长下尾")
        if body > atr * 0.25 and upper_wick < body * 0.15 and lower_wick < body * 0.15:
            tags.append("强趋势棒")
        tag_str = " | ".join(tags) if tags else ""
        lines.append(f"{t:<19s} {o:>8.2f} {h:>8.2f} {l:>8.2f} {c:>8.2f} {body:>5.1f}点  {tag_str}")
    return "\n".join(lines)


def _build_swings_text(swings, max_count=40):
    """构建摆动点序列文本。"""
    if not swings:
        return "（无摆动点）"
    lines = []
    recent = swings[-max_count:]
    for i in range(1, len(recent)):
        prev = recent[i - 1]
        curr = recent[i]
        rng = abs(curr["price"] - prev["price"])
        direction = "SH" if curr["type"] == "SH" else "SL"
        lines.append(f"  {prev['time']} [{prev['price']:.2f}] → {curr['time']} [{curr['price']:.2f}]  "
                     f"{direction} {rng:.1f}点")
    return "\n".join(lines)


def _build_user_prompt(df, algo_result, lookback_days=3):
    """构建用户提示词 —— 原始 K 线数据 + 算法分析结果。"""
    n = len(df)
    current_price = float(df["close"].iloc[-1])
    atr = calc_atr(df)
    data_start = df["time"].iloc[0]
    data_end = df["time"].iloc[-1]

    parts = [
        f"品种: {SYMBOL}  |  周期: M5  |  总K线数: {n}",
        f"数据范围: {data_start} ~ {data_end}",
        f"当前价格: {current_price:.2f}  |  ATR(14): {atr:.1f} 点",
        f"分析窗口: 最近 {lookback_days} 天（当天权重最高）",
        "",
        "=" * 60,
        "=== 最近 24 小时逐根 M5 K 线（微观分析核心数据）===",
        "=" * 60,
        _build_24h_bars(df, atr),
        "",
        "=" * 60,
        "=== 以下为算法辅助分析（供参考）===",
        "=" * 60,
        f"\n--- 每日总览 ---\n{_build_daily_summary(df)}",
    ]

    trend = algo_result.get("trend", {})
    dir_map = {"up": "上升趋势 (HH+HL)", "down": "下降趋势 (LL+LH)",
               "range": "区间 / 过渡", "insufficient_data": "数据不足"}
    parts.append(f"\n--- 趋势结构 ---")
    parts.append(f"算法判断: {dir_map.get(trend.get('direction'), '未知')}")
    if trend.get("last_sh"):
        parts.append(f"  最后SH: {trend['last_sh']['price']:.2f} ({trend['last_sh']['time']})")
    if trend.get("last_sl"):
        parts.append(f"  最后SL: {trend['last_sl']['price']:.2f} ({trend['last_sl']['time']})")

    all_swings = algo_result.get("swings", [])
    parts.append(f"\n--- 全部摆动点 (共{len(all_swings)}个) ---")
    parts.append(_build_swings_text(all_swings, max_count=40))

    zones = algo_result.get("zones", [])
    parts.append(f"\n--- 关键价格区间 (共{len(zones)}个) ---")
    for z in zones[:8]:
        if z.get("touches", 0) < 2:
            continue
        role_cn = {"support": "支撑", "resistance": "阻力", "mixed": "翻转区"}.get(z["role"], z["role"])
        parts.append(f"  [{z['lower']:.2f} - {z['upper']:.2f}] {role_cn} 触碰{z['touches']}次")

    traps = algo_result.get("traps", [])
    if traps:
        parts.append(f"\n--- MM 陷阱信号 (共{len(traps)}个) ---")
        for t in traps[:8]:
            parts.append(f"  {t['description']}")

    flips = algo_result.get("flips", [])
    if flips:
        parts.append(f"\n--- SR 翻转 (共{len(flips)}处) ---")
        for f in flips:
            type_cn = "支撑→阻力" if f.get("flip_type") == "support_to_resistance" else "阻力→支撑"
            parts.append(f"  [{f['lower']:.2f} - {f['upper']:.2f}] {type_cn}")

    return "\n".join(parts)


# ═══════════════════════════════════════════
# JSON 解析与验证
# ═══════════════════════════════════════════

def _extract_json(text: str) -> Optional[str]:
    """从 LLM 输出中提取 JSON。处理各种包装情况。"""
    if not text:
        return None

    # 尝试直接提取 code block
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 查找第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        return text[start:end + 1]

    return None


def _parse_json_safe(json_str: str) -> Optional[dict]:
    """多层回退的 JSON 解析。"""
    attempts = [
        ("直接解析", lambda s: json.loads(s)),
        ("去除BOM", lambda s: json.loads(s.lstrip('﻿'))),
        ("修复trailing comma", lambda s: json.loads(re.sub(r',\s*}', '}', s))),
        ("修复trailing comma + 数组", lambda s: json.loads(re.sub(r',\s*]', ']', re.sub(r',\s*}', '}', s)))),
        ("raw_decode", lambda s: json.JSONDecoder().raw_decode(s)[0]),
    ]

    for name, fn in attempts:
        try:
            return fn(json_str)
        except Exception:
            continue

    return None


def _json_to_analysis(data: dict) -> GoldAnalysis:
    """将 LLM 输出的 JSON dict 转换为强类型 GoldAnalysis 对象。"""
    analysis = GoldAnalysis()

    # 市场结构
    struct_data = data.get("structure", {})
    if struct_data:
        analysis.structure = MarketStructure(
            state=struct_data.get("state", "range"),
            confidence=struct_data.get("confidence", "中"),
            summary=struct_data.get("summary", ""),
            hh=struct_data.get("hh"),
            hl=struct_data.get("hl"),
            ll=struct_data.get("ll"),
            lh=struct_data.get("lh"),
            last_swing_high=PricePoint(**struct_data["last_swing_high"]) if struct_data.get("last_swing_high") else None,
            last_swing_low=PricePoint(**struct_data["last_swing_low"]) if struct_data.get("last_swing_low") else None,
        )

    # 趋势成熟度
    tm_data = data.get("trend_maturity", {})
    if tm_data:
        analysis.trend_maturity = TrendMaturity(
            stage=tm_data.get("stage", "中期"),
            retrace_depth_pct=tm_data.get("retrace_depth_pct"),
            channel_slope=tm_data.get("channel_slope", "正常"),
            climax_signs=tm_data.get("climax_signs", []),
            description=tm_data.get("description", ""),
        )

    analysis.direction = data.get("direction", "neutral")
    analysis.multi_tf = data.get("multi_tf", {})

    # 关键价位
    for z_data in data.get("key_zones", []):
        analysis.key_zones.append(PriceZone(
            lower=z_data["lower"], upper=z_data["upper"], mid=z_data["mid"],
            touches=z_data["touches"], role=z_data["role"],
            strength=z_data.get("strength", "中"),
            description=z_data.get("description", ""),
            points=[PricePoint(**p) for p in z_data.get("points", [])],
        ))

    # 信号
    for s_data in data.get("signals", []):
        analysis.signals.append(PriceSignal(
            type=s_data["type"], direction=s_data["direction"],
            title=s_data["title"], description=s_data["description"],
            price_level=s_data.get("price_level"),
            time=s_data.get("time"),
            confidence=s_data.get("confidence", "中"),
        ))

    # 每日总览
    for d_data in data.get("daily_summaries", []):
        analysis.daily_summaries.append(DailySummary(**d_data))

    # 交易参考
    tr_data = data.get("trade_reference")
    if tr_data:
        # 归一化 target_levels: 确保是 list[float]
        raw_targets = tr_data.get("target_levels", [])
        norm_targets = []
        for t in raw_targets:
            if isinstance(t, dict):
                norm_targets.append(float(t.get("level", t.get("price", 0))))
            elif isinstance(t, (int, float)):
                norm_targets.append(float(t))
            else:
                norm_targets.append(float(t) if t else 0.0)
        analysis.trade_reference = TradeReference(
            direction=tr_data.get("direction", "观望"),
            entry_zone=tr_data.get("entry_zone"),
            stop_level=tr_data.get("stop_level"),
            target_levels=norm_targets,
            reasoning=tr_data.get("reasoning", ""),
            invalidation=tr_data.get("invalidation", ""),
        )

    # 叙事
    for n_data in data.get("narratives", []):
        analysis.narratives.append(NarrativeSection(
            title=n_data.get("title", ""),
            content=n_data.get("content", ""),
            icon=n_data.get("icon", ""),
            highlight=n_data.get("highlight", False),
        ))

    return analysis


# ═══════════════════════════════════════════
# 公共 API
# ═══════════════════════════════════════════

def build_prompt(df, algo_result, lookback_days=3) -> dict:
    """构建完整的 LLM 分析提示词，供 agent 使用。

    Returns:
        dict with keys:
            system_prompt: str  -- 系统提示词（知识库 + JSON Schema）
            user_prompt: str    -- 用户提示词（K线数据 + 算法结果）
            metadata: dict      -- {symbol, timeframe, current_price, atr, data_range, lookback_days}
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(df, algo_result, lookback_days)
    atr = calc_atr(df)
    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "metadata": {
            "symbol": SYMBOL,
            "timeframe": "M5",
            "current_price": float(df["close"].iloc[-1]),
            "atr": atr,
            "data_range": f"{df['time'].iloc[0].strftime('%m-%d %H:%M')} ~ {df['time'].iloc[-1].strftime('%m-%d %H:%M')}",
            "lookback_days": lookback_days,
            "system_prompt_chars": len(system_prompt),
            "user_prompt_chars": len(user_prompt),
        }
    }


def parse_response(text: str, df: Optional = None) -> Optional[GoldAnalysis]:
    """解析 agent/LLM 的输出文本，转换为 GoldAnalysis 对象。

    Args:
        text: agent 生成的原始文本（可含 markdown 包装）
        df: 可选，提供 DataFrame 以填充元信息和图表数据

    Returns:
        GoldAnalysis 对象，失败返回 None
    """
    json_str = _extract_json(text)
    if not json_str:
        logger.error("无法从输出中提取 JSON")
        return None

    data = _parse_json_safe(json_str)
    if not data:
        logger.error("JSON 解析失败")
        return None

    try:
        analysis = _json_to_analysis(data)
    except Exception as e:
        logger.error(f"JSON → GoldAnalysis 转换失败: {e}")
        return None

    # 填充元信息
    analysis.symbol = SYMBOL
    analysis.timeframe = "M5"
    analysis.generated_at = pd.Timestamp.now().isoformat()

    if df is not None and len(df) > 0:
        analysis.current_price = float(df["close"].iloc[-1])
        analysis.atr = calc_atr(df)
        analysis.data_range = f"{df['time'].iloc[0].strftime('%m-%d %H:%M')} ~ {df['time'].iloc[-1].strftime('%m-%d %H:%M')}"
        # 图表数据
        analysis.chart = ChartData(
            times=[t.strftime("%m-%d %H:%M") for t in df["time"]],
            opens=[float(x) for x in df["open"]],
            highs=[float(x) for x in df["high"]],
            lows=[float(x) for x in df["low"]],
            closes=[float(x) for x in df["close"]],
            zones=analysis.key_zones,
            marks=[BarMark(**m) for m in data.get("chart_marks", [])],
        )

    logger.info(f"响应解析完成: direction={analysis.direction}, "
                f"zones={len(analysis.key_zones)}, signals={len(analysis.signals)}, "
                f"narratives={len(analysis.narratives)}")
    return analysis
