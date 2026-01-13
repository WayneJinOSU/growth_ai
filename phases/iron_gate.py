"""
Phase 1: The Iron Gate (铁律筛选)
================================
通过纯粹的数学纪律，剔除 90% 的不合格标的。此阶段不带任何感情色彩，只看客观数据。

核心检查项:
1. 20% 黄金分割线 - CAGR 和季度增速
2. 减速预警 - 增速骤降检测
3. 盈利路径二分法 - 盈利公司看 PEG，未盈利公司看毛利斜率和运营杠杆
"""

import numpy as np
from typing import List
from tools.fmp import FMPClient
from core.data_models import IronGateMetrics
import config


class IronGate:
    """
    铁律筛选器：MGP 策略的第一道关卡

    职责：
    - 获取财务数据 (年报、季报、估值比率)
    - 计算 CAGR、季度增速、PEG、毛利斜率等核心指标
    - 根据阈值判断是否通过筛选
    """

    def __init__(self, fmp_client: FMPClient):
        self.fmp = fmp_client

    def _calculate_cagr(self, start_value: float, end_value: float, years: int) -> float:
        """
        计算复合年均增长率 (CAGR - Compound Annual Growth Rate)

        公式: CAGR = (终值 / 起值) ^ (1/年数) - 1

        示例:
            起值=100, 终值=150, 年数=3
            CAGR = (150/100)^(1/3) - 1 = 14.47%

        Args:
            start_value: 起始年度的值 (如 3 年前的营收)
            end_value: 结束年度的值 (如 当前营收)
            years: 跨越的年数

        Returns:
            CAGR 比率 (如 0.1447 表示 14.47%)
        """
        if start_value <= 0 or years <= 0:
            return 0.0
        return (end_value / start_value) ** (1 / years) - 1

    def _calculate_slope(self, values: List[float]) -> float:
        """
        计算数据序列的线性回归斜率

        用于判断毛利率是否呈上升趋势 (正斜率) 或下降趋势 (负斜率)

        Args:
            values: 按时间顺序排列的数值列表 (从旧到新)

        Returns:
            斜率值，正数表示上升趋势，负数表示下降趋势
        """
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        y = np.array(values)
        # np.polyfit 返回 [斜率, 截距]
        slope, _ = np.polyfit(x, y, 1)
        return slope

    def analyze(self, ticker: str) -> IronGateMetrics:
        """
        对单只股票执行铁律筛选分析

        分析流程:
        1. 获取年度和季度财务数据
        2. 计算 CAGR (复合年均增长率)
        3. 计算当季同比增速
        4. 检测增速减速预警
        5. 根据盈利状态选择不同的估值检查路径

        Args:
            ticker: 股票代码 (如 "AAPL", "SNOW")

        Returns:
            IronGateMetrics: 包含所有计算指标和通过/失败状态
        """
        # ========== 从配置中读取参数 ==========
        cagr_years = config.CAGR_YEARS  # CAGR 计算年限 (默认 3 年)
        quarters_for_decel = config.QUARTERS_FOR_DECEL_CHECK  # 减速预警需要的季度数 (默认 9)
        quarters_for_yoy = config.QUARTERS_FOR_YOY  # 同比增速需要的季度数 (默认 5)
        quarters_for_margin = config.QUARTERS_FOR_MARGIN_SLOPE  # 毛利斜率计算季度数 (默认 6)
        quarters_for_ni = config.QUARTERS_FOR_NI_SUM  # TTM 净利润求和季度数 (默认 4)

        # ========== 获取财务数据 ==========
        # 年度利润表: 用于计算 CAGR
        income_annual = self.fmp.get_income_statement(ticker, period='annual', limit=cagr_years + 1)
        # 季度利润表: 用于计算同比增速、减速预警、毛利斜率等
        income_quarterly = self.fmp.get_income_statement(ticker, period='quarter', limit=quarters_for_decel)
        # TTM 估值比率: 用于获取 PE、PEG 等
        ratios_ttm = self.fmp.get_ratios_ttm(ticker)
        # 实时报价: 用于获取当前股价
        quote = self.fmp.get_quote(ticker)

        metrics = IronGateMetrics()

        # ========== 数据完整性检查 ==========
        if not income_annual or len(income_annual) < 2:
            # 数据不足时，不直接判负，而是将 CAGR 标记为 None，后续仅依赖季度增速判断
            cagr_valid = False
            metrics.revenue_cagr_5y = None
        else:
            cagr_valid = True

        # ========== 1. CAGR 计算 (20% 黄金分割线 - 长期检验) ==========
        # 检验公司是否具备"长跑能力"，而非昙花一现
        if cagr_valid:
            try:
                latest_rev = income_annual[0]['revenue']  # 最新年度营收
                old_rev = income_annual[-1]['revenue']  # N 年前营收
                years = len(income_annual) - 1  # 实际跨越年数
                cagr = self._calculate_cagr(old_rev, latest_rev, years)
                metrics.revenue_cagr_5y = cagr  # 字段名保留兼容性 (实际按 config 配置)
            except Exception:
                metrics.revenue_cagr_5y = None
                cagr_valid = False


        # ========== 2. 当季同比增速 (20% 黄金分割线 - 动能检验) ==========
        if not income_quarterly or len(income_quarterly) < quarters_for_yoy:
            metrics.passed = False
            metrics.fail_reason = f"Insufficient quarterly data (need {quarters_for_yoy})"
            return metrics

        try:
            # Q0 vs Q-4: 当前季度 vs 去年同期
            current_rev = income_quarterly[0]['revenue']
            prev_year_q_rev = income_quarterly[quarters_for_yoy - 1]['revenue']
            current_growth = (current_rev - prev_year_q_rev) / prev_year_q_rev
            metrics.revenue_growth_current_q = current_growth

            # ========== 3. 减速预警 (Deceleration Alarm) ==========
            # 比较: 今年增速 vs 去年同期增速
            # 如果增速从 60% 骤降至 25% (跌幅超过一半)，视为"成长逻辑破损"
            decel_index = quarters_for_decel - 1  # Q-8 的索引位置
            prev_rev = income_quarterly[quarters_for_yoy - 1]['revenue']  # Q-4 营收
            prev_prev_rev = income_quarterly[decel_index]['revenue'] if len(
                income_quarterly) > decel_index else 0  # Q-8 营收

            if prev_prev_rev > 0:
                # 去年同期的增速: (Q-4 - Q-8) / Q-8
                prev_growth = (prev_rev - prev_prev_rev) / prev_prev_rev
                metrics.revenue_growth_prev_y_q = prev_growth
            else:
                # 数据不足时，假设增速稳定
                metrics.revenue_growth_prev_y_q = current_growth
        except Exception as e:
            metrics.passed = False
            metrics.fail_reason = f"Data Error: {str(e)}"
            return metrics

        # ========== 阈值检查: 增长率 ==========
        # 白皮书: "如果 CAGR < 20% 且 当季增速 < 20%，直接淘汰"
        # 改进逻辑: 如果没有 CAGR 数据 (新股)，仅检查季度增速
        
        passed_growth_gate = False
        
        if metrics.revenue_cagr_5y is None:
             # Case 1: 新股 (无 CAGR)，仅看爆发力
            if metrics.revenue_growth_current_q >= config.GROWTH_THRESHOLD_QUARTER:
                passed_growth_gate = True
            else:
                metrics.fail_reason = f"Low Growth (New IPO): Q_Growth {metrics.revenue_growth_current_q:.1%} < {config.GROWTH_THRESHOLD_QUARTER:.1%}"
        else:
            # Case 2: 老股，看长跑能力 OR 爆发力 (二者满足其一即可)
            if (metrics.revenue_cagr_5y >= config.GROWTH_THRESHOLD_CAGR) or \
               (metrics.revenue_growth_current_q >= config.GROWTH_THRESHOLD_QUARTER):
                passed_growth_gate = True
            else:
                metrics.fail_reason = f"Low Growth: CAGR {metrics.revenue_cagr_5y:.1%}, Q_Growth {metrics.revenue_growth_current_q:.1%}"

        if not passed_growth_gate:
            metrics.passed = False
            return metrics

        # ========== 阈值检查: 减速预警 ==========
        # 只有当前期增速 > 40% 时才检测减速 (高增长股才有减速风险)
        if metrics.revenue_growth_prev_y_q and metrics.revenue_growth_prev_y_q > config.DECEL_PREV_GROWTH_THRESHOLD:
            # 如果增速下降超过 50%，触发警报
            if metrics.revenue_growth_current_q < (metrics.revenue_growth_prev_y_q * config.DECEL_DROP_RATIO):
                metrics.passed = False
                metrics.fail_reason = f"Deceleration Alarm: {metrics.revenue_growth_prev_y_q:.1%} -> {metrics.revenue_growth_current_q:.1%}"
                return metrics

        # ========== 4. 盈利路径二分法 (Profitability Bifurcation) ==========
        # 盈利公司和未盈利公司采用两套完全不同的生存标准

        # 判断是否实质盈利: 
        # 旧逻辑: TTM 净利润 > 0 即为盈利
        # 新逻辑: TTM 净利率 > 3% 才算实质盈利 (微利企业归入未盈利组)
        
        is_profitable = False
        ttm_net_margin = 0.0
        
        if ratios_ttm:
            ttm_net_margin = ratios_ttm.get('netProfitMarginTTM', 0)
        
        # 即使没有 ratios_ttm，也可以手动计算 margin (可选优化，暂时依赖 ratios)
        
        if ttm_net_margin > config.MIN_NET_MARGIN_FOR_PEG:
            is_profitable = True

        if is_profitable:
            # ========== A 类: 已盈利公司 - 检查 PEG ==========
            # PEG = PE / Growth Rate
            # PEG < 1.0 极度低估, PEG > 2.0 泡沫风险

            pe = ratios_ttm.get('peRatioTTM') if ratios_ttm else None
            if pe is None:
                # 备用计算: PE = 股价 / TTM EPS
                eps = sum(q['eps'] for q in income_quarterly[:quarters_for_ni])
                price = quote.get('price') if quote else 0
                if eps > 0 and price > 0:
                    pe = price / eps

            # 使用营收增速作为 Growth Rate (高增长科技股 EPS 可能波动大)
            growth_rate = metrics.revenue_growth_current_q * 100  # 转换为百分比数值

            # 优先使用 FMP 提供的 PEG
            peg = ratios_ttm.get('pegRatioTTM') if ratios_ttm else None

            # 如果 FMP 没有 PEG，手动计算
            if not peg and pe and growth_rate > 0:
                peg = pe / growth_rate

            metrics.peg_ratio = peg

            # PEG 阈值检查
            if peg and peg > config.PEG_THRESHOLD_BUBBLE:
                metrics.passed = False
                metrics.fail_reason = f"PEG too high: {peg:.2f} (threshold: {config.PEG_THRESHOLD_BUBBLE})"
                return metrics
        else:
            # ========== B 类: 未盈利公司 - 证明"烧钱是有意义的" ==========

            # --- 检查 1: 毛利率斜率 (Gross Margin Slope) ---
            # 过去 4-6 个季度，毛利率必须呈现上升趋势
            # 这证明了规模效应的存在 (卖得越多，单位成本越低)
            margins = []
            for q in reversed(income_quarterly[:quarters_for_margin]):  # 从旧到新排列
                if q['revenue'] > 0:
                    gm = q['grossProfit'] / q['revenue']  # 毛利率 = 毛利 / 营收
                    margins.append(gm)

            slope = self._calculate_slope(margins)
            metrics.gross_margin_slope = slope

            # 斜率检查: 必须为正 (上升趋势)，允许轻微噪音
            if slope < config.GROSS_MARGIN_SLOPE_TOLERANCE:
                metrics.passed = False
                metrics.fail_reason = f"Gross Margin Declining (Slope: {slope:.4f})"
                return metrics

            # --- 检查 2: 运营杠杆 (Operating Leverage) ---
            # 营收增速必须快于运营费用 (OpEx) 增速
            # 这证明公司在扩张过程中效率在提升
            curr_opex = income_quarterly[0]['operatingExpenses']
            old_opex = income_quarterly[quarters_for_yoy - 1]['operatingExpenses']
            opex_growth = (curr_opex - old_opex) / old_opex if old_opex > 0 else 0

            metrics.opex_growth = opex_growth
            metrics.operating_leverage = metrics.revenue_growth_current_q > opex_growth

            if not metrics.operating_leverage:
                metrics.passed = False
                metrics.fail_reason = f"No Operating Leverage: Rev {metrics.revenue_growth_current_q:.1%} < OpEx {opex_growth:.1%}"
                return metrics

        # ========== 全部检查通过 ==========
        metrics.passed = True
        return metrics
