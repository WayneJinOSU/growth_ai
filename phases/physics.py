"""
Phase 7: The Physics of VPA (量价物理学) - V3.5 Blue Sky Edition
===========================================================
废弃滞后指标，捕捉机构进场的瞬间。
基于 FMP 原始 OHLCV 数据进行本地计算。

均线铁律: SMA20 (20日线) 是生命线。线下不买，线上不卖。

核心形态:
1. Accumulation (吸筹) - 底部横盘，振幅极小，RVol > 1.5
2. Ignition (点火) - 放量突破 SMA20，RVol > 2.0，收盘价在最高点
3. Broken Trend (破位) - 收盘价跌破 SMA20 且 3 日内无法收回
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from tools.llm import LLMClient
from tools.fmp import FMPClient
from tools.json_parser import JSONParser
from core.data_models import PhysicsData
import config
from tools.lang import get_lang_instruction

class Physics:
    """
    量价物理学引擎
    """
    
    def __init__(self, fmp_client: FMPClient = None, llm_client: Optional[LLMClient] = None):
        self.fmp = fmp_client or FMPClient()
        self.llm = llm_client

    def analyze(self, data_obj) -> PhysicsData:
        ticker = data_obj.ticker
        print(f"  [Phase 7] Physics VPA Analysis for {ticker} (V3.5 Blue Sky)...")
        
        # 1. Fetch Raw Data (OHLCV)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        raw_data = self.fmp.get_historical_price_daily(ticker, from_date=start_date, to_date=end_date)
        
        if not raw_data or len(raw_data) < 25:
            print("      [Warning] Insufficient historical data for Physics analysis.")
            return PhysicsData(details="Insufficient Data")
            
        df = pd.DataFrame(raw_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=True)
        
        # Base Calculation
        data = self._calculate_technical_metrics(df)
        
        # 4. LLM-Enhanced Analysis (Physical Dynamics)
        if self.llm:
            print(f"      [AI] Performing Physical Dynamics analysis with Gemini-3-Pro...")
            ai_data = self._analyze_with_ai(ticker, lang_instruction=get_lang_instruction(data_obj))
            if ai_data:
                data.ai_analysis = ai_data.get('analysis')
                data.ai_conclusion = ai_data.get('conclusion')
                data.ai_recommendation = ai_data.get('recommendation')
                
                # Align indicators if AI detected specific signals
                if data.ai_conclusion:
                    conclusion_lower = data.ai_conclusion.lower()
                    if "ignition" in conclusion_lower: data.is_ignition = True
                    if "broken trend" in conclusion_lower: data.is_broken_trend = True
                    if "accumulation" in conclusion_lower: data.is_accumulation = True
        
        return data

    def _calculate_technical_metrics(self, df: pd.DataFrame) -> PhysicsData:
        # Move existing logic here
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean() # V3.5 New for Mid-Large Cap
        df['sma_200'] = df['close'].rolling(window=200).mean() # V3.5 New
        df['vol_ma_20'] = df['volume'].rolling(window=20).mean()
        df['rvol'] = df.apply(lambda row: row['volume'] / row['vol_ma_20'] if row['vol_ma_20'] > 0 else 1.0, axis=1)
        df['range_pct'] = (df['high'] - df['low']) / df['open']
        df['close_loc'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        latest = df.iloc[-1]
        data = PhysicsData()
        data.current_price = latest['close']
        data.sma_20 = latest['sma_20']
        data.sma_50 = latest.get('sma_50', None)
        data.sma_200 = latest.get('sma_200', None)
        data.relative_volume = latest['rvol']
        data.daily_range = latest['range_pct']
        data.close_strength = latest['close_loc']
        
        # Signal Detection
        is_above_sma = latest['close'] > latest['sma_20']
        is_green = latest['close'] > latest['open']
        is_strong_close = latest['close_loc'] > 0.7
        is_high_vol = latest['rvol'] > config.RVOL_IGNITION
        
        if is_above_sma and is_green and is_strong_close and is_high_vol:
            data.is_ignition = True
        
        is_tight_range = latest['range_pct'] < config.ACCUMULATION_RANGE_PCT
        is_acc_vol = latest['rvol'] > config.RVOL_ACCUMULATION
        if is_tight_range and is_acc_vol:
            data.is_accumulation = True
            
        last_3 = df.tail(3)
        below_sma20_count = sum(row['close'] < row['sma_20'] for _, row in last_3.iterrows())
        data.days_below_sma20 = below_sma20_count
        
        # V3.5 Mid-Large Cap Modification: Use SMA 50 for trend breakdown
        if 'sma_50' in last_3.columns and not pd.isna(last_3['sma_50'].iloc[-1]):
            below_sma50_count = sum(row['close'] < row['sma_50'] for _, row in last_3.iterrows())
            data.days_below_sma50 = below_sma50_count
            if below_sma50_count >= 3:
                data.is_broken_trend = True
        else:
            # Fallback to SMA20 if not enough data for 50 days
            if below_sma20_count >= 3:
                data.is_broken_trend = True
            
        data.details = f"RVol {latest['rvol']:.1f}x | Range {latest['range_pct']*100:.1f}% | Close Strength {latest['close_loc']:.1%}"
        return data

    def _analyze_with_ai(self, ticker: str, lang_instruction: str = "") -> Optional[Dict]:
        # Prepare data snippet for LLM
        # Last 40 days is usually enough for daily chart context
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        raw_data = self.fmp.get_historical_price_daily(ticker, from_date=start_date, to_date=end_date)

        prompt = f"""
        Adopt the perspective of "Physical Dynamics" (Technical Dynamics) to analyze the stock {ticker} based on the following 40-day trading data (JSON format):
        {raw_data}
        
        Analytical Framework:
        1. Kinematics (Motion Analysis): Trends, speed, acceleration, and momentum.
        2. Dynamics (Force Analysis): Volume as mass/inertia. Analyze force of buyers vs sellers.
        3. Statics (Structure Analysis): Support/Resistance levels (the "floor" and "ceiling").
        4. Energy Conservation (VWAP/Deviation): Over-extension or mean reversion.

        Output Requirements (STRICTLY FOLLOW):
        Reply ONLY with a valid JSON object matching the following structure:
        {{
            "conclusion": "Ignition, Broken Trend, Accumulation, Divergence, Volatility Trap, or Neutral",
            "recommendation": "Strong Buy, Buy, Wait, Observe, or Sell",
            "analysis": "Detailed analysis using physical metaphors"
        }}
        {lang_instruction}
        """
        
        response = self.llm.analyze_text(prompt, system_prompt="You are a senior technical analyst. Respond strictly with JSON.")
        if not response:
            return None
        ai_data = JSONParser.parse_llm_json(response, default={})
        return {
            "conclusion": ai_data.get("conclusion", "Neutral").replace('*', ''),
            "recommendation": ai_data.get("recommendation", "Wait").replace('*', ''),
            "analysis": ai_data.get("analysis", "Analysis parsing failed.")
        }

physics = Physics()

if __name__ == "__main__":
    from core.data_models import CompanyData
    fmp = FMPClient()
    llm = LLMClient()
    p = Physics(fmp, llm)
    test_data = CompanyData(ticker='AXON')
    print(p.analyze(test_data))


