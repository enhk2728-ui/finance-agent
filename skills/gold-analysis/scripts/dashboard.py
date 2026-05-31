"""XAUUSD 黄金分析看板 v4.3 —— Liquid Metal · 金融科技终端

设计: 暗色宇宙背景 + 玻璃拟态卡片 + 霓虹强调色
架构: GoldAnalysis (JSON) → HTML 组件 1:1 映射

数据来源优先级:
  1. analysis_result.json (agent 预生成的分析结果) — 完整 LLM 叙事
  2. 算法实时分析 (engine.prepare + 算法数据) — 结构数据无叙事

渲染规则:
  - HTML 容器/表格/标签 → st.markdown(html, unsafe_allow_html=True)
  - LLM 文本内容（含 markdown） → 独立 st.markdown(content)
  - 永远不在 HTML div 内部嵌入 LLM 生成的文本
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
_skill_root = _scripts_dir.parent

# 预生成分析结果路径 (agent 在启动看板前写入)
_PREGENERATED_ANALYSIS = _skill_root / "analysis_result.json"
# 中间结果路径（看板启动时由 engine 写入，包含算法分析结果）
_INTERMEDIATE_RESULT = _skill_root / "intermediate_result.json"
# Prompts 输出目录（agent 从此读取 system/user prompt 进行 LLM 分析）
_PROMPTS_DIR = _skill_root / "prompts"

try:
    from dotenv import load_dotenv
    load_dotenv(_skill_root / ".env")
except ImportError:
    pass

import streamlit as st
import plotly.graph_objects as go

from config import SYMBOL, REFRESH_OPTIONS, DEFAULT_REFRESH, LOOKBACK_DAYS
from analysis_engine import AnalysisEngine
from dashboard_styles import inject_dashboard_css

st.set_page_config(
    page_title=f"{SYMBOL} 价格行为分析",
    page_icon="◆",
    layout="wide",
)
inject_dashboard_css()


@st.cache_resource
def get_engine() -> AnalysisEngine:
    return AnalysisEngine()


# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

def _dir_cn(d: str) -> str:
    m = {"bullish": "多头 ▲", "bearish": "空头 ▼", "neutral": "观望 ◆"}
    return m.get(d, d)


def _card_open(title: str, extra_class: str = "", icon: str = "") -> None:
    """打开一个 HTML 卡片容器。"""
    st.markdown(
        f'<div class="analysis-card {extra_class}">'
        f'<div class="card-title">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def _card_close() -> None:
    """关闭 HTML 卡片容器。"""
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
# 渲染函数
# ═══════════════════════════════════════════

def render_price_ticker(analysis):
    """行情条 —— 纯数值数据，HTML 安全。"""
    price = analysis.current_price or 0
    atr = analysis.atr or 0
    direction = analysis.direction

    change_class = ""
    if direction == "bullish":
        change_class = "up"
    elif direction == "bearish":
        change_class = "down"

    struct = analysis.structure
    state_cn = {"uptrend": "上升趋势", "downtrend": "下降趋势",
                "range": "交易区间", "transition": "过渡期"}.get(
        struct.state if struct else "", "")

    cols = st.columns([2, 1, 1, 1, 1.5])
    with cols[0]:
        st.markdown(f"""
        <div class="price-ticker ticker-hero">
            <div class="price-metric-label">XAUUSD · M5</div>
            <div class="price-main">${price:,.2f}</div>
            <div class="price-change {change_class}" style="margin-top:0">{_dir_cn(direction)}</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="price-ticker">
            <div><div class="price-metric-label">ATR(14)</div>
            <div class="price-metric-value">{atr:.1f} 点</div></div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        live = engine.connected
        dot = "live" if live else "offline"
        txt = "在线" if live else "离线"
        st.markdown(f"""
        <div class="price-ticker">
            <div><div class="price-metric-label">MT5</div>
            <div class="price-metric-value"><span class="status-dot {dot}"></span>{txt}</div></div>
        </div>
        """, unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"""
        <div class="price-ticker">
            <div><div class="price-metric-label">数据范围</div>
            <div class="price-metric-value" style="font-size:0.75rem;">{analysis.data_range}</div></div>
        </div>
        """, unsafe_allow_html=True)
    with cols[4]:
        st.markdown(f"""
        <div class="price-ticker">
            <div><div class="price-metric-label">更新时间</div>
            <div class="price-metric-value">{datetime.now().strftime('%H:%M:%S')}</div></div>
        </div>
        """, unsafe_allow_html=True)


def render_multi_tf_display(analysis):
    """多周期方向 —— 纯枚举数据，HTML 安全。

    注意：使用单行拼接避免多行 f-string 在前端显示原始 HTML 代码。
    emoji 统一由 _dir_cn() 提供，不在 HTML 中重复追加。
    """
    mtf = analysis.multi_tf
    if not mtf:
        mtf = {"M5": analysis.direction, "M15": "neutral", "H1": "neutral", "H4": "neutral"}

    cells = []
    for tf in ["M5", "M15", "H1", "H4"]:
        d = mtf.get(tf, "neutral")
        label = {"bullish": "多头", "bearish": "空头", "neutral": "观望"}.get(d, "观望")
        emoji = {"bullish": "▲", "bearish": "▼", "neutral": "◆"}.get(d, "◆")
        cells.append(
            '<div class="mtf-item">'
            f'<div class="tf-label">{tf}</div>'
            f'<div class="tf-dir {d}">{emoji} {label}</div>'
            '</div>'
        )

    html = (
        '<div class="mtf-section">'
        '<div class="mtf-section-title">多周期方向</div>'
        '<div class="mtf-grid">'
        + ''.join(cells) +
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _md_to_html(text):
    """简易 Markdown → HTML：**bold**、*italic*、换行、列表。"""
    import re, html as _html
    if not text:
        return ""
    s = _html.escape(text)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'^[-•]\s+', '• ', s, flags=re.MULTILINE)
    s = re.sub(r'\n{2,}', '</p><p>', s)
    s = re.sub(r'\n', '<br>', s)
    return f'<p>{s}</p>'


def render_structure_card(analysis):
    """市场结构卡片 —— 数值部分用 HTML。"""
    struct = analysis.structure
    if not struct:
        return

    state_cn = {"uptrend": "上升趋势 (HH+HL)", "downtrend": "下降趋势 (LL+LH)",
                "range": "交易区间", "transition": "过渡状态"}.get(struct.state, struct.state or "—")

    card_class = "bullish-card" if analysis.direction == "bullish" else (
        "bearish-card" if analysis.direction == "bearish" else "")

    # 结构状态行
    parts = []
    for label, val in [("HH", struct.hh), ("HL", struct.hl), ("LL", struct.ll), ("LH", struct.lh)]:
        if val is not None:
            sym = "✓" if val else "✗"
            parts.append(f"{label}:{sym}")
    detail_str = " | ".join(parts) if parts else "结构: 算法分析中"

    # 摆动点
    sh = struct.last_swing_high
    sl = struct.last_swing_low
    sh_text = f"SH: {sh.price:.2f} ({sh.time})" if sh else ""
    sl_text = f"SL: {sl.price:.2f} ({sl.time})" if sl else ""
    swing_text = f"{sh_text}  {sl_text}".strip()

    # 趋势成熟度
    tm = analysis.trend_maturity
    tm_parts = []
    if tm:
        if tm.stage:
            tm_parts.append(f"阶段: {tm.stage}")
        if tm.retrace_depth_pct is not None:
            tm_parts.append(f"回调: {tm.retrace_depth_pct}%")
        if tm.channel_slope:
            tm_parts.append(f"通道: {tm.channel_slope}")
    tm_text = " | ".join(tm_parts) if tm_parts else ""

    # HTML 卡片
    card_body = f'<p><strong>状态</strong> {detail_str}</p>'
    if swing_text:
        card_body += f'<p><strong>摆动</strong> {swing_text}</p>'
    if tm_text:
        card_body += f'<p><strong>成熟度</strong> {tm_text}</p>'
    if struct.summary:
        card_body += f'<div class="card-desc">{_md_to_html(struct.summary)}</div>'

    st.markdown(f"""
    <div class="analysis-card {card_class}">
        <div class="card-title">市场结构 <span class="direction-badge {analysis.direction}">{state_cn}</span></div>
        <div class="card-body">{card_body}</div>
    </div>
    """, unsafe_allow_html=True)


def render_zones_table(analysis):
    """关键价位表 —— 纯数值数据，HTML table 安全。单次渲染确保对齐。"""
    zones = analysis.key_zones
    if not zones:
        return

    price = analysis.current_price

    # 构建完整表格（thead + tbody 一次性输出）
    rows_html = []
    for i, z in enumerate(zones):
        role_class = {"support": "zone-support", "resistance": "zone-resistance",
                      "mixed": "zone-mixed"}.get(z.role, "")
        role_cn = {"support": "支撑", "resistance": "阻力", "mixed": "翻转区"}.get(z.role, z.role)
        strength_dot = {"强": "strong", "中": "medium", "弱": "weak"}.get(z.strength, "medium")

        if price > z.upper:
            pos_class, pos_text = "zone-support", "↓ 下方"
        elif price < z.lower:
            pos_class, pos_text = "zone-resistance", "↑ 上方"
        else:
            pos_class, pos_text = "zone-mixed", "↔ 区间内"

        label = chr(65 + i)
        rows_html.append(f"""<tr>
            <td>{label}</td>
            <td class="{role_class}">{z.lower:.2f} – {z.upper:.2f}</td>
            <td class="{role_class}">{role_cn}</td>
            <td><span class="zone-strength-dot {strength_dot}"></span>{z.strength}</td>
            <td>{z.touches}次</td>
            <td class="{pos_class}">{pos_text}</td>
            <td>{z.description}</td>
        </tr>""")

    full_table = (
        '<div class="analysis-card">'
        '<div class="card-title">关键价格区间</div>'
        '<table class="zone-table">'
        '<thead><tr>'
        '<th>编号</th><th>价格范围</th><th>角色</th><th>强度</th><th>触碰</th><th>位置</th><th>说明</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table></div>'
    )
    st.markdown(full_table, unsafe_allow_html=True)


def render_signals(analysis):
    """交易信号 —— 标题/数值用 HTML，descriptions 用独立 markdown。"""
    signals = analysis.signals
    if not signals:
        return

    # 标签条（纯数据，HTML 安全）
    tags_html = []
    for s in signals:
        conf_class = "high" if s.confidence == "高" else ""
        tags_html.append(
            f'<span class="signal-tag {s.direction} {conf_class}">{s.title} ({s.confidence})</span>'
        )

    # 标签条 + 每条信号详情全部在卡片内
    detail_html = []
    for s in signals:
        price_str = f" @ ${s.price_level:.2f}" if s.price_level else ""
        time_str = f" ({s.time})" if s.time else ""
        header = f"<strong>{s.title}</strong>{price_str}{time_str}  <span style=\"opacity:.6\">置信度: {s.confidence}</span>"
        detail_html.append(f"<div class=\"signal-detail\"><div class=\"signal-detail-header\">{header}</div><div class=\"signal-detail-desc\">{_md_to_html(s.description)}</div></div>")

    st.markdown(f"""
    <div class="analysis-card warning-card">
        <div class="card-title">⚡ 交易信号</div>
        <div style="margin-bottom:0.5rem;">{"".join(tags_html)}</div>
        <div class="card-body">{"".join(detail_html)}</div>
    </div>
    """, unsafe_allow_html=True)


def render_trade_reference(analysis):
    """交易参考卡 —— 数值用 HTML，reasoning/invalidation 用独立 markdown。"""
    tr = analysis.trade_reference
    if not tr:
        return

    dir_class = {"多头": "long", "空头": "short", "观望": "wait"}.get(tr.direction, "wait")
    dir_emoji = {"多头": "🔺", "空头": "🔻", "观望": "⏸️"}.get(tr.direction, "")
    def _fmt_target(t):
        v = t["level"] if isinstance(t, dict) else t
        return f"${float(v):.2f}"
    targets = ", ".join(_fmt_target(t) for t in tr.target_levels) if tr.target_levels else "—"
    stop_str = f"${tr.stop_level:.2f}" if tr.stop_level else "—"

    # reasoning / invalidation 放入卡片内
    extra_rows = ""
    if tr.reasoning:
        extra_rows += f"""<tr><td colspan="2" class="tr-extra"><strong>交易逻辑:</strong> {_md_to_html(tr.reasoning)}</td></tr>"""
    if tr.invalidation:
        extra_rows += f"""<tr><td colspan="2" class="tr-extra"><strong>证伪条件:</strong> {_md_to_html(tr.invalidation)}</td></tr>"""

    # 完整 HTML 表格
    st.markdown(f"""
    <div class="trade-ref-card">
        <div class="card-title">🎯 交易参考与风险提示</div>
        <div class="tr-direction {dir_class}" style="margin-bottom:0.5rem;">{dir_emoji} {tr.direction}</div>
        <table class="zone-table tr-table">
            <thead><tr>
                <th>项目</th><th>详情</th>
            </tr></thead>
            <tbody>
                <tr>
                    <td>入场区间</td>
                    <td>{tr.entry_zone or '—'}</td>
                </tr>
                <tr>
                    <td>止损</td>
                    <td style="color:#F85149;">{stop_str}</td>
                </tr>
                <tr>
                    <td>目标</td>
                    <td style="color:#3BA55D;">{targets}</td>
                </tr>
                {extra_rows}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


def render_chart(analysis):
    """价格走势图表 —— 纯折线静态图片，无交互功能。"""
    chart = analysis.chart
    if not chart or not chart.times:
        return

    n = len(chart.times)
    start = max(0, n - 300)
    times = chart.times[start:]
    closes = chart.closes[start:]
    highs = chart.highs[start:]
    lows = chart.lows[start:]

    # 转换时间为 datetime
    try:
        import pandas as pd
        time_dt = pd.to_datetime(times)
    except Exception:
        time_dt = list(range(len(times)))

    # 日分隔 tick
    tick_indices = []
    tick_labels = []
    if isinstance(time_dt, pd.DatetimeIndex):
        last_date = None
        for i, t in enumerate(time_dt):
            d = t.date()
            if d != last_date:
                tick_indices.append(i)
                tick_labels.append(t.strftime("%m-%d"))
                last_date = d

    # Y轴范围：基于数据的实际高低点，加少量 padding
    data_low = min(lows) if lows else 0
    data_high = max(highs) if highs else 0
    data_range = data_high - data_low
    y_pad = data_range * 0.06 if data_range > 0 else 10
    y_min = data_low - y_pad
    y_max = data_high + y_pad

    fig = go.Figure()

    # 收盘价折线（无 hover）
    fig.add_trace(go.Scatter(
        x=time_dt,
        y=closes,
        mode="lines",
        line=dict(color="#e2b04a", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(226,176,74,0.06)",
        hoverinfo="skip",
    ))

    # 关键价位水平线（只画在数据可视范围内的）
    for zone in analysis.key_zones[:6]:
        if y_min <= zone.mid <= y_max:
            fig.add_hline(
                y=zone.mid, line_dash="dash", line_color="#e2b04a",
                opacity=0.3, line_width=1,
                annotation_text=f"{zone.mid:.1f}",
                annotation_position="right",
                annotation_font=dict(size=9, color="#e2b04a"),
            )

    # 静态布局（无 hover/spike/zoom）
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(14,20,33,0.75)",
        plot_bgcolor="rgba(8,12,20,0.6)",
        margin=dict(l=45, r=50, t=10, b=30),
        height=380,
        font=dict(family="JetBrains Mono", color="#7a8299", size=10),
        showlegend=False,
        xaxis=dict(
            tickmode="array" if tick_indices else "auto",
            tickvals=[time_dt[i] for i in tick_indices] if tick_indices else None,
            ticktext=tick_labels if tick_labels else None,
            tickangle=0,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
        ),
        yaxis=dict(
            range=[y_min, y_max],
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            side="right",
            tickformat=",.0f",
        ),
    )

    # 导出为静态 PNG 并用 st.image 展示
    try:
        from plotly.io import write_image
        import io
        buf = io.BytesIO()
        write_image(fig, buf, format="png", scale=2, width=1200, height=380,
                     engine="kaleido")
        buf.seek(0)
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.image(buf, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        # kaleido 不可用时回退到 plotly（禁用所有交互）
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": False,
            "displaylogo": False,
            "staticPlot": True,
        })
        st.markdown('</div>', unsafe_allow_html=True)


def render_narratives(analysis):
    """叙事章节 —— LLM 生成的长文本，每节用 HTML 标题框 + 独立 markdown 内容。"""
    narratives = analysis.narratives
    if not narratives:
        return

    for narr in narratives:
        card_class = "highlight" if narr.highlight else ""
        icon = narr.icon or ""
        content_html = _md_to_html(narr.content)

        st.markdown(f"""
        <div class="analysis-card {card_class}">
            <div class="card-title">{icon} {narr.title}</div>
            <div class="card-body">{content_html}</div>
        </div>
        """, unsafe_allow_html=True)


def render_daily_summaries(analysis):
    """每日总览 —— 纯数值数据，HTML table 安全。单次渲染确保对齐。"""
    ds_list = analysis.daily_summaries
    if not ds_list:
        return

    rows_html = []
    for ds in ds_list:
        dir_class = "zone-support" if ds.body_direction == "阳" else "zone-resistance"
        rows_html.append(f"""
        <tr>
            <td>{ds.date}</td>
            <td>{ds.weekday}</td>
            <td class="num">${ds.open:.2f}</td>
            <td class="num">${ds.high:.2f}</td>
            <td class="num">${ds.low:.2f}</td>
            <td class="num">${ds.close:.2f}</td>
            <td class="num">{ds.range_pct:.2f}%</td>
            <td class="{dir_class}">{ds.body_direction}线</td>
            <td class="note">{ds.note}</td>
        </tr>""")

    full_table = f"""
    <div class="analysis-card">
        <div class="card-title">每日总览</div>
        <table class="zone-table daily-table">
            <thead><tr>
                <th>日期</th><th>周</th><th>开</th><th>高</th><th>低</th><th>收</th><th>波幅</th><th>K线</th><th>特征</th>
            </tr></thead>
            <tbody>{"".join(rows_html)}</tbody>
        </table>
    </div>"""
    st.markdown(full_table, unsafe_allow_html=True)


# ═══════════════════════════════════════════
# 主看板
# ═══════════════════════════════════════════

engine = get_engine()


def _load_pregenerated_analysis():
    """加载 agent 预生成的分析结果 JSON 文件。

    返回 GoldAnalysis 对象，如果文件不存在或解析失败则返回 None。
    """
    if not _PREGENERATED_ANALYSIS.exists():
        return None
    try:
        from llm_analyzer import _json_to_analysis
        from schema import ChartData, BarMark
        data = json.loads(_PREGENERATED_ANALYSIS.read_text(encoding="utf-8"))
        raw = data.get("raw_analysis") or data
        inner = raw if isinstance(raw, dict) else json.loads(raw)
        analysis = _json_to_analysis(inner)
        # 填充非 LLM 字段
        analysis.symbol = data.get("symbol", SYMBOL)
        analysis.timeframe = data.get("timeframe", "M5")
        analysis.generated_at = data.get("generated_at", datetime.now().isoformat())
        analysis.current_price = data.get("current_price", 0)
        analysis.atr = data.get("atr", 0)
        analysis.data_range = data.get("data_range", "")
        # 图表数据
        chart = data.get("chart", {})
        if chart:
            times = chart.get("times", [])
            closes = chart.get("closes", [])
            highs = chart.get("highs", [])
            lows = chart.get("lows", [])
            analysis.chart = ChartData(
                times=times,
                opens=chart.get("opens", []),
                highs=highs,
                lows=lows,
                closes=closes,
                zones=analysis.key_zones,
                marks=[BarMark(**m) for m in chart.get("marks", [])],
            )
            # 从 chart 数据回填缺失字段
            if not analysis.current_price and closes:
                analysis.current_price = closes[-1]
            if not analysis.atr and highs and lows:
                n = min(14, len(highs))
                atr_val = sum(highs[-n:][i] - lows[-n:][i] for i in range(n)) / n
                analysis.atr = round(atr_val, 2)
            if not analysis.data_range and times:
                t_start = times[0]
                t_end = times[-1]
                # 截取日期部分（去掉时分秒）
                def _short(t):
                    s = str(t).strip()
                    return s[:10] if len(s) > 10 else s
                analysis.data_range = f"{_short(t_start)} ~ {_short(t_end)}"
        return analysis
    except Exception as e:
        st.warning(f"预生成分析文件加载失败: {e}")
        return None


def _build_from_intermediate(data: dict):
    """从 intermediate_result.json 重建 GoldAnalysis 对象。"""
    from schema import (
        GoldAnalysis, MarketStructure, PriceZone, PricePoint,
        DailySummary, NarrativeSection, ChartData,
    )
    analysis = GoldAnalysis()
    analysis.symbol = data.get("symbol", SYMBOL)
    analysis.timeframe = data.get("timeframe", "M5")
    analysis.generated_at = data.get("generated_at", "")
    analysis.data_range = data.get("data_range", "")
    analysis.current_price = data.get("current_price", 0)
    analysis.atr = data.get("atr", 0)
    analysis.direction = data.get("direction", "neutral")

    struct = data.get("structure", {})
    analysis.structure = MarketStructure(
        state=struct.get("state", "range"),
        confidence=struct.get("confidence", "中"),
        summary=struct.get("summary", ""),
        hh=struct.get("hh"), hl=struct.get("hl"),
        ll=struct.get("ll"), lh=struct.get("lh"),
    )

    for z in data.get("key_zones", []):
        analysis.key_zones.append(PriceZone(
            lower=z["lower"], upper=z["upper"], mid=z["mid"],
            touches=z.get("touches", 0), role=z.get("role", ""),
            strength=z.get("strength", ""), description=z.get("description", ""),
        ))

    for n in data.get("narratives", []):
        analysis.narratives.append(NarrativeSection(
            title=n.get("title", ""), content=n.get("content", ""),
            icon=n.get("icon", ""), highlight=n.get("highlight", False),
        ))

    chart = data.get("chart", {})
    if chart:
        analysis.chart = ChartData(
            times=chart.get("times", []),
            opens=chart.get("opens", []),
            highs=chart.get("highs", []),
            lows=chart.get("lows", []),
            closes=chart.get("closes", []),
            zones=analysis.key_zones,
        )

    return analysis


def _run_algorithm_only(lookback_days):
    """运行纯算法分析（无 LLM），返回基础 GoldAnalysis。"""
    from analysis_engine import AnalysisEngine
    eng = AnalysisEngine()
    result = eng.run(lookback_days=lookback_days, skip_llm=True)
    return result


def render_full_dashboard(analysis):
    """渲染完整看板（含 LLM 叙事）—— 9 段渲染管线。"""
    render_price_ticker(analysis)
    render_multi_tf_display(analysis)

    col_left, col_right = st.columns([5, 4])
    with col_left:
        render_chart(analysis)
        render_daily_summaries(analysis)
        render_signals(analysis)
    with col_right:
        render_structure_card(analysis)
        render_zones_table(analysis)
        render_trade_reference(analysis)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    with st.expander("🧠 AI 市场解读", expanded=False):
        render_narratives(analysis)


def render_partial_dashboard(analysis):
    """渲染部分看板（算法数据 + 等待 Agent 提示）。

    仅展示结构化数据（行情条、图表、价位表等），叙事区域显示
    Agent 进度提示而非 LLM 解读文字。
    """
    render_price_ticker(analysis)
    render_multi_tf_display(analysis)

    col_left, col_right = st.columns([5, 4])
    with col_left:
        render_chart(analysis)
        render_daily_summaries(analysis)
    with col_right:
        render_structure_card(analysis)
        render_zones_table(analysis)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # 等待 Agent 状态区
    st.markdown("### ⏳ AI 市场解读")
    prompts_exist = check_prompts_ready()

    wait_html = """
    <div class="analysis-card highlight" style="border:1px solid #e2b04a;">
        <div class="card-title">⏳ 等待 Agent 分析</div>
        <div class="card-body">
            <p style="color:#e2b04a;font-size:1.1rem;">Agent 正在使用 LLM 进行价格行为解读…</p>
            <p style="color:#8B949E;margin:0.75rem 0;">
                看板已启动并完成<strong>算法结构分析</strong>。<br>
                <strong>图表、价位、市场结构</strong>已在左侧展示。
            </p>
            <p style="color:#8B949E;margin:0.75rem 0;">
                接下来由 <strong>Agent (Claude Code)</strong> 完成:
            </p>
            <ol style="color:#8B949E;margin:0.5rem 0 0.5rem 1.25rem;">
                <li>读取价格行为 prompts（Al Brooks 方法论）</li>
                <li>用自身模型生成 JSON 格式的市场解读</li>
                <li>写入 <code>analysis_result.json</code></li>
                <li>看板自动检测 → 完整渲染</li>
            </ol>
            <div id="agent-status-section" style="margin-top:0.75rem;
                padding:0.6rem;background:rgba(226,176,74,0.08);border-radius:4px;
                font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#7a8299;">
                <span id="poll-status">📂 检测分析文件中...</span>
                <span id="poll-count" style="float:right;"></span>
            </div>
        </div>
    </div>
    """
    st.markdown(wait_html, unsafe_allow_html=True)

    # 显示 prompts 就绪状态
    if prompts_exist:
        sp_mtime = _PROMPTS_DIR.joinpath("system_prompt.md").stat().st_mtime if _PROMPTS_DIR.joinpath("system_prompt.md").exists() else 0
        up_mtime = _PROMPTS_DIR.joinpath("user_prompt.md").stat().st_mtime if _PROMPTS_DIR.joinpath("user_prompt.md").exists() else 0
        ready_time = datetime.fromtimestamp(max(sp_mtime, up_mtime)).strftime("%H:%M:%S")
        st.info(
            f"✅ Prompts 已就绪 ({ready_time}) —— Agent 可直接读取 "
            f"`prompts/system_prompt.md` 和 `prompts/user_prompt.md` "
            f"并在此会话中生成分析。完成后将 JSON 写入 "
            f"`analysis_result.json`，看板将自动检测。"
        )
    else:
        st.caption(
            "💡 **提示**: 运行 `python scripts/analysis_engine.py --days "
            f"{st.session_state.get('_lookback_days', 3)} --prompts-only` "
            "生成 prompts，Agent 即可开始分析。"
        )


def check_prompts_ready() -> bool:
    """检查 prompts 目录下是否有可用的 system_prompt.md 和 user_prompt.md。"""
    sp = _PROMPTS_DIR / "system_prompt.md"
    up = _PROMPTS_DIR / "user_prompt.md"
    return sp.exists() and up.exists()


def _watch_for_analysis_file():
    """前端轮询组件：向页面注入 JS 定时检测 analysis_result.json。

    使用 Streamlit 的 auto-refresh + session_state 实现文件检测。
    当检测到文件出现时，前端显示就绪提示。
    """
    # 使用 st.empty() + 周期性 rerun 实现轮询
    if "_poll_count" not in st.session_state:
        st.session_state["_poll_count"] = 0
    st.session_state["_poll_count"] += 1

    if _PREGENERATED_ANALYSIS.exists():
        # 文件已就绪 — 刷新看板
        st.session_state.pop("analysis_cache", None)
        st.session_state.pop("_poll_count", None)
        # 删除中间结果，下次启动不会卡在等待阶段
        if _INTERMEDIATE_RESULT.exists():
            _INTERMEDIATE_RESULT.unlink()
        st.rerun()
    else:
        # 文件尚未就绪 — 显示轮询状态
        count = st.session_state["_poll_count"]
        st.caption(
            f"🔍 轮询中… (第 {count} 次) | 等待 `analysis_result.json` 出现"
        )


def main():
    """两阶段看板主入口。

    Phase 1: 进度管道——独立阶段展示数据获取→算法分析→prompts 构建进度，
             渲染头部和侧边栏，使用 st.status() 展示分段加载状态。
    Phase 2: 全量渲染——若 analysis_result.json 存在则完整渲染；
             否则展示部分看板 + Agent 等待提示，由 _watch_for_analysis_file()
             定时轮询文件就绪。
    """

    # ── 渲染头部栏（始终可见）──
    st.markdown(f"""
    <div class="header-bar">
        <div>
            <span class="header-title"><span>◆</span> {SYMBOL} 价格行为分析</span>
            <span class="header-subtitle">Al Brooks 方法论 · Agent 驱动分析 · M5</span>
        </div>
        <div class="header-status">
            <span class="live-tag"><span class="status-dot live"></span>LIVE</span>
            <span>BEIJING {datetime.now().strftime('%H:%M:%S')} CST</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 侧边栏控制（始终可见）──
    with st.sidebar:
        st.markdown("### 设置")
        lookback_days = st.selectbox(
            "分析天数", options=[1, 2, 3, 5, 7], index=2,
            help="拉取过去 N 天的 M5 数据。当天权重最高。")
        st.session_state["_lookback_days"] = lookback_days
        st.markdown("---")

        auto_refresh = st.toggle("自动刷新", value=False)
        refresh_label = st.selectbox(
            "刷新间隔",
            options=list(REFRESH_OPTIONS.keys()),
            index=list(REFRESH_OPTIONS.keys()).index(DEFAULT_REFRESH),
            disabled=not auto_refresh,
        )
        refresh_seconds = REFRESH_OPTIONS[refresh_label]

        st.caption("引擎: Agent 驱动分析")
        st.caption("数据: MT5 XAUUSD · M5 / CSV 离线")
        st.caption("参考: Al Brooks 四部著作")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("刷新", type="primary", use_container_width=True):
                st.session_state.pop("analysis_cache", None)
                st.session_state.pop("_poll_count", None)
                _INTERMEDIATE_RESULT.unlink(missing_ok=True)
                st.rerun()
        with col_btn2:
            if st.button("重连", use_container_width=True):
                engine.reconnect()
                st.session_state.pop("analysis_cache", None)
                st.session_state.pop("_poll_count", None)
                _INTERMEDIATE_RESULT.unlink(missing_ok=True)
                st.rerun()

        st.markdown("---")
        st.caption("v4.2 · Static Chart")

    # ═══════════════════════ Phase 1: 进度管道 ═══════════════════════
    cache_key = f"analysis_{lookback_days}d"

    # 检查缓存
    if cache_key in st.session_state:
        analysis = st.session_state[cache_key]
        st.toast("✅ 从缓存加载", icon="🚀")

        if analysis and analysis.narratives and len(analysis.narratives) > 0:
            first_narr = analysis.narratives[0]
            if first_narr.title != "LLM 分析待完成" and first_narr.title != "等待 Agent 分析":
                # 完整分析已缓存
                render_full_dashboard(analysis)
            else:
                # 算法分析已缓存，等待 LLM
                render_partial_dashboard(analysis)
                _watch_for_analysis_file()
        else:
            render_partial_dashboard(analysis) if analysis else st.error("缓存数据异常")
            if analysis:
                _watch_for_analysis_file()

        if auto_refresh:
            time.sleep(refresh_seconds)
            st.session_state.pop(cache_key, None)
            st.rerun()
        return

    with st.status("正在启动黄金分析引擎…", expanded=True) as pipeline_status:
        # Stage 1: 连接数据源
        pipeline_status.update(label="📡 正在连接数据源...", state="running")
        st.write("🔍 检测 MT5 终端连接...")
        live = engine.connected
        if live:
            st.write(f"✅ MT5 已连接 — {SYMBOL}")
        else:
            st.write("⚠️ MT5 未连接，使用离线 CSV 数据")

        # Stage 2: 获取行情数据
        pipeline_status.update(label="📊 正在获取 XAUUSD M5 行情数据...", state="running")
        bar_count = lookback_days * 300  # M5_BARS_PER_DAY
        df = engine.fetcher.fetch("M5", count=bar_count)
        if df is None or len(df) < 30:
            pipeline_status.update(label="❌ 数据不足，无法分析", state="error")
            st.error(f"数据不足：{'无数据' if df is None else f'仅 {len(df)} 根 K 线'}（需要 ≥30 根）")
            st.info("请确保 MT5 中 XAUUSD M5 图表已打开且有足够历史数据，"
                    "或确保 `assets/sample_data.csv` 离线数据可用。")
            return
        st.write(f"✅ 获取 {len(df)} 根 M5 K 线 — {df['time'].iloc[0]} ~ {df['time'].iloc[-1]}")

        # Stage 3: 算法分析
        pipeline_status.update(label="🔍 正在运行价格行为算法分析...", state="running")
        try:
            from price_action_analyzer import full_report
            algo_result = full_report(df)
            st.write(f"✅ 算法分析完成 — "
                     f"趋势: {algo_result.get('trend', {}).get('direction', 'N/A')}, "
                     f"摆动点: {len(algo_result.get('sig_swings', []))} 个, "
                     f"价位区: {len(algo_result.get('zones', []))} 个")
        except Exception as e:
            pipeline_status.update(label="❌ 算法分析失败", state="error")
            st.error(f"算法分析异常: {e}")
            return

        # Stage 4: 检查预生成分析
        if _PREGENERATED_ANALYSIS.exists():
            pipeline_status.update(label="✅ 检测到 Agent 预生成分析，正在加载...", state="running")
            st.write("📂 发现 `analysis_result.json` — 加载 Agent 分析...")
            analysis = _load_pregenerated_analysis()
            if analysis is not None:
                pipeline_status.update(label="✅ 分析就绪，渲染看板", state="complete", expanded=True)
                st.toast("🎯 完整分析已加载", icon="✅")
                st.session_state[cache_key] = analysis
                render_full_dashboard(analysis)
                if auto_refresh:
                    time.sleep(refresh_seconds)
                    st.session_state.pop(cache_key, None)
                    st.rerun()
                return
            else:
                st.warning("analysis_result.json 解析失败，回退到算法模式")

        # Stage 5: 无预生成分析 — 保存中间结果 + 进入等待 Agent 模式
        pipeline_status.update(
            label="⏳ 算法分析完成 — 等待 Agent 生成 LLM 解读",
            state="running",
            expanded=False,
        )
        st.write("💡 **算法分析已完成**，图表和结构数据已就绪。")
        st.write("📋 接下来由 **Agent (Claude Code)** 使用 LLM 生成市场解读。")

        # 构建并保存 prompts
        try:
            from llm_analyzer import build_prompt
            prompts = build_prompt(df, algo_result, lookback_days)
            _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
            _PROMPTS_DIR.joinpath("system_prompt.md").write_text(
                prompts["system_prompt"], encoding="utf-8"
            )
            _PROMPTS_DIR.joinpath("user_prompt.md").write_text(
                prompts["user_prompt"], encoding="utf-8"
            )
            st.write(f"📝 Prompts 已就绪: `{_PROMPTS_DIR.relative_to(_skill_root)}`")
        except Exception as e:
            st.warning(f"Prompts 保存失败: {e}")

        # 保存中间结果供 partial dashboard 使用
        try:
            engine.save_intermediate(str(_INTERMEDIATE_RESULT))
            st.write(f"💾 算法分析中间结果已保存: `{_INTERMEDIATE_RESULT.name}`")
        except Exception as e:
            st.warning(f"中间结果保存失败: {e}")

        # 构建基础分析用于展示
        from analysis_engine import AnalysisEngine
        eng = AnalysisEngine()
        eng._last_df = df
        eng._last_algo_result = algo_result
        analysis = eng._build_basic_result(df, algo_result)
        st.session_state[cache_key] = analysis

    # ═══════════════════════ Phase 2: 部分看板 + 文件轮询 ═══════════════════════
    if analysis is not None:
        render_partial_dashboard(analysis)
        _watch_for_analysis_file()
    else:
        st.error("分析构建失败")

    # ── 自动刷新 ──
    if auto_refresh and not _PREGENERATED_ANALYSIS.exists():
        time.sleep(refresh_seconds)
        st.session_state.pop(cache_key, None)
        st.session_state.pop("_poll_count", None)
        st.rerun()


if __name__ == "__main__":
    main()
