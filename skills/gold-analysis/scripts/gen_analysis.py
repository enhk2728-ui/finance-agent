"""生成新的黄金分析 JSON 结果"""
import json
import datetime

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

analysis = {
    "symbol": "XAUUSD",
    "timeframe": "M5",
    "generated_at": now.isoformat(),
    "data_range": "05-26 22:05 ~ 05-30 04:45",
    "current_price": 4541.81,
    "atr": 3.2,
    "spread": 0.3,

    "structure": {
        "state": "transition",
        "confidence": "中",
        "summary": "XAUUSD 在经历 5/27 大阴暴跌 126 点（-2.84%）至 4401 低点后，5/28-29 连续两日 V 型强势反弹，5/29 单日暴涨 117 点（+2.59%）触及 4595 高点。然而 5/30 早盘从 4573 高点快速回落至 4541，呈现冲高回落格局。当前处于多空转换的关键过渡期：大级别上 4366-4401 区间形成强支撑基底，但 4573-4595 区域的抛压明显。M5 级别最近结构为 LL+LH（下降趋势特征），最后摆动高点和低点均在下移。市场正在测试 4540-4545 支撑区，若跌破则可能开启新一轮下跌；若守住并反弹，则可能在 4540-4580 区间震荡整理。",
        "hh": False,
        "hl": False,
        "ll": True,
        "lh": True,
        "last_swing_high": {"time": "05-30 00:35", "price": 4573.36, "type": "SH"},
        "last_swing_low": {"time": "05-30 03:55", "price": 4542.65, "type": "SL"}
    },

    "trend_maturity": {
        "stage": "末期",
        "retrace_depth_pct": 71.5,
        "channel_slope": "陡峭",
        "climax_signs": [
            "5/29 单日波幅 117 点（2.59%）为近 3 日最大",
            "5/29 23:10 触及 4595 后急剧回落 37 点，疑似冲顶",
            "M5 级别连续出现长上影线（05-30 00:35 后多根 K 线上影明显）",
            "从 4401 到 4595 的 194 点反弹已完成 61.8% 回撤位测试"
        ],
        "description": "5/27 暴跌 → 5/28-29 V 型反转 → 5/30 冲高回落的完整 cycle 已走完。从 4366 低点到 4595 高点的 229 点大反弹在 5/30 凌晨触及 4573 后动能衰竭。"
    },

    "direction": "bearish",

    "multi_tf": {
        "M5": "bearish",
        "M15": "bearish",
        "H1": "neutral",
        "H4": "bullish"
    },

    "key_zones": [
        {"lower": 4539.18, "upper": 4543.34, "mid": 4541.26, "touches": 4, "role": "support", "strength": "强", "description": "当前价格正 testing 此区域，SR Flip 支撑区核心，是多空分水岭"},
        {"lower": 4550.55, "upper": 4552.68, "mid": 4551.62, "touches": 3, "role": "resistance", "strength": "中", "description": "5/29 22:05 高点区域，突破后回踩确认的阻力位"},
        {"lower": 4557.48, "upper": 4561.83, "mid": 4559.66, "touches": 4, "role": "resistance", "strength": "中", "description": "5/29 23:45-05-30 02:35 密集震荡区，支撑→阻力翻转（SR Flip）"},
        {"lower": 4570.0, "upper": 4573.36, "mid": 4571.68, "touches": 2, "role": "resistance", "strength": "强", "description": "5/30 00:35 最高点，即时阻力，短期空头防守线"},
        {"lower": 4590.0, "upper": 4595.22, "mid": 4592.61, "touches": 1, "role": "resistance", "strength": "强", "description": "5/29 23:10 绝对高点，本次大反弹最高点，心理关口"},
        {"lower": 4520.80, "upper": 4526.26, "mid": 4523.53, "touches": 5, "role": "support", "strength": "强", "description": "5/29 下午多次测试的密集成交区，阻力→支撑翻转"},
        {"lower": 4504.16, "upper": 4510.56, "mid": 4507.36, "touches": 6, "role": "support", "strength": "强", "description": "5/29 上午核心震荡区间中枢，多次被测试未跌破"},
        {"lower": 4477.56, "upper": 4481.87, "mid": 4479.72, "touches": 2, "role": "support", "strength": "中", "description": "5/29 日内最低点 + V 型反弹起点，结构性支撑"}
    ],

    "signals": [
        {
            "type": "climax_reversal",
            "direction": "bearish",
            "title": "5/29 冲顶逆转信号",
            "description": "5/29 23:10 价格飙升至 4595.22（本次反弹最高点）后在 45 分钟内暴跌 37.7 点至 4557.48，形成典型的 Al Brooks 高潮反转模式：急速赶顶 → 长上影 → 急剧回落。随后 5/30 00:35 的二次冲高 4573.36 未能超越前高，确认了 M5 双顶雏形。",
            "price_level": 4595.22,
            "time": "05-29 23:10",
            "confidence": "高"
        },
        {
            "type": "sr_flip",
            "direction": "bearish",
            "title": "4557-4562 支撑→阻力翻转",
            "description": "[4557.48-4561.83] 区间在 5/29 晚间作为多次测试的支撑位（4 次 touches），但在 5/30 02:45 被跌破后翻转为阻力。02:35 反弹高点 4561.83 正好受制于该区间上沿，验证 SR Flip 有效。",
            "price_level": 4559.66,
            "time": "05-30 02:35",
            "confidence": "高"
        },
        {
            "type": "weak_retrace",
            "direction": "bearish",
            "title": "弱势反弹信号（4573→4551）",
            "description": "从 4573.36 高点到 4551.40 低点的 22 点下跌过程中，仅出现一次 10.4 点的反弹（4551→4561），反弹幅度仅为前一波跌幅的 47%，且随后的下跌创出更低低点 4542.65。弱反弹-新低的模式是典型空头主导结构。",
            "price_level": 4561.83,
            "time": "05-30 02:35",
            "confidence": "中"
        },
        {
            "type": "sr_flip",
            "direction": "bullish",
            "title": "4539-4543 阻力→支撑翻转",
            "description": "[4539.18-4543.34] 区间在 5/29 19:30 和 20:40 期间作为阻力阻挡了两波上涨，但在 5/29 22:05 被强力突破后转为支撑。当前价格 4541.81 正位于此区域内，是当前最重要的多空博弈焦点。",
            "price_level": 4541.26,
            "time": "05-30 04:45",
            "confidence": "高"
        },
        {
            "type": "fake_breakout",
            "direction": "bearish",
            "title": "05-30 02:45 假突破",
            "description": "5/30 02:35 价格反弹至 4561.83（看似要突破 4557-4562 阻力区），但紧接着一根大阴线从 4561.83 暴跌至 4550.55（11.3 点），完全吞没前一根阳线。典型的 M5 级别假突破 FBO，诱多后迅速反转向下。",
            "price_level": 4550.55,
            "time": "05-30 02:45",
            "confidence": "中"
        }
    ],

    "daily_summaries": [
        {"date": "2026-05-26", "weekday": "周二", "open": 4517.48, "high": 4524.91, "low": 4502.03, "close": 4506.50, "range_pct": 0.51, "body_direction": "阴", "note": "窄幅震荡阴线，波幅仅 23 点，市场在积蓄方向选择能量"},
        {"date": "2026-05-27", "weekday": "周三", "open": 4506.48, "high": 4527.79, "low": 4401.19, "close": 4436.20, "range_pct": 2.84, "body_direction": "阴", "note": "大阴暴跌 126 点（-2.84%），从 4527 高点单边下杀至 4401，空头完全掌控"},
        {"date": "2026-05-28", "weekday": "周四", "open": 4436.20, "high": 4484.97, "low": 4366.04, "close": 4481.87, "range_pct": 2.69, "body_direction": "阳", "note": "V 型大反弹！先探底 4366 后绝地反击收复 4481，振幅 119 点"},
        {"date": "2026-05-29", "weekday": "周五", "open": 4481.87, "high": 4595.22, "low": 4477.56, "close": 4571.14, "range_pct": 2.59, "body_direction": "阳", "note": "暴涨 117 点（+2.59%）！从 4477 低点一路推升至 4595 历史新高区域"},
        {"date": "2026-05-30", "weekday": "周六", "open": 4571.14, "high": 4573.36, "low": 4541.15, "close": 4541.81, "range_pct": 0.71, "body_direction": "阴", "note": "高开 4571 后短暂摸高 4573 即快速回落至 4541，获利回吐特征明显"}
    ],

    "trade_reference": {
        "direction": "空头",
        "entry_zone": "4555-4565 区间（接近 SR Flip 阻力区 4557-4562）",
        "stop_level": 4575.0,
        "target_levels": [4525.0, 4505.0, 4482.0],
        "reasoning": "(1) M5 级别 LL+LH 下降结构明确；(2) 4595→4573 双顶形态初现，二次冲高失败；(3) [4557-4562] SR Flip 阻力有效；(4) 5/30 02:45 FBO 假突破确认上方抛压；(5) 趋势成熟度为末期，上涨动能衰竭。",
        "invalidation": "价格有效突破 4573.36 并站稳 4575 以上，表明双底失效，可能开启新一波上涨"
    },

    "narratives": [
        {
            "title": "日线总览 —— 过山车式的 72 小时",
            "content": "过去 3 个交易日的 XAUUSD 行情堪称惊心动魄。5/27 周三一根 126 点的大阴棒将价格从 4527 砸至 4401，跌幅达 2.84%。但就在恐慌蔓延之际，5/28 周四走出了经典的 V 型反转——先向下刺穿 4366 创出更新低，然后绝地反击 115 点收于 4481。5/29 更是火力全开，从 4477 低点一路狂飙至 4595，单日涨幅 2.59%。然而故事并未就此结束。5/30 早盘开盘后，价格仅在 4573 略作试探便掉头向下，4 小时内从 4573 回落至 4541。这种暴涨后急跌的节奏变化，正是 Al Brooks 所说的趋势性质改变的典型征兆——当所有人都在谈论突破的时候，市场往往已经悄悄转向了。",
            "icon": "📈",
            "highlight": True
        },
        {
            "title": "市场状态 —— 多空过渡期的博弈",
            "content": "当前定位：Transition（过渡期）。从 M5 微观结构来看，最近的价格行为呈现出典型的下降趋势特征：LL (Lower Low) - 最后一个显著低点 4542.65 低于前一个低点 4550.55；LH (Lower High) - 最后一个显著高点 4561.83 低于前一个高点 4573.36。这个 LL+LH 组合意味着每一波反弹的高度在降低，而每一波回调的深度在增加——这是教科书式的空头控场微观结构。但从更大视角 H4 级别来看，从 4366 到 4595 的 229 点超级反弹仍然有效，形成了多时间框架矛盾：H4 看多 vs M5/M15 看空。Al Brooks 的处理原则：当多时间框架矛盾时，优先尊重较小周期的最新信号。",
            "icon": "⚖️",
            "highlight": True
        },
        {
            "title": "关键价位 —— 六个必看的博弈焦点",
            "content": "① 4541-4543（当前位置 - 强支撑）：价格正位于此 SR Flip 区域内，如果这里守住则可能在 4540-4580 震荡；一旦跌破下方空间打开。② 4555-4562（即时阻力 - SR Flip）：原支撑翻转为阻力，任何反弹至此应高度警惕。③ 4570-4574（短期顶部防线）：5/30 凌晨最高点所在区域，空头的止损线。④ 4590-4595（绝对高点）：本次反弹最高点，短期难以触及但到了就是绝佳做空区。⑤ 4520-4526（中级支撑）：5/29 下午密集成交区，第一目标位。⑥ 4477-4482（结构支撑）：V 型反弹起点，跌到这里整个 5/29 涨幅将归零。",
            "icon": "🎯",
            "highlight": False
        },
        {
            "title": "24h 结构演变 —— 从狂欢到清醒",
            "content": "第一阶段 蓄势(04:45-12:00)：价格在 4490-4520 窄幅震荡，亚洲盘整理格局。第二阶段 欧洲盘启动(12:00-17:50)：从 4508 推高至 4539，回调浅反弹快，趋势初期特征。第三阶段 加速拉升(17:50-23:10)：从 4539 飙升至 4595，涨幅 156 点！连续大阳线和强趋势棒，Al Brooks 称之为 climax run 高潮冲刺，通常是趋势末期标志。第四阶段 见顶回落(23:10-00:35)：触及 4595 后 45 分钟暴跌 38 点至 4557，二次冲高 4573 未超越前高，双顶雏形确立。第五阶段 获利回吐(00:35-04:45)：从 4573 滑落至 4541，出现假突破和 LL+LH 下降结构，空头逐渐掌控局面。",
            "icon": "🕐",
            "highlight": False
        },
        {
            "title": "总结与交易参考",
            "content": "核心结论：XAUUSD 处于暴涨后的获利回吐阶段，短期偏空。看跌理由：M5 级别 LL+LH 下降结构明确；4595→4573 双顶形态初现；SR Flip 阻力有效；FBO 假突破确认上方抛压；趋势成熟度为末期。看涨风险：H4 级别大反弹尚未被破坏；4541-4543 SR Flip 支撑正在接受测试。推荐策略：逢高做空入场区间 4555-4565，止损 4575，目标一 4525、目标二 4505、目标三 4482。替代策略：若 4540 被有效跌破可追空至 4520-4525。观望条件：价格重新站上 4570 并守住则取消做空计划转为观望。",
            "icon": "💡",
            "highlight": True
        }
    ],

    "chart_marks": [
        {"time": "05-27 10:00", "bar_type": "大阴", "price": 4450.0, "note": "5/27 暴跌日的强趋势阴棒"},
        {"time": "05-28 08:00", "bar_type": "大阳", "price": 4420.0, "note": "V型反转启动"},
        {"time": "05-29 09:10", "bar_type": "强趋势棒", "price": 4515.0, "note": "欧洲盘突破启动"},
        {"time": "05-29 13:50", "bar_type": "大阳", "price": 4514.77, "note": "午后加速拉升"},
        {"time": "05-29 17:10", "bar_type": "大阳", "price": 4529.0, "note": "美盘开盘跳涨"},
        {"time": "05-29 22:05", "bar_type": "大阳", "price": 4552.68, "note": "晚间突破 SR Flip 区间"},
        {"time": "05-29 23:10", "bar_type": "大阳", "price": 4595.22, "note": "绝对最高点 Climax Top"},
        {"time": "05-29 23:30", "bar_type": "大阴", "price": 4570.0, "note": "高潮后首次大幅回落"},
        {"time": "05-30 00:35", "bar_type": "十字星", "price": 4573.36, "note": "二次冲高 双顶右肩"},
        {"time": "05-30 02:45", "bar_type": "大阴", "price": 4550.55, "note": "假突破后暴跌 FBO"},
        {"time": "05-30 03:55", "bar_type": "大阴", "price": 4542.65, "note": "最新最低点 LL确认"},
        {"time": "05-30 04:25", "bar_type": "大阴", "price": 4542.52, "note": "测试 4540 支撑"}
    ]
}

# 写入 analysis_result.json
output_path = r"C:\Users\Administrator\.workbuddy\skills\gold-analysis\analysis_result.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

result_str = json.dumps(analysis, ensure_ascii=False)
print(f"OK: 分析结果已写入 {output_path}")
print(f"大小: {len(result_str)} bytes")
print(f"生成时间: {now.isoformat()}")
print(f"方向: {analysis['direction']}")
print(f"状态: {analysis['structure']['state']}")
print(f"信号数: {len(analysis['signals'])}")
print(f"每日数: {len(analysis['daily_summaries'])}")
print(f"叙事数: {len(analysis['narratives'])}")
print(f"K线标记: {len(analysis['chart_marks'])}")
