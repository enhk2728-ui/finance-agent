"""
价格行为分析器 (Price Action Analyzer)
======================================
基于 Al Brooks 价格行为方法论，从 OHLCV K线数据中自动识别：

- 摆动高低点（Swing Highs / Swing Lows）
- 趋势结构（HH+HL 上升 / LL+LH 下降 / 区间）
- 关键价格区间（多次测试的支撑阻力带）
- 支撑阻力翻转（旧支撑变新阻力，破位回测）
- MM 做市商陷阱（假突破、弱势反弹、三次测试失败）
- 跳空缺口（跨会话的价格跳空）
- 全量结构报告（一键生成可读文本）

依赖：pandas, numpy
数据格式：DataFrame 需含列 ['time', 'open', 'high', 'low', 'close']

使用方式：
    import pandas as pd
    from price_action_analyzer import full_report

    df = pd.read_csv('xauusd_m5.csv')
    df['time'] = pd.to_datetime(df['time'])
    result = full_report(df)
    print(result['report'])   # 文本报告
    print(result['swings'])    # 摆动点列表
    print(result['zones'])     # 价格区间
"""

import pandas as pd
import numpy as np


# ============================================================
# 1. 摆动点检测
# ============================================================

def find_swings(df, lookback=5):
    """
    找出有效摆动高点和摆动低点。

    规则：一个摆动高点是其 high 在左右各 lookback 根 K 线中最高。
          一个摆动低点是其 low 在左右各 lookback 根 K 线中最低。

    参数:
        df: DataFrame，含 'high', 'low', 'time' 列
        lookback: 左右确认 K 线数 (默认 5，对 M5 图表约 25 分钟的确认窗口)

    返回:
        list[dict]: 按时间排序的摆动点列表
            每个 dict: {'idx': 行号, 'time': Timestamp, 'price': 价格, 'type': 'SH'或'SL'}
    """
    n = len(df)
    if n < lookback * 2 + 1:
        return []

    highs = df['high'].values
    lows = df['low'].values
    swings = []

    for i in range(lookback, n - lookback):
        # 摆动高点
        if highs[i] == max(highs[i - lookback:i + lookback + 1]):
            swings.append({
                'idx': int(i),
                'time': df['time'].iloc[i],
                'price': float(highs[i]),
                'type': 'SH'
            })
        # 摆动低点
        if lows[i] == min(lows[i - lookback:i + lookback + 1]):
            swings.append({
                'idx': int(i),
                'time': df['time'].iloc[i],
                'price': float(lows[i]),
                'type': 'SL'
            })

    # 按时间排序
    swings.sort(key=lambda x: x['idx'])
    return swings


# ============================================================
# 2. 过滤显著摆动点
# ============================================================

def filter_significant_swings(swings, min_range_pct=0.003):
    """
    从摆动点中筛选出有意义的波段转折点，过滤掉噪音摆动。

    规则：一个 SH→SL 或 SL→SH 的摆动段，幅度必须超过 min_range_pct（默认 0.3%）。
    对于 XAUUSD ~4700，0.3% = ~14 点。

    参数:
        swings: find_swings() 的输出
        min_range_pct: 最小波段幅度百分比 (默认 0.003 = 0.3%)

    返回:
        list[dict]: 过滤后的显著摆动点
    """
    if len(swings) < 2:
        return swings

    # 找出每段连续同向摆动，只保留幅度足够大的
    # 简化方法：只保留与前一个反向摆动点幅度 > 阈值的点
    significant = [swings[0]]

    for i in range(1, len(swings)):
        curr = swings[i]
        prev = significant[-1]

        if curr['type'] != prev['type']:
            # 方向变化，检查幅度
            range_size = abs(curr['price'] - prev['price'])
            avg_price = (curr['price'] + prev['price']) / 2
            threshold = avg_price * min_range_pct

            if range_size >= threshold:
                significant.append(curr)
        # 同方向：只保留更极端的点
        elif curr['type'] == 'SH' and curr['price'] > prev['price']:
            significant[-1] = curr
        elif curr['type'] == 'SL' and curr['price'] < prev['price']:
            significant[-1] = curr

    return significant


# ============================================================
# 3. 趋势结构判断
# ============================================================

def detect_trend(swings):
    """
    根据摆动高/低点判断当前趋势结构。

    规则：
    - 上升趋势：最近的 2 组摆动满足 HH + HL（更高的高点 + 更高的低点）
    - 下降趋势：最近的 2 组摆动满足 LL + LH（更低的低点 + 更低的高点）
    - 趋势不完整 → 区间

    参数:
        swings: 摆动点列表 (至少需要 2 个 SH 和 2 个 SL)

    返回:
        dict: {
            'direction': 'up' | 'down' | 'range' | 'insufficient_data',
            'hh': bool,      # 最近两个 SH 形成 HH?
            'hl': bool,      # 最近两个 SL 形成 HL?
            'll': bool,      # 最近两个 SL 形成 LL?
            'lh': bool,      # 最近两个 SH 形成 LH?
            'last_sh': {'price': float, 'time': str},
            'prev_sh': {'price': float, 'time': str},
            'last_sl': {'price': float, 'time': str},
            'prev_sl': {'price': float, 'time': str},
        }
    """
    sh_points = [s for s in swings if s['type'] == 'SH']
    sl_points = [s for s in swings if s['type'] == 'SL']

    if len(sh_points) < 2 or len(sl_points) < 2:
        return {
            'direction': 'insufficient_data',
            'hh': None, 'hl': None, 'll': None, 'lh': None,
            'last_sh': None, 'prev_sh': None,
            'last_sl': None, 'prev_sl': None
        }

    last_sh = sh_points[-1]
    prev_sh = sh_points[-2]
    last_sl = sl_points[-1]
    prev_sl = sl_points[-2]

    hh = last_sh['price'] > prev_sh['price']
    hl = last_sl['price'] > prev_sl['price']
    ll = last_sl['price'] < prev_sl['price']
    lh = last_sh['price'] < prev_sh['price']

    if hh and hl:
        direction = 'up'
    elif ll and lh:
        direction = 'down'
    else:
        direction = 'range'

    return {
        'direction': direction,
        'hh': hh, 'hl': hl, 'll': ll, 'lh': lh,
        'last_sh': {'price': last_sh['price'], 'time': str(last_sh['time'])},
        'prev_sh': {'price': prev_sh['price'], 'time': str(prev_sh['time'])},
        'last_sl': {'price': last_sl['price'], 'time': str(last_sl['time'])},
        'prev_sl': {'price': prev_sl['price'], 'time': str(prev_sl['time'])}
    }


# ============================================================
# 4. 关键价格区间（支撑阻力带）
# ============================================================

def find_price_zones(swings, tolerance_pct=0.0015, min_touches=2):
    """
    找出被多次测试的价格区间（支撑/阻力带）。

    原理：将摆动点的价格按 tolerance_pct 聚类。
    被触碰 >= min_touches 次的聚类就是关键区间。

    对 XAUUSD ~4700，tolerance_pct=0.0015（0.15%）= ~7点。
    即两个价格差距在 7 点以内视为"触及同一区域"。

    参数:
        swings: 摆动点列表
        tolerance_pct: 聚类容差百分比 (默认 0.0015)
        min_touches: 最少触碰次数才算关键区间 (默认 2)

    返回:
        list[dict]: 按价格排序的关键区间
            每个 dict: {
                'upper': 区间上沿,
                'lower': 区间下沿,
                'mid': 区间中位,
                'touches': 触碰次数,
                'role': 'support' | 'resistance' | 'mixed',
                'points': [该区间内所有摆动点]
            }
    """
    if len(swings) < min_touches:
        return []

    # 按价格排序
    sorted_swings = sorted(swings, key=lambda x: x['price'])
    avg_price = sum(s['price'] for s in swings) / len(swings)
    tolerance = avg_price * tolerance_pct

    # 贪心聚类
    clusters = []
    used = set()

    for i, s in enumerate(sorted_swings):
        if i in used:
            continue
        cluster = [s]
        used.add(i)
        for j in range(i + 1, len(sorted_swings)):
            if j in used:
                continue
            if sorted_swings[j]['price'] - cluster[0]['price'] <= tolerance:
                cluster.append(sorted_swings[j])
                used.add(j)
            else:
                break  # 已排序，后续更大

        if len(cluster) >= min_touches:
            prices = [p['price'] for p in cluster]
            # 判断角色
            types = set(p['type'] for p in cluster)
            if types == {'SH'}:
                role = 'resistance'
            elif types == {'SL'}:
                role = 'support'
            else:
                role = 'mixed'  # SH 和 SL 都出现过 -> 支撑阻力翻转区

            clusters.append({
                'upper': max(prices),
                'lower': min(prices),
                'mid': sum(prices) / len(prices),
                'touches': len(cluster),
                'role': role,
                'points': cluster
            })

    clusters.sort(key=lambda z: z['mid'])
    return clusters


# ============================================================
# 5. 支撑阻力翻转（旧支撑变阻力 / 旧阻力变支撑）
# ============================================================

def detect_sr_flips(zones, swings):
    """
    检测支撑阻力翻转：一个曾经是支撑的区间，后来被跌破并变成阻力（或反之）。

    判断标准：一个 zone 的 role='mixed'（既有 SH 也有 SL），
    且最近的触碰和最早的触碰类型不同。

    参数:
        zones: find_price_zones() 的输出
        swings: 摆动点列表（用于判断最新触碰）

    返回:
        list[dict]: 发生翻转的区间
            每个 dict 在 zone 基础上增加：
            {
                'flip_type': 'support_to_resistance' | 'resistance_to_support',
                'first_role': 最早触碰的类型,
                'last_role': 最近触碰的类型
            }
    """
    flips = []
    for zone in zones:
        if zone['role'] != 'mixed':
            continue
        if len(zone['points']) < 2:
            continue

        # 按时间排序
        sorted_points = sorted(zone['points'], key=lambda p: p['time'])
        first_type = sorted_points[0]['type']
        last_type = sorted_points[-1]['type']

        if first_type == last_type:
            continue  # 没有翻转

        flip = dict(zone)  # 复制
        if first_type == 'SL' and last_type == 'SH':
            flip['flip_type'] = 'support_to_resistance'
        else:
            flip['flip_type'] = 'resistance_to_support'

        flip['first_role'] = first_type
        flip['last_role'] = last_type
        flips.append(flip)

    return flips


# ============================================================
# 6. 跳空缺口检测
# ============================================================

def detect_gaps(df, time_col='time', gap_threshold_pct=0.002):
    """
    检测相邻 K 线之间的跳空缺口。

    跳空：当前 K 线的 open 不在前一根 K 线的 high-low 范围内，
    且偏离幅度超过阈值。

    参数:
        df: DataFrame
        time_col: 时间列名
        gap_threshold_pct: 跳空幅度阈值 (默认 0.2%，对 ~4700 约 9 点)

    返回:
        list[dict]: 跳空缺口列表
            每个 dict: {
                'idx': 缺口发生的行号,
                'time': 时间,
                'prev_close': 前一根收盘,
                'curr_open': 当前开盘,
                'gap_size': 跳空幅度,
                'direction': 'up' | 'down'
            }
    """
    gaps = []
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        # 向上跳空：当前开盘 > 前高
        if curr['open'] > prev['high']:
            gap_size = curr['open'] - prev['high']
            avg_price = (curr['open'] + prev['high']) / 2
            if avg_price > 0 and gap_size / avg_price >= gap_threshold_pct:
                gaps.append({
                    'idx': int(i),
                    'time': str(curr[time_col]),
                    'prev_close': float(prev['close']),
                    'curr_open': float(curr['open']),
                    'gap_size': float(gap_size),
                    'direction': 'up'
                })

        # 向下跳空：当前开盘 < 前低
        elif curr['open'] < prev['low']:
            gap_size = prev['low'] - curr['open']
            avg_price = (curr['open'] + prev['low']) / 2
            if avg_price > 0 and gap_size / avg_price >= gap_threshold_pct:
                gaps.append({
                    'idx': int(i),
                    'time': str(curr[time_col]),
                    'prev_close': float(prev['close']),
                    'curr_open': float(curr['open']),
                    'gap_size': float(gap_size),
                    'direction': 'down'
                })

    # 也检测跨日的开盘跳空 (连续两根K线时间差 > 1小时视为跨会话)
    for i in range(1, len(df)):
        time_diff = df[time_col].iloc[i] - df[time_col].iloc[i - 1]
        if time_diff.total_seconds() > 3600:  # 超过 1 小时
            prev_close = df.iloc[i - 1]['close']
            curr_open = df.iloc[i]['open']
            gap = curr_open - prev_close
            avg_price = (curr_open + prev_close) / 2
            if avg_price > 0 and abs(gap) / avg_price >= gap_threshold_pct:
                # 检查是否已经在普通跳空中（避免重复）
                already_found = any(g['idx'] == i for g in gaps)
                if not already_found:
                    gaps.append({
                        'idx': int(i),
                        'time': str(df[time_col].iloc[i]),
                        'prev_close': float(prev_close),
                        'curr_open': float(curr_open),
                        'gap_size': float(abs(gap)),
                        'direction': 'up' if gap > 0 else 'down',
                        'session_gap': True
                    })

    return gaps


# ============================================================
# 7. MM 陷阱检测
# ============================================================

def detect_mm_traps(df, swings, zones):
    """
    检测可能的做市商陷阱模式。

    检测三种模式：
    1. 假突破：价格突破关键区间后迅速回到区间内
    2. 弱势反弹：反弹高度不到前一波段的 38.2%
    3. 三次测试失败：同一阻力/支撑被测试 3 次以上但始终未突破

    参数:
        df: DataFrame
        swings: 摆动点列表
        zones: 关键区间列表

    返回:
        list[dict]: 陷阱信号列表
    """
    traps = []
    if len(swings) < 4 or not zones:
        return traps

    # 模式 1: 假突破检测
    for zone in zones:
        zone_mid = zone['mid']
        zone_width = zone['upper'] - zone['lower']

        for i in range(2, len(swings)):
            s0 = swings[i - 2]  # 突破前
            s1 = swings[i - 1]  # 突破
            s2 = swings[i]      # 突破后

            # 向上假突破: 突破阻力后立刻回来
            if (s0['type'] == 'SH' and
                s0['price'] <= zone['upper'] and
                s1['price'] > zone['upper'] and
                s2['price'] <= zone['upper'] and
                s2['type'] == 'SL'):
                traps.append({
                    'type': 'fake_breakout',
                    'direction': 'up',
                    'zone': f"{zone['lower']:.2f}-{zone['upper']:.2f}",
                    'break_time': str(s1['time']),
                    'break_price': s1['price'],
                    'return_time': str(s2['time']),
                    'description': f"假突破: {s1['price']:.2f}突破{zone['upper']:.2f}后回到区间内"
                })

            # 向下假突破
            if (s0['type'] == 'SL' and
                s0['price'] >= zone['lower'] and
                s1['price'] < zone['lower'] and
                s2['price'] >= zone['lower'] and
                s2['type'] == 'SH'):
                traps.append({
                    'type': 'fake_breakout',
                    'direction': 'down',
                    'zone': f"{zone['lower']:.2f}-{zone['upper']:.2f}",
                    'break_time': str(s1['time']),
                    'break_price': s1['price'],
                    'return_time': str(s2['time']),
                    'description': f"假突破: {s1['price']:.2f}跌破{zone['lower']:.2f}后回到区间内"
                })

    # 模式 2: 弱势反弹 (反弹不到前一波段的 38.2%)
    for i in range(2, len(swings)):
        prev = swings[i - 2]
        extreme = swings[i - 1]
        retrace = swings[i]

        # 下跌后的弱势反弹
        if (prev['type'] == 'SH' and extreme['type'] == 'SL' and
            retrace['type'] == 'SH'):
            leg_size = prev['price'] - extreme['price']
            retrace_size = retrace['price'] - extreme['price']
            if leg_size > 0 and retrace_size / leg_size < 0.382:
                traps.append({
                    'type': 'weak_retrace',
                    'direction': 'bearish',
                    'leg_size': round(leg_size, 2),
                    'retrace_pct': round(retrace_size / leg_size * 100, 1),
                    'time': str(retrace['time']),
                    'description': (
                        f"弱势反弹: {leg_size:.1f}点的跌势只反弹{retrace_size:.1f}点"
                        f"({retrace_size/leg_size*100:.1f}%), 不到38.2%"
                    )
                })

        # 上涨后的弱势回调
        if (prev['type'] == 'SL' and extreme['type'] == 'SH' and
            retrace['type'] == 'SL'):
            leg_size = extreme['price'] - prev['price']
            retrace_size = extreme['price'] - retrace['price']
            if leg_size > 0 and retrace_size / leg_size < 0.382:
                traps.append({
                    'type': 'weak_retrace',
                    'direction': 'bullish',
                    'leg_size': round(leg_size, 2),
                    'retrace_pct': round(retrace_size / leg_size * 100, 1),
                    'time': str(retrace['time']),
                    'description': (
                        f"弱势回调: {leg_size:.1f}点的涨势只回调{retrace_size:.1f}点"
                        f"({retrace_size/leg_size*100:.1f}%), 不到38.2%"
                    )
                })

    # 模式 3: 三次测试失败
    for zone in zones:
        if zone['touches'] >= 3:
            role_cn = '阻力' if zone['role'] == 'resistance' else ('支撑' if zone['role'] == 'support' else '区间')
            traps.append({
                'type': 'triple_test_failure',
                'zone': f"{zone['lower']:.2f}-{zone['upper']:.2f}",
                'touches': zone['touches'],
                'role': zone['role'],
                'description': (
                    f"三次测试{role_cn}: {zone['lower']:.2f}-{zone['upper']:.2f}"
                    f"被测试{zone['touches']}次未突破, 突破后动量可能很大"
                )
            })

    return traps


# ============================================================
# 8. 结构描述生成
# ============================================================

def describe_structure(df, swings, zones, flips, gaps, traps, trend):
    """
    生成人类可读的价格行为结构描述文本。

    参数: 各检测函数的输出

    返回:
        str: 格式化的中文报告文本
    """
    lines = []
    n = len(df)
    time_start = df['time'].iloc[0]
    time_end = df['time'].iloc[-1]
    price_low = df['low'].min()
    price_high = df['high'].max()
    total_range = price_high - price_low

    # 标题
    lines.append("=" * 64)
    lines.append(f"价格行为结构报告: XAUUSD M5")
    lines.append(f"时间: {time_start} ~ {time_end}")
    lines.append(f"K线数: {n}  价格范围: {price_low:.2f} ~ {price_high:.2f} (波幅 {total_range:.1f}点)")
    lines.append("=" * 64)

    # 趋势
    lines.append("")
    lines.append("【趋势结构】")
    if trend['direction'] == 'up':
        lines.append(f"  方向: 上升趋势 (HH+HL)")
    elif trend['direction'] == 'down':
        lines.append(f"  方向: 下降趋势 (LL+LH)")
    elif trend['direction'] == 'range':
        lines.append(f"  方向: 区间 / 趋势过渡期 (HH+HL/LL+LH 不一致)")
    else:
        lines.append(f"  数据不足，无法判断趋势")

    if trend.get('last_sh'):
        lines.append(f"  最近摆动高点: {trend['prev_sh']['price']:.2f} -> {trend['last_sh']['price']:.2f}")
    if trend.get('last_sl'):
        lines.append(f"  最近摆动低点: {trend['prev_sl']['price']:.2f} -> {trend['last_sl']['price']:.2f}")

    # 显著摆动点
    sig_swings = filter_significant_swings(swings)
    lines.append("")
    lines.append(f"【显著波段】(共 {len(sig_swings)} 个转折点, 仅列出 >0.3% 波段)")
    for i in range(1, len(sig_swings)):
        prev = sig_swings[i - 1]
        curr = sig_swings[i]
        if prev['type'] != curr['type']:
            rng = abs(curr['price'] - prev['price'])
            direction = "上涨" if curr['type'] == 'SH' else "下跌"
            lines.append(f"  {prev['time']} [{prev['price']:.2f}] -> {curr['time']} [{curr['price']:.2f}]  {direction} {rng:.1f}点")

    # 关键区间
    lines.append("")
    lines.append(f"【关键价格区间】(共 {len(zones)} 个)")
    for z in zones:
        role_cn = {'support': '支撑', 'resistance': '阻力', 'mixed': '翻转区'}.get(z['role'], z['role'])
        lines.append(f"  [{z['lower']:.2f} - {z['upper']:.2f}]  {role_cn}  触碰{z['touches']}次")
        # 列出触碰点
        for p in z['points']:
            marker = "▲" if p['type'] == 'SH' else "▼"
            lines.append(f"      {marker} {p['time']}  {p['price']:.2f}")

    # 支撑阻力翻转
    if flips:
        lines.append("")
        lines.append(f"【支撑阻力翻转】(共 {len(flips)} 处)")
        for f in flips:
            type_cn = '支撑变阻力' if f['flip_type'] == 'support_to_resistance' else '阻力变支撑'
            lines.append(f"  [{f['lower']:.2f} - {f['upper']:.2f}]  {type_cn}")

    # 跳空
    if gaps:
        lines.append("")
        lines.append(f"【跳空缺口】(共 {len(gaps)} 处)")
        for g in gaps:
            tag = " [跨会话]" if g.get('session_gap') else ""
            lines.append(f"  {g['time']}  {g['direction']}跳空 {g['gap_size']:.1f}点{tag}")

    # MM 陷阱
    if traps:
        lines.append("")
        lines.append(f"【潜在 MM 陷阱】(共 {len(traps)} 个信号)")
        for t in traps:
            type_cn = {
                'fake_breakout': '假突破',
                'weak_retrace': '弱势反弹',
                'triple_test_failure': '三次测试失败'
            }.get(t['type'], t['type'])
            lines.append(f"  [{type_cn}] {t['description']}")

    lines.append("")
    lines.append("=" * 64)
    return "\n".join(lines)


# ============================================================
# 9. 主入口：一键全量分析
# ============================================================

def full_report(df, lookback=5, min_range_pct=0.003, zone_tolerance_pct=0.0015):
    """
    一键生成完整的价格行为分析报告。

    参数:
        df: pandas DataFrame，须含 ['time', 'open', 'high', 'low', 'close']
        lookback: 摆动点左右确认窗口 (默认 5)
        min_range_pct: 最小有效波段幅度 (默认 0.003 = 0.3%)
        zone_tolerance_pct: 价格区间聚类容差 (默认 0.0015 = 0.15%)

    返回:
        dict: {
            'report': str,           # 人类可读的结构报告
            'df': DataFrame,         # 传入的原始数据
            'swings': list[dict],    # 所有摆动点
            'sig_swings': list,      # 过滤后的显著摆动点
            'trend': dict,           # 趋势判断
            'zones': list[dict],     # 关键价格区间
            'flips': list[dict],     # 支撑阻力翻转
            'gaps': list[dict],      # 跳空缺口
            'traps': list[dict],     # MM 陷阱信号
        }
    """
    # 确保时间列是 datetime
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])

    df = df.sort_values('time').reset_index(drop=True)

    # 1. 摆动点
    swings = find_swings(df, lookback=lookback)
    sig_swings = filter_significant_swings(swings, min_range_pct=min_range_pct)

    # 2. 趋势
    trend = detect_trend(sig_swings if sig_swings else swings)

    # 3. 价格区间
    zones = find_price_zones(swings, tolerance_pct=zone_tolerance_pct)

    # 4. 支撑阻力翻转
    flips = detect_sr_flips(zones, swings)

    # 5. 跳空
    gaps = detect_gaps(df)

    # 6. MM 陷阱
    traps = detect_mm_traps(df, sig_swings if sig_swings else swings, zones)

    # 7. 生成报告
    report = describe_structure(df, swings, zones, flips, gaps, traps, trend)

    return {
        'report': report,
        'df': df,
        'swings': swings,
        'sig_swings': sig_swings,
        'trend': trend,
        'zones': zones,
        'flips': flips,
        'gaps': gaps,
        'traps': traps
    }


# ============================================================
# 10. 为 LLM 叙事生成准备结构化上下文
# ============================================================

def prepare_llm_context(result: dict, max_zones: int = 6, max_traps: int = 5) -> str:
    """将 full_report 的结果整理为结构化上下文，供 LLM 生成叙事报告。

    提取关键字段（趋势、区间、翻转、陷阱、跳空），按 SKILL.md 模板格式组织。
    不包含原始 report 文本——LLM 应基于原始数据自行撰写。
    """
    df = result.get('df')
    trend = result.get('trend', {})
    zones = result.get('zones', [])
    flips = result.get('flips', [])
    gaps = result.get('gaps', [])
    traps = result.get('traps', [])
    sig_swings = result.get('sig_swings', [])

    lines = []
    n = len(df) if df is not None else 0

    # 时间范围 & 价格范围
    if df is not None and n > 0:
        lines.append(f"数据范围: {df['time'].iloc[0]} ~ {df['time'].iloc[-1]}  |  K线数: {n}")
        lines.append(f"价格范围: {df['low'].min():.2f} ~ {df['high'].max():.2f}  |  当前价: {df['close'].iloc[-1]:.2f}")

    # 每日总览 (SKILL.md 第一章)
    if df is not None and n > 0:
        lines.append("")
        lines.append("=== 每日总览 ===")
        df['date'] = df['time'].dt.date
        for date, day_df in df.groupby('date'):
            o = day_df['open'].iloc[0]
            h = day_df['high'].max()
            l = day_df['low'].min()
            c = day_df['close'].iloc[-1]
            body = c - o
            direction = "阳" if body > 0 else "阴"
            lines.append(f"  {date}  O:{o:.2f} H:{h:.2f} L:{l:.2f} C:{c:.2f}  {direction} {abs(body):.1f}点")

    # 趋势结构
    lines.append("")
    lines.append("=== 趋势结构 ===")
    dir_map = {"up": "上升趋势 (HH+HL)", "down": "下降趋势 (LL+LH)",
               "range": "区间 / 过渡", "insufficient_data": "数据不足"}
    lines.append(f"  方向: {dir_map.get(trend.get('direction'), '未知')}")
    if trend.get('last_sh'):
        lines.append(f"  摆动高点: {trend['prev_sh']['price']:.2f} -> {trend['last_sh']['price']:.2f}  (HH={trend.get('hh')})")
    if trend.get('last_sl'):
        lines.append(f"  摆动低点: {trend['prev_sl']['price']:.2f} -> {trend['last_sl']['price']:.2f}  (HL={trend.get('hl')}, LL={trend.get('ll')})")

    # 显著波段 (最近 6 个)
    if sig_swings:
        lines.append("")
        lines.append("=== 显著波段 (幅度 >= 0.3%) ===")
        recent = sig_swings[-6:]
        for i in range(1, len(recent)):
            prev = recent[i - 1]
            curr = recent[i]
            if prev['type'] != curr['type']:
                rng = abs(curr['price'] - prev['price'])
                direction = "上涨" if curr['type'] == 'SH' else "下跌"
                lines.append(f"  {prev['time']} [{prev['price']:.2f}] -> {curr['time']} [{curr['price']:.2f}]  {direction} {rng:.1f}点")

    # 关键价格区间
    if zones:
        lines.append("")
        lines.append("=== 关键价格区间 ===")
        for z in zones[:max_zones]:
            role_cn = {'support': '支撑', 'resistance': '阻力', 'mixed': '翻转区'}.get(z['role'], z['role'])
            lines.append(f"  区间 [{z['lower']:.2f} - {z['upper']:.2f}]  {role_cn}  触碰{z['touches']}次")
            for p in z['points'][:5]:
                marker = "▲" if p['type'] == 'SH' else "▼"
                lines.append(f"      {marker} {p['time']}  {p['price']:.2f}")

    # SR 翻转
    if flips:
        lines.append("")
        lines.append("=== SR 翻转 ===")
        for f in flips:
            type_cn = '支撑→阻力' if f.get('flip_type') == 'support_to_resistance' else '阻力→支撑'
            lines.append(f"  [{f['lower']:.2f} - {f['upper']:.2f}]  {type_cn}")

    # 跳空
    if gaps:
        lines.append("")
        lines.append("=== 跳空缺口 ===")
        for g in gaps:
            tag = "[跨会话]" if g.get('session_gap') else ""
            lines.append(f"  {g['time']}  {g['direction']}跳空 {g['gap_size']:.1f}点 {tag}")

    # MM 陷阱
    if traps:
        lines.append("")
        lines.append("=== MM 陷阱信号 ===")
        for t in traps[:max_traps]:
            lines.append(f"  {t['description']}")

    return "\n".join(lines)


# ============================================================
# 11. 便捷函数：从 MT5 拉数据并分析
# ============================================================

def analyze_from_mt5(symbol='XAUUSD', timeframe_min=5, days=5, **kwargs):
    """
    直接从 MT5 拉取数据并生成全量报告。
    需要：pip install MetaTrader5 (Windows only)
    需要：MT5 终端已运行并登录

    参数:
        symbol: 品种名 (默认 'XAUUSD')
        timeframe_min: K线周期分钟数 (默认 5)
        days: 拉取天数 (默认 5)
        **kwargs: 传递给 full_report() 的参数

    返回:
        同 full_report() 的返回格式，增加 'mt5_error' 字段
    """
    try:
        import MetaTrader5 as mt5
    except ImportError:
        return {'error': 'MetaTrader5 未安装。请在 Windows 上运行: pip install MetaTrader5'}

    if not mt5.initialize():
        return {'error': f'MT5 初始化失败: {mt5.last_error()}'}

    from datetime import datetime, timedelta
    import pytz

    # 时间范围
    end = datetime.now(pytz.UTC)
    start = end - timedelta(days=days)

    # 时间框架映射
    tf_map = {1: mt5.TIMEFRAME_M1, 5: mt5.TIMEFRAME_M5,
              15: mt5.TIMEFRAME_M15, 30: mt5.TIMEFRAME_M30,
              60: mt5.TIMEFRAME_H1, 240: mt5.TIMEFRAME_H4,
              1440: mt5.TIMEFRAME_D1}
    tf = tf_map.get(timeframe_min, mt5.TIMEFRAME_M5)

    rates = mt5.copy_rates_range(symbol, tf, start, end)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        return {'error': f'未获取到 {symbol} 数据'}

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    result = full_report(df, **kwargs)
    return result


# ============================================================
# 直接运行时的测试
# ============================================================

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        print("Usage: python price_action_analyzer.py <csv_file>")
        print("  The CSV must have columns: time, open, high, low, close")
        sys.exit(1)
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    result = full_report(df)
    print(result['report'])
