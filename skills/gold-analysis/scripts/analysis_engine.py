"""黄金分析引擎 —— 独立于展示层的分析服务。

可以被多种消费者调用：
- Streamlit 看板 (dashboard.py)
- CLI 命令行 (python analysis_engine.py)
- 定时任务 / cron
- 外部 API / webhook

用法:
    from analysis_engine import AnalysisEngine
    engine = AnalysisEngine()
    prompts = engine.prepare()  # 获取 prompts
    # agent 用自己的模型生成分析文本...
    result = engine.finalize(agent_output)
    print(result.to_json())
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

try:
    from dotenv import load_dotenv
    load_dotenv(_scripts_dir.parent / ".env")
except ImportError:
    pass

from config import SYMBOL, TIMEFRAME, LOOKBACK_DAYS, M5_BARS_PER_DAY
from data_fetcher import DataFetcher
from llm_analyzer import build_prompt, parse_response, calc_atr
from price_action_analyzer import full_report
from schema import GoldAnalysis

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """黄金价格行为分析引擎。

    封装数据获取→算法分析→prompt 构建流水线。
    LLM 调用由 agent（Claude Code）完成，此引擎只负责准备 prompts 和解析响应。

    用法:
        engine = AnalysisEngine()
        prompts = engine.prepare(lookback_days=3)
        # agent 用自己的模型生成分析文本...
        result = engine.finalize(agent_output)
        print(result.to_json())
    """

    def __init__(self):
        self._fetcher: Optional[DataFetcher] = None
        self._last_df = None
        self._last_algo_result = None

    @property
    def fetcher(self) -> DataFetcher:
        if self._fetcher is None:
            self._fetcher = DataFetcher(symbol=SYMBOL)
        return self._fetcher

    @property
    def connected(self) -> bool:
        return self._fetcher is not None and self._fetcher.connected

    def prepare(self, lookback_days: int = LOOKBACK_DAYS) -> Optional[dict]:
        """准备分析：获取数据 + 算法分析 + 构建 prompts。

        Returns:
            dict with keys: system_prompt, user_prompt, metadata,
                           df (DataFrame), algo_result (dict)
            失败返回 None
        """
        # 1. 获取数据
        bar_count = lookback_days * M5_BARS_PER_DAY
        df = self.fetcher.fetch(TIMEFRAME, count=bar_count)
        if df is None or len(df) < 30:
            logger.warning("数据不足，无法分析")
            return None

        # 2. 算法分析
        try:
            algo_result = full_report(df)
        except Exception as e:
            logger.error(f"算法分析失败: {e}")
            return None

        if algo_result is None:
            return None

        # 3. 构建 prompts
        prompts = build_prompt(df, algo_result, lookback_days)

        self._last_df = df
        self._last_algo_result = algo_result
        prompts["df"] = df
        prompts["algo_result"] = algo_result
        return prompts

    def finalize(self, llm_output: str) -> Optional[GoldAnalysis]:
        """解析 agent 的 LLM 输出为 GoldAnalysis。

        Args:
            llm_output: agent 生成的分析文本

        Returns:
            GoldAnalysis 对象，失败返回 None
        """
        df = self._last_df
        if df is None:
            logger.error("no data — call prepare() first")
            return None

        analysis = parse_response(llm_output, df)
        if analysis is None:
            logger.warning("LLM 响应解析失败，返回基础算法结果")
            if self._last_algo_result:
                return self._build_basic_result(df, self._last_algo_result)
            return None

        return analysis

    def run(self, lookback_days: int = LOOKBACK_DAYS,
            skip_llm: bool = False) -> Optional[GoldAnalysis]:
        """便捷方法：prepare + 跳过 LLM 时直接返回算法结果。

        当 skip_llm=True 时直接返回算法分析结果。
        当 skip_llm=False 时返回 prepare() 的 prompts——agent 需要自行
        调用 LLM 并用 finalize() 解析。
        """
        result = self.prepare(lookback_days)
        if result is None:
            return None

        if skip_llm:
            return self._build_basic_result(result["df"], result["algo_result"])

        # 不跳过 LLM 时，返回 None 表示"需要 agent 介入"
        # agent 应读取 result["system_prompt"] 和 result["user_prompt"]
        # 用自己的模型生成分析，然后调用 engine.finalize()
        return None

    def _build_basic_result(self, df, algo_result) -> GoldAnalysis:
        """仅用算法结果构建基础 GoldAnalysis（无 LLM 叙事）。"""
        from schema import (
            MarketStructure, PriceZone, PricePoint, DailySummary,
            NarrativeSection, ChartData,
        )

        analysis = GoldAnalysis()
        analysis.symbol = SYMBOL
        analysis.timeframe = TIMEFRAME
        analysis.generated_at = str(df["time"].iloc[-1])
        analysis.data_range = f"{df['time'].iloc[0].strftime('%m-%d %H:%M')} ~ {df['time'].iloc[-1].strftime('%m-%d %H:%M')}"
        analysis.current_price = float(df["close"].iloc[-1])
        analysis.atr = calc_atr(df)

        trend = algo_result.get("trend", {})
        analysis.structure = MarketStructure(
            state=trend.get("direction", "range"),
            confidence="中",
            summary="（算法分析，无 LLM 解读）",
            hh=trend.get("hh"), hl=trend.get("hl"),
            ll=trend.get("ll"), lh=trend.get("lh"),
        )
        dir_map = {"up": "bullish", "down": "bearish"}
        analysis.direction = dir_map.get(trend.get("direction", ""), "neutral")

        for z in algo_result.get("zones", [])[:6]:
            analysis.key_zones.append(PriceZone(
                lower=z["lower"], upper=z["upper"], mid=z["mid"],
                touches=z["touches"], role=z["role"],
                strength="强" if z["touches"] >= 5 else ("中" if z["touches"] >= 3 else "弱"),
                description="",
                points=[PricePoint(time=str(p["time"]), price=p["price"], type=p["type"])
                        for p in z.get("points", [])[:5]],
            ))

        analysis.chart = ChartData(
            times=[t.strftime("%m-%d %H:%M") for t in df["time"]],
            opens=[float(x) for x in df["open"]],
            highs=[float(x) for x in df["high"]],
            lows=[float(x) for x in df["low"]],
            closes=[float(x) for x in df["close"]],
            zones=analysis.key_zones,
        )

        analysis.narratives = [
            NarrativeSection(
                title="LLM 分析待完成",
                content="agent 尚未调用 LLM 生成解读。请使用 engine.finalize(agent_output) 解析 agent 的分析文本。",
                icon="⏳",
                highlight=True,
            )
        ]

        return analysis

    def get_data(self, lookback_days: int = LOOKBACK_DAYS):
        """仅获取数据（不分析），用于快速查看行情。"""
        bar_count = lookback_days * M5_BARS_PER_DAY
        return self.fetcher.fetch(TIMEFRAME, count=bar_count)

    def prompts_to_file(self, output_dir: Optional[str] = None) -> dict:
        """将 prompts 写入标准文件位置，供 agent 消费。

        在 engine.prepare() 之后调用此方法，将 system_prompt 和 user_prompt
        保存到文件。agent 随后可读取这些文件进行 LLM 推理。

        Args:
            output_dir: 输出目录，默认 skill root 下的 prompts/

        Returns:
            dict with 'system_prompt_path' and 'user_prompt_path' keys，
            如果 prepare() 未调用则返回空 dict
        """
        df = self._last_df
        algo_result = self._last_algo_result
        if df is None or algo_result is None:
            logger.warning("prompts_to_file: 请先调用 prepare()")
            return {}

        from llm_analyzer import build_prompt
        prompts = build_prompt(df, algo_result)
        out = Path(output_dir) if output_dir else _scripts_dir.parent / "prompts"
        out.mkdir(parents=True, exist_ok=True)

        system_path = out / "system_prompt.md"
        user_path = out / "user_prompt.md"
        system_path.write_text(prompts["system_prompt"], encoding="utf-8")
        user_path.write_text(prompts["user_prompt"], encoding="utf-8")
        logger.info(f"Prompts 已保存: {system_path}, {user_path}")
        return {
            "system_prompt_path": str(system_path),
            "user_prompt_path": str(user_path),
            "system_prompt": prompts["system_prompt"],
            "user_prompt": prompts["user_prompt"],
        }

    def save_intermediate(self, output_path: Optional[str] = None) -> str:
        """保存算法中间结果到 intermediate_result.json（供看板加载阶段展示）。

        在 engine.prepare() 之后调用，将算法分析结果（不含 LLM 叙事）
        写入 JSON 文件。看板检测到 intermediate_result.json 后，
        可先展示算法结果并显示"等待 Agent 分析"状态。

        Args:
            output_path: 输出路径，默认 skill root/intermediate_result.json

        Returns:
            实际写入的文件路径，prepare() 未调用时返回空字符串
        """
        df = self._last_df
        algo_result = self._last_algo_result
        if df is None or algo_result is None:
            logger.warning("save_intermediate: 请先调用 prepare()")
            return ""

        basic = self._build_basic_result(df, algo_result)
        path = Path(output_path) if output_path else _scripts_dir.parent / "intermediate_result.json"
        payload = {
            "symbol": SYMBOL,
            "timeframe": TIMEFRAME,
            "generated_at": basic.generated_at,
            "current_price": basic.current_price,
            "atr": basic.atr,
            "data_range": basic.data_range,
            "direction": basic.direction,
            "structure": {
                "state": basic.structure.state,
                "confidence": basic.structure.confidence,
                "summary": basic.structure.summary,
                "hh": basic.structure.hh,
                "hl": basic.structure.hl,
                "ll": basic.structure.ll,
                "lh": basic.structure.lh,
            },
            "key_zones": [
                {"lower": z.lower, "upper": z.upper, "mid": z.mid,
                 "touches": z.touches, "role": z.role, "strength": z.strength,
                 "description": z.description}
                for z in basic.key_zones
            ],
            "chart": basic.chart.to_dict() if basic.chart else {},
            "narratives": [
                {"title": n.title, "content": n.content, "icon": n.icon, "highlight": n.highlight}
                for n in basic.narratives
            ],
            "partial": True,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"中间结果已保存: {path}")
        return str(path)

    def reconnect(self):
        """重新连接 MT5。"""
        if self._fetcher:
            del self._fetcher
            self._fetcher = None
        return self.fetcher


# ═══════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    p = argparse.ArgumentParser(description="XAUUSD 价格行为分析引擎")
    p.add_argument("--days", type=int, default=3, help="分析天数 (默认3)")
    p.add_argument("--skip-llm", action="store_true", help="跳过 LLM 分析，仅输出算法结果")
    p.add_argument("--output", type=str, help="输出 JSON 文件路径")
    p.add_argument("--print", action="store_true", help="打印结果到 stdout")
    p.add_argument("--prompts-only", action="store_true", help="仅输出 prompts，不调用 LLM")
    args = p.parse_args()

    engine = AnalysisEngine()
    print(f"分析引擎启动 | MT5: {'已连接' if engine.connected else '未连接'}")
    print(f"分析窗口: {args.days}天 | LLM: {'跳过' if args.skip_llm else 'agent 驱动'}")

    if args.skip_llm:
        result = engine.run(lookback_days=args.days, skip_llm=True)
        if result is None:
            print("分析失败：数据不足或 MT5 未连接")
            sys.exit(1)
        if args.print:
            print(result.to_json())
        if args.output:
            Path(args.output).write_text(result.to_json(), encoding="utf-8")
            print(f"结果已保存到: {args.output}")
        print(f"完成: direction={result.direction}, price={result.current_price:.2f}, "
              f"zones={len(result.key_zones)}")
    else:
        prompts = engine.prepare(lookback_days=args.days)
        if prompts is None:
            print("数据获取或算法分析失败")
            sys.exit(1)
        print(f"Prompts 已构建: system={prompts['metadata']['system_prompt_chars']}chars, "
              f"user={prompts['metadata']['user_prompt_chars']}chars")
        if args.prompts_only:
            print("\n" + "="*60)
            print("SYSTEM PROMPT:")
            print("="*60)
            print(prompts["system_prompt"])
            print("\n" + "="*60)
            print("USER PROMPT:")
            print("="*60)
            print(prompts["user_prompt"])
        else:
            print("agent 需调用 engine.finalize(agent_output) 完成分析")
            sys.exit(0)
