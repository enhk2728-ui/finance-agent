<!-- 语言切换 -->
<p align="right">
  <a href="README.md">🇬🇧 English</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="README.zh.md">🇨🇳 中文</a>
</p>

<h1 align="center">
  <img src="https://img.shields.io/badge/XAUUSD-黄金-ebc934?style=flat-square" alt="XAUUSD">
  黄金价格行为分析系统
</h1>

<p align="center">
  <strong>基于 Al Brooks 方法论与智能体驱动 AI 的全流程 XAUUSD 价格行为分析引擎</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/版本-4.2-blue?style=flat-square" alt="version">
  <img src="https://img.shields.io/badge/python-3.10+-green?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/框架-Streamlit-ff4b4b?style=flat-square" alt="streamlit">
  <img src="https://img.shields.io/badge/数据源-MT5-00549e?style=flat-square" alt="MT5">
  <img src="https://img.shields.io/badge/方法论-Al%20Brooks-8b5cf6?style=flat-square" alt="Al Brooks">
  <img src="https://img.shields.io/badge/许可证-MIT-lightgrey?style=flat-square" alt="license">
</p>

---

## 项目概述

黄金分析系统是一个**四阶段管线**，从原始行情数据到交互式金融看板。系统从 MT5 拉取实时 XAUUSD 数据，运行基于 Al Brooks 价格行为方法论的确定性算法分析，由智能体驱动的 LLM 阶段生成 AI 市场解读，最终在专业 Streamlit 看板中渲染全部结果。

```
MT5 (M5 数据, N 天)
  │
  ▼
price_action_analyzer.full_report()     ← 纯算法（无 LLM）
  ├─ 摆动点（最多 40 个）
  ├─ 价格区域（≥2 次触碰 → 关键区域）
  ├─ 趋势 / 陷阱 / 翻转 / 缺口
  │
  ▼
engine.prepare()                        ← 构建提示词（无 API 调用）
  ├─ system_prompt: 7 个 Brooks 参考资料 + JSON Schema
  ├─ user_prompt: OHLCV K 线 + 算法分析上下文
  └─ metadata: 数据范围、当前价格、ATR
  │
  ▼
看板 (阶段一 — 加载进度)
  ├─ st.status() 管线: 连接 → 拉取 → 算法分析
  ├─ 保存提示词供智能体消费
  └─ 进入"等待智能体"状态，显示部分看板
  │
  ▼
智能体 (Claude Code)                    ← 读取提示词，生成分析
  ├─ 使用自身模型推理（无需外部 API Key）
  └─ 输出匹配 Schema 的结构化 JSON
  │
  ▼
engine.finalize(agent_output)           ← 解析智能体 JSON → GoldAnalysis
  │
  ▼
看板 (阶段二 — 完整渲染)
  ├─ 通过文件监听检测 analysis_result.json
  └─ 渲染完整 9 段看板，含 AI 市场解读
```

### 核心架构决策

- **智能体驱动 LLM**：无需外部 LLM API Key — 智能体使用其自有模型进行推理
- **确定性算法层**：摆动点识别、价格区域聚类、陷阱检测 → 全部纯 Python，零随机性
- **严格数据契约**：10 个 Python dataclass（`schema.py`）定义智能体与看板之间的精确 JSON 合约
- **双阶段看板**：阶段一立即渲染算法数据；阶段二在智能体完成分析后解锁

---

## 快速开始

### 环境要求

- **Python 3.10+**
- **MT5 终端**（可选）— 仅实时数据需要；离线 CSV 模式任何系统均可运行
- **无需外部 LLM API Key** — 智能体内置模型处理所有推理
- MT5 需要 Windows（原生 COM 桥接）；Linux/macOS 可运行非 MT5 功能

### 安装

```bash
pip install -r assets/requirements.txt
```

### 看板先行工作流（推荐）

```bash
# 步骤 1: 启动看板 — 立即处理数据拉取和算法分析
cd skills/gold-analysis
streamlit run scripts/dashboard.py
# → 浏览器打开 http://localhost:8501
# → 实时显示进度: 连接数据源 → 拉取行情 → 算法分析
# → 进入"等待智能体"状态，已显示部分看板

# 步骤 2: 智能体读取提示词并生成 LLM 市场解读
# → 读取 prompts/system_prompt.md 和 prompts/user_prompt.md
# → 生成匹配输出 Schema 的 JSON 分析
# → 保存到 analysis_result.json

# 步骤 3: 看板自动检测结果并完整渲染
# → 含 AI 市场解读的完整 9 段看板
```

### 准备先行工作流（备选 — 批处理/命令行）

```bash
# 先生成分析，再查看
python scripts/analysis_engine.py --days 3 --prompts-only
# → 智能体生成 JSON → 保存 analysis_result.json
streamlit run scripts/dashboard.py  # 读取已保存的结果
```

### 离线演示（无需 MT5）

MT5 不可用时，系统自动回退到 `assets/sample_data.csv`（约 900 根 M5 K 线，约 3 个交易日）。看板清晰标注"离线 (CSV)"模式。

---

## 架构

| 层级 | 模块 | 输出 | 确定性 |
|------|------|------|:---:|
| **数据** | `data_fetcher.py` | pandas DataFrame | ✅ |
| **算法** | `price_action_analyzer.py` | 含 9 个分析键的字典 | ✅ |
| **提示词构建** | `llm_analyzer.py` (build_prompt) | system_prompt + user_prompt + metadata | ✅ |
| **LLM 推理** | 智能体 (Claude Code) | 结构化 JSON | ❌ |
| **响应解析** | `llm_analyzer.py` (parse_response) | GoldAnalysis dataclass | ✅ |
| **渲染** | `dashboard.py` + `dashboard_styles.py` | HTML/CSS | ✅ |

### 关注点分离

v4 的核心设计洞察：**llm_analyzer.py 零网络调用**。它是一个纯净的提示词构建器和响应解析器。智能体位于两半之间：

```
build_prompt(df, algo_result)   →   智能体 (读取提示词，生成 JSON)   →   parse_response(text, df)
```

无外部 API Key、无供应商锁定、无速率限制 — 智能体使用当前 Claude Code 会话的模型。

---

## 看板

### 液态金属主题

深色金融终端美学，玻璃拟态卡片、霓虹发光动画、金色点缀排版。

| 元素 | 样式 |
|------|------|
| 背景 | 深空海军蓝 `#080c14` + 径向渐变 + 网格纹理 |
| 卡片 | 玻璃拟态 (`backdrop-filter: blur(12px)`) |
| 主色 | 金色 `#e2b04a` |
| 强调色 | 青色 `#00c8e8` |
| 看涨色 | 绿色 `#00d978` |
| 看跌色 | 红色 `#ff3d5a` |
| 字体 | Rajdhani（标题）· Noto Sans SC（中文正文）· JetBrains Mono（数据） |

### 9 大渲染模块

1. **行情条** — 当前价格、ATR、MT5 状态、数据范围
2. **多周期方向** — M5 / M15 / H1 / H4 方向标签卡
3. **走势图** — Plotly OHLCV 含区域水平和 K 线标记标注
4. **每日总览** — 日期、OHLCV、振幅%、实体方向表
5. **市场结构卡** — 状态标签、HH/HL/LL/LH 证据、摆动点
6. **关键价位表** — 下限/上限、角色、强度、触碰次数、相对位置
7. **交易信号** — 信号标签及证据描述
8. **交易参考卡** — 方向、入场区、止损、目标及推理
9. **AI 市场解读** — 5+ 个中文叙述段落（智能体生成）

### 侧边栏控制

- 分析回溯天数：1 / 2 / 3 / 5 / 7 天
- 自动刷新开关 + 间隔（10分 / 15分 / 30分 / 1时 / 4时）
- 手动刷新 & 重连按钮
- 会话状态缓存提升性能

---

## 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `GOLD_KNOWLEDGE_DIR` | `references/` | Brooks 知识库目录（可自定义路径） |
| `GOLD_MT5_SYMBOL` | `XAUUSD` | 交易品种代码（不同经纪商可能需要不同代码） |
| `GOLD_LOOKBACK_DAYS` | `3` | 拉取 M5 数据的回溯天数 |
| `GOLD_CACHE_STALE_SECONDS` | `300` | 数据缓存的过期时间（秒） |

`config.py` 中的常量（非环境变量配置）：`TIMEFRAME = "M5"`、`M5_BARS_PER_DAY = 300`、`MT5_TZ_OFFSET_HOURS = 5`。

---

## CLI 命令参考

```bash
# 完整分析（算法 + 智能体提示词，需 MT5）
python scripts/analysis_engine.py --days 3 --print

# 纯算法分析（无智能体提示词，无需 API Key）
python scripts/analysis_engine.py --days 5 --skip-agent --print

# 仅生成提示词（保存到文件供手动智能体消费）
python scripts/analysis_engine.py --days 3 --prompts-only --output-dir ./prompts

# 保存分析到 JSON
python scripts/analysis_engine.py --days 3 --output result.json

# 独立对 CSV 运行价格行为分析
python scripts/price_action_analyzer.py data.csv
```

---

## 项目结构

```
gold-analysis/
├── SKILL.md                          # 完整的 16 章节技能文档
├── README.md                         # 英文 README
├── README.zh.md                      # 中文 README（← 你在这里）
├── finalize.py                       # 独立 finalize 脚本：智能体输出 → analysis_result.json
├── gen_analysis_live.py              # 实时智能体驱动分析执行器
│
├── scripts/                          # 10 个 Python 模块
│   ├── __init__.py                   # sys.path 初始化 + .env 自动加载
│   ├── config.py                     # 全局配置（环境变量 + 常量）
│   ├── schema.py                     # 10 个 dataclass + 严格 JSON 输出 Schema
│   ├── data_fetcher.py               # MT5 数据拉取、缓存、多周期支持
│   ├── price_action_analyzer.py      # 纯算法结构提取（884 行，11 个函数）
│   ├── llm_analyzer.py               # build_prompt() + parse_response() — 零 API 调用
│   ├── analysis_engine.py            # 编排：拉取 → 算法 → prepare/finalize → GoldAnalysis
│   ├── gen_analysis.py               # 独立分析生成的 CLI 入口
│   ├── dashboard.py                  # Streamlit Web 看板（18 个渲染函数）
│   └── dashboard_styles.py           # 液态金属金融终端 CSS（677 行）
│
├── references/                       # 7 份 Al Brooks 方法论文档
│   ├── 01-market-structure.md        # HH/HL/LL/LH 框架、趋势/震荡/过渡
│   ├── 02-breakouts.md               # 强/弱/假突破、突破回测
│   ├── 03-mm-traps.md                # 假突破、弱势回撤、三次测试
│   ├── 04-sr-flips.md                # 支撑阻力翻转、区域强度评级
│   ├── 05-measured-moves.md          # 基于尖峰/震荡区/楔形的目标测算
│   ├── 06-trend-maturity.md          # 三阶段生命周期、高潮形态识别
│   └── 07-key-reversal-signals.md    # 反转信号层级、确认规则
│
├── assets/
│   ├── .env.example                  # 配置模板（GOLD_* 环境变量说明）
│   ├── requirements.txt              # Python 包依赖
│   └── sample_data.csv               # 离线演示数据（约 900 根 M5 K 线）
│
├── evals/                            # 测试套件
│   ├── conftest.py                   # 共享测试 fixtures
│   ├── test_data_fetcher.py          # DataFetcher 初始化、缓存、mock fetch
│   └── test_llm_analyzer.py          # build_prompt() 结构、parse_response() 测试
│
└── prompts/                          # 运行时提示词存储（已 gitignore）
    ├── system_prompt.md              # Brooks 方法论 + JSON Schema
    └── user_prompt.md                # OHLCV K 线数据 + 算法分析上下文
```

---

## Al Brooks 方法论体系

七份参考文档编码了驱动分析的核心价格行为原则：

| # | 文档 | 核心概念 |
|---|------|---------|
| 01 | 市场结构 | HH+HL 确认上升趋势；LL+LH 确认下降趋势；混合信号 = 震荡/过渡 |
| 02 | 突破 | "永远假设突破会失败，除非它展现出强势" |
| 03 | MM 陷阱 | "识别谁被套住了——被套的交易者会为下一波行情提供燃料" |
| 04 | SR 翻转 | 旧支撑变新阻力（反向亦然）；触碰越多 = 翻转越强 |
| 05 | 测量目标 | 尖峰投影、缺口磁铁、震荡区 / 楔形目标测算 |
| 06 | 趋势成熟度 | 初期（浅回撤）→ 中期（深回撤，通道演变）→ 末期（高潮） |
| 07 | 关键反转 | 高潮反转（最强）→ 楔形/三推 → 双顶/双底 → 外包/内包 K 线 |

> **黄金法则**："绝不预期——等待信号 K 线被入场 K 线突破确认。"

---

## 数据契约

`schema.py` 中定义的智能体与看板之间的完整 JSON 合约：

| Dataclass | 用途 |
|-----------|------|
| `GoldAnalysis` | 顶层容器 — 完整分析响应 |
| `MarketStructure` | 市场状态（uptrend/downtrend/range/transition）、置信度、摆动点证据 |
| `TrendMaturity` | 趋势生命周期（初期/中期/末期）、回撤深度、高潮信号 |
| `PriceZone` | 价格区域含触碰次数、角色（support/resistance/mixed）、强度 |
| `PriceSignal` | 交易信号含类型（8 种枚举值）、方向、证据、置信度 |
| `DailySummary` | 单日 OHLCV + 振幅% + 实体方向（阳/阴） |
| `TradeReference` | 方向（多头/空头/观望）、入场区、止损、目标、推理、失效条件 |
| `NarrativeSection` | AI 叙述章节（标题、内容、图标、高亮标记） |
| `ChartData` | 完整 OHLCV 数组 + 区域 + K 线标记供 Plotly 渲染 |
| `BarMark` | 图表上的标注 K 线（K 线类型 + 价格 + 备注） |
| `PricePoint` | 单个摆动点（时间、价格、SH/SL 类型） |

**SignalType 枚举值**：`fake_breakout`（假突破）、`weak_retrace`（弱势回撤）、`triple_test_failure`（三次测试失败）、`sr_flip`（支撑阻力翻转）、`wedge`（楔形）、`double_top_bottom`（双顶/双底）、`climax_reversal`（高潮反转）、`gap`（缺口）

---

## 常见问题排查

| 症状 | 原因 | 解决方法 |
|------|------|---------|
| MT5 无法连接 | MT5 终端未启动或 XAUUSD 图表未打开 | 自动回退到 `assets/sample_data.csv`（离线演示数据） |
| 使用离线数据 | 本机无 MT5 | `DataFetcher` 自动加载 CSV。在分析中注明数据为历史快照 |
| 无离线数据可用 | `sample_data.csv` 缺失 | 重新运行 `python scripts/analysis_engine.py --prompts-only` |
| 数据不足（<30 根） | MT5 未打开 XAUUSD 图表 | 在 MT5 中打开 XAUUSD M5 图表，等待 K 线加载后刷新 |
| 智能体解析失败 | 智能体输出非有效 JSON 或 Schema 不匹配 | 检查智能体输出格式；确保严格匹配 LLM_OUTPUT_SCHEMA |
| 看板无法启动 | streamlit 未安装或 8501 端口被占用 | `pip install streamlit`，检查 `lsof -i :8501` |
| 导入错误 | 从错误目录运行 | 务必从 skill 根目录 (`skills/gold-analysis/`) 运行 |
| 字体无法加载 | 无互联网 / CDN 被屏蔽 | 字体从 Google Fonts CDN 加载；离线：提前本地安装字体 |

---

## 许可证

MIT

---

## 相关资源

- [Al Brooks 价格行为四部曲](https://www.brookstradingcourse.com/)
- [MetaTrader 5 Python 集成文档](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [Streamlit 文档](https://docs.streamlit.io/)
- [Claude Code 技能文档](https://docs.anthropic.com/en/docs/claude-code)
