"""Dashboard 主题 —— Liquid Metal · 金融科技终端 v4.0

设计方向: 暗色宇宙背景 + 玻璃拟态卡片 + 霓虹强调色
字体: Rajdhani (标题) + Noto Sans SC (正文) + JetBrains Mono (数据)
"""

import streamlit as st

CSS = """
/* ═══════════════════════════════════════════════════════════
   LIQUID METAL · 金融科技终端 v4.0
   ═══════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── CSS 变量 ── */
:root {
    --bg-deep: #080c14;
    --bg-surface: #0d1220;
    --bg-card: rgba(14, 20, 33, 0.75);
    --bg-card-hover: rgba(18, 26, 42, 0.85);
    --glass-border: rgba(255, 255, 255, 0.06);
    --glass-border-hover: rgba(255, 255, 255, 0.12);
    --gold: #e2b04a;
    --gold-dim: rgba(226, 176, 74, 0.18);
    --gold-glow: rgba(226, 176, 74, 0.35);
    --cyan: #00c8e8;
    --cyan-dim: rgba(0, 200, 232, 0.12);
    --green: #00d978;
    --green-dim: rgba(0, 217, 120, 0.12);
    --red: #ff3d5a;
    --red-dim: rgba(255, 61, 90, 0.12);
    --amber: #f08c2a;
    --amber-dim: rgba(240, 140, 42, 0.12);
    --text-primary: #e6e9f0;
    --text-secondary: #7a8299;
    --text-dim: #4a5168;
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 14px;
}

/* ── 全局基底 ── */
.stApp {
    background: var(--bg-deep);
    background-image:
        radial-gradient(ellipse at 20% 10%, rgba(226, 176, 74, 0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 90%, rgba(0, 200, 232, 0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 50% 50%, rgba(30, 40, 70, 0.15) 0%, transparent 100%);
}
.main .block-container {
    padding: 0.6rem 1.2rem 1rem 1.2rem;
    max-width: 1440px;
}

/* ── 网格背景纹理 ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    opacity: 0.03;
    background-image:
        linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 48px 48px;
}

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1a 0%, #0d1424 100%);
    border-right: 1px solid var(--glass-border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-border);
    color: var(--text-primary);
    border-radius: var(--radius-md);
    font-weight: 500;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem;
    letter-spacing: 0.5px;
    transition: all 0.25s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.08);
    border-color: var(--gold);
    box-shadow: 0 0 20px var(--gold-dim);
}
[data-testid="stSidebar"] hr { border-color: var(--glass-border) !important; }
[data-testid="stSidebar"] h3 {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.85rem;
    color: var(--text-secondary) !important;
}
[data-testid="stSidebar"] .stCaption {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim) !important;
}

/* ── 顶部标题栏 ── */
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 0;
    margin-bottom: 0.75rem;
    position: relative;
}
.header-bar::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--gold-dim) 5%,
        var(--gold) 20%,
        rgba(255,255,255,0.08) 50%,
        var(--cyan) 80%,
        var(--cyan-dim) 95%,
        transparent 100%);
}
.header-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 3px;
    text-transform: uppercase;
}
.header-title span {
    color: var(--gold);
}
.header-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-dim);
    letter-spacing: 1px;
}
.header-status {
    display: flex;
    align-items: center;
    gap: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.5px;
}
.header-status .live-tag {
    color: var(--green);
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── 价格行情条 ── */
.price-ticker {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 0.7rem 1.1rem;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
    position: relative;
    overflow: hidden;
}
.price-ticker::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-dim), var(--cyan-dim), transparent);
    opacity: 0.6;
}
.price-ticker:hover {
    border-color: var(--glass-border-hover);
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.price-main {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.65rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -1px;
    text-shadow: 0 0 30px var(--gold-glow);
}
.price-change {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 3px;
    letter-spacing: 0.5px;
}
.price-change.up {
    color: var(--green);
    background: var(--green-dim);
    border: 1px solid rgba(0, 217, 120, 0.25);
}
.price-change.down {
    color: var(--red);
    background: var(--red-dim);
    border: 1px solid rgba(255, 61, 90, 0.25);
}
.price-metric-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    color: var(--text-dim);
    margin-bottom: 0.15rem;
    font-weight: 600;
}
.price-metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
}

/* ── 方向徽章 ── */
.direction-badge {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 3px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.direction-badge.bullish {
    color: var(--green);
    background: var(--green-dim);
    border: 1px solid rgba(0, 217, 120, 0.25);
}
.direction-badge.bearish {
    color: var(--red);
    background: var(--red-dim);
    border: 1px solid rgba(255, 61, 90, 0.25);
}
.direction-badge.neutral {
    color: var(--amber);
    background: var(--amber-dim);
    border: 1px solid rgba(240, 140, 42, 0.25);
}

/* ── 通用卡片 ── */
.analysis-card {
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    position: relative;
}
.analysis-card:hover {
    border-color: var(--glass-border-hover);
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}
.analysis-card.highlight {
    border-color: rgba(226, 176, 74, 0.35);
    box-shadow: 0 0 24px var(--gold-dim);
}
.analysis-card.bullish-card {
    border-left: 2px solid var(--green);
}
.analysis-card.bearish-card {
    border-left: 2px solid var(--red);
}
.analysis-card.warning-card {
    border-left: 2px solid var(--amber);
}
.card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.card-body {
    font-size: 0.82rem;
    color: var(--text-primary);
    line-height: 1.7;
    font-family: 'Noto Sans SC', sans-serif;
}
.card-body strong { color: var(--gold); font-weight: 600; }

/* ── 信号标签 ── */
.signal-tag {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 3px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-right: 0.35rem;
    margin-bottom: 0.25rem;
}
.signal-tag.bullish {
    color: var(--green);
    background: var(--green-dim);
    border: 1px solid rgba(0, 217, 120, 0.2);
}
.signal-tag.bearish {
    color: var(--red);
    background: var(--red-dim);
    border: 1px solid rgba(255, 61, 90, 0.2);
}
.signal-tag.neutral {
    color: var(--amber);
    background: var(--amber-dim);
    border: 1px solid rgba(240, 140, 42, 0.2);
}
.signal-tag.high {
    border-color: var(--gold) !important;
    box-shadow: 0 0 12px var(--gold-dim);
}

/* ── 多周期方向 ── */
.mtf-section {
    margin-bottom: 0.85rem;
}
.mtf-section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--text-dim);
    margin-bottom: 0.4rem;
    font-weight: 600;
}
.mtf-grid {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
}
.mtf-item {
    flex: 1;
    min-width: 95px;
    text-align: center;
    padding: 0.65rem 0.6rem;
    border-radius: var(--radius-md);
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--glass-border);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.mtf-item::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    opacity: 0;
    transition: opacity 0.3s ease;
}
.mtf-item:hover::after { opacity: 1; }
.mtf-item.bullish-card::after { background: var(--green); }
.mtf-item.bearish-card::after { background: var(--red); }
.mtf-item.neutral-card::after { background: var(--amber); }
.mtf-item:hover {
    border-color: var(--glass-border-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.3);
}
.mtf-item .tf-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: var(--text-dim);
    margin-bottom: 0.2rem;
    transition: color 0.3s ease;
}
.mtf-item:hover .tf-label { color: var(--gold); }
.mtf-item .tf-dir {
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
}
.mtf-item .tf-dir.bullish { color: var(--green); }
.mtf-item .tf-dir.bearish { color: var(--red); }
.mtf-item .tf-dir.neutral { color: var(--amber); }

/* ── 价位表 ── */
.zone-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
}
.zone-table th {
    text-align: center;
    color: var(--text-dim);
    font-weight: 600;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 0.3rem 0.4rem;
    border-bottom: 1px solid var(--glass-border);
    white-space: nowrap;
}
.zone-table th:first-child { width: 6%; }
.zone-table th:nth-child(2) { width: 22%; }
.zone-table th:nth-child(3) { width: 10%; }
.zone-table th:nth-child(4) { width: 10%; }
.zone-table th:nth-child(5) { width: 7%; }
.zone-table th:nth-child(6) { width: 10%; }
.zone-table th:nth-child(7) { width: 35%; }
.zone-table td {
    padding: 0.3rem 0.4rem;
    color: var(--text-primary);
    border-bottom: 1px solid rgba(255,255,255,0.03);
    text-align: center;
    vertical-align: middle;
    white-space: nowrap;
}
.zone-table td:last-child {
    text-align: left;
    white-space: normal;
    font-size: 0.65rem;
    color: var(--text-secondary);
}
.zone-table td:first-child {
    color: var(--gold);
    font-weight: 600;
}
.zone-table td:nth-child(2) {
    text-align: right;
    padding-right: 0.5rem;
}
.zone-table td:nth-child(7) {
    text-align: left;
}
.zone-table tr:hover td {
    background: rgba(255,255,255,0.03);
}
.zone-table .zone-support { color: var(--green); }
.zone-table .zone-resistance { color: var(--red); }
.zone-table .zone-mixed { color: var(--amber); }
.zone-strength-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
}
.zone-strength-dot.strong {
    background: var(--gold);
    box-shadow: 0 0 8px var(--gold-glow);
}
.zone-strength-dot.medium {
    background: var(--text-secondary);
}
.zone-strength-dot.weak {
    background: var(--text-dim);
}

/* ── 每日总览表微调 ── */
.zone-table.daily-table {
    table-layout: auto;  /* 覆盖 fixed，让 note 列自适应内容宽度 */
    word-break: keep-all;
}
.zone-table.daily-table td,
.zone-table.daily-table th {
    padding: 0.25rem 0.4rem;
    line-height: 1.3;
    white-space: nowrap;
}
.zone-table.daily-table td.num {
    text-align: right;
    padding-right: 0.6rem;
}
.zone-table.daily-table td.note,
.zone-table.daily-table th:last-child {
    white-space: normal;
    width: 35%;          /* 给特征列足够宽度 */
    min-width: 120px;
}
.zone-table.daily-table td.note {
    text-align: left;
    font-size: 0.65rem;
    color: var(--text-secondary);
}

/* ── 卡片内文本块 ── */
.card-body {
    margin-top: 0.4rem;
}
.card-desc {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.5;
}
.signal-detail {
    margin-top: 0.6rem;
    padding: 0.4rem 0.5rem;
    background: rgba(255,255,255,0.02);
    border-radius: 4px;
    border-left: 2px solid rgba(226,176,74,0.25);
}
.signal-detail-header {
    font-size: 0.78rem;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
}
.signal-detail-desc {
    font-size: 0.72rem;
    color: var(--text-secondary);
    line-height: 1.45;
}
.signal-detail-desc p {
    margin: 0.2rem 0;
}
.tr-reasoning {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-size: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.45;
}
.tr-reasoning strong {
    color: var(--text-primary);
}

/* ── 状态指示点 ── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
    position: relative;
}
.status-dot.live {
    background: var(--green);
    box-shadow: 0 0 10px rgba(0, 217, 120, 0.5), 0 0 20px rgba(0, 217, 120, 0.2);
    animation: pulse-glow 2s ease-in-out infinite;
}
.status-dot.offline {
    background: var(--red);
    box-shadow: 0 0 10px rgba(255, 61, 90, 0.4);
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(0, 217, 120, 0.5), 0 0 20px rgba(0, 217, 120, 0.2); }
    50% { box-shadow: 0 0 16px rgba(0, 217, 120, 0.8), 0 0 32px rgba(0, 217, 120, 0.4); }
}

/* ── 分隔线 ── */
.section-divider {
    height: 1px;
    margin: 0.8rem 0;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--glass-border) 20%,
        var(--gold-dim) 50%,
        var(--glass-border) 80%,
        transparent 100%);
}
hr { border-color: var(--glass-border) !important; margin: 0.5rem 0 !important; }

/* ── 图表容器 ── */
.chart-container {
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 0.5rem;
    margin-bottom: 0.7rem;
}
.chart-container:hover {
    border-color: var(--glass-border-hover);
}

/* ── 交易参考卡 ── */
.trade-ref-card {
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.2rem;
    position: relative;
}
.trade-ref-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-dim), transparent);
    opacity: 0.5;
}
.trade-ref-card .tr-direction {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.trade-ref-card .tr-direction.long { color: var(--green); }
.trade-ref-card .tr-direction.short { color: var(--red); }
.trade-ref-card .tr-direction.wait { color: var(--amber); }
.trade-ref-card .tr-table {
    margin-top: 0.3rem;
}
.trade-ref-card .tr-table th:first-child {
    width: 30%;
    text-align: left;
}
.trade-ref-card .tr-table td:first-child {
    color: var(--text-dim);
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-size: 0.68rem;
}
.trade-ref-card .tr-table td:nth-child(2) {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.78rem;
    text-align: left;
}
.trade-ref-card .tr-extra {
    text-align: left;
    font-size: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.45;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.trade-ref-card .tr-extra strong {
    color: var(--text-primary);
}

/* ── 按钮 ── */
.stButton button {
    border-radius: var(--radius-md);
    font-weight: 600;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    transition: all 0.25s ease;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, #b88928 100%);
    color: #0a0e14;
    border: none;
}
.stButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, #f0cc5e 0%, var(--gold) 100%);
    box-shadow: 0 4px 24px var(--gold-dim);
    transform: translateY(-1px);
}

/* ── Select/Toggle 控件 ── */
[data-testid="stSelectbox"] label,
[data-testid="stToggle"] label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}

/* ── Streamlit 元素覆盖 ── */
.stMarkdown {
    color: var(--text-primary);
    line-height: 1.7;
    font-family: 'Noto Sans SC', sans-serif;
}
p, li { font-family: 'Noto Sans SC', sans-serif; }
h1, h2, h3, h4 {
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}
h3 {
    color: var(--text-secondary) !important;
    font-size: 0.9rem !important;
    letter-spacing: 2px !important;
}
.stSpinner { color: var(--gold) !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: var(--bg-deep); }

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }

/* ── 响应式 ── */
@media (max-width: 768px) {
    .price-ticker { flex-direction: column; align-items: flex-start; }
    .mtf-grid { flex-direction: column; }
    .header-bar { flex-direction: column; gap: 0.4rem; }
}

/* ── 卡片行等高 ── */
div[data-testid="stColumn"] {
    display: flex;
    flex-direction: column;
}
div[data-testid="stColumn"] > div {
    flex: 1;
    display: flex;
    flex-direction: column;
}
.price-ticker {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 78px;
}
.price-ticker.ticker-hero {
    min-height: 78px;
}
.price-ticker.ticker-hero .price-main {
    font-size: 1.2rem;
}
.price-ticker.ticker-hero .price-metric-label {
    margin-bottom: 0.1rem;
}
"""


def inject_dashboard_css():
    """注入 Liquid Metal 金融科技终端主题 CSS。"""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
