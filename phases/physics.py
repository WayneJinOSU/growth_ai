"""
Phase 5: The Physics of VPA (量价物理学) - V3.5 Singularity
===========================================================
废弃滞后指标，捕捉机构进场的瞬间。
基于 FMP 原始 OHLCV 数据进行本地计算。

核心公式:
1. SMA20 (生命线)
2. RVol (相对成交量) = Vol / Avg_Vol_20
3. Ignition (点火) = Price > SMA20 + RVol > 2.0 + Strong Close
4. Accumulation (吸筹) = Range < 2% + RVol > 1.5
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from tools.fmp import FMPClient
from core.data_models import PhysicsData
import config

class Physics:
    """
    量价物理学引擎
    """
    
    def __init__(self, fmp_client: FMPClient):
        self.fmp = fmp_client

    def analyze(self, ticker: str) -> PhysicsData:
        print(f"  [Phase 5] Physics VPA Analysis for {ticker} (V3.5)...")
        
        # 1. Fetch Raw Data (OHLCV)
        # Need enough data for SMA20 + some buffer
        raw_data = self.fmp.get_historical_price_daily(ticker, days=60)
        
        if not raw_data or len(raw_data) < 25:
            print("      [Warning] Insufficient historical data for Physics analysis.")
            return PhysicsData(details="Insufficient Data")
            
        # Convert to DataFrame for easier calc
        # FMP returns list of dicts: {'date': '...', 'open': ...}
        # Sorted by date descending usually? FMP 'historical' is usually new to old.
        # We need chronological for rolling calc.
        
        df = pd.DataFrame(raw_data)
        # Ensure date sorting (Oldest to Newest for calc)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=True)
        
        # 2. Calculate Indicators
        # SMA 20
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Avg Volume 20
        df['vol_ma_20'] = df['volume'].rolling(window=20).mean()
        
        # RVol
        # Avoid division by zero
        df['rvol'] = df.apply(lambda row: row['volume'] / row['vol_ma_20'] if row['vol_ma_20'] > 0 else 1.0, axis=1)
        
        # Price Range % (High - Low) / Open
        df['range_pct'] = (df['high'] - df['low']) / df['open']
        
        # Close Location (0.0 = Low, 1.0 = High)
        df['close_loc'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # 3. Analyze Latest Candle (The "Now")
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        data = PhysicsData()
        data.current_price = latest['close']
        data.sma_20 = latest['sma_20']
        data.relative_volume = latest['rvol']
        
        print(f"      Price: ${latest['close']:.2f} | SMA20: ${latest['sma_20']:.2f}")
        print(f"      RVol: {latest['rvol']:.1f}x (Vol: {latest['volume']/1e6:.1f}M)")
        
        # ========== Signal Detection ==========
        
        # A. Ignition (强力点火)
        # Rules: Price > SMA20, Breakout (Price > Prev Close?), RVol > 2.0, Strong Close (>0.8)
        # Also maybe breakout of SMA20? Or just above it.
        # "股价放量突破 SMA20" -> Cross over? Or just above.
        # Let's say: Close > SMA20 AND (Close > Prev Close) AND RVol > 2.0 AND CloseLoc > 0.7
        is_above_sma = latest['close'] > latest['sma_20']
        is_green = latest['close'] > latest['open'] # or > prev close
        is_strong_close = latest['close_loc'] > 0.7
        is_high_vol = latest['rvol'] > config.RVOL_IGNITION
        
        if is_above_sma and is_green and is_strong_close and is_high_vol:
            data.is_ignition = True
            print("      🚀 IGNITION DETECTED (High Vol Breakout)")
            
        # B. Accumulation (机构吸筹)
        # Rules: Range < 2%, RVol > 1.5
        is_tight_range = latest['range_pct'] < config.ACCUMULATION_RANGE_PCT
        is_acc_vol = latest['rvol'] > config.RVOL_ACCUMULATION
        
        if is_tight_range and is_acc_vol:
            data.is_accumulation = True
            print("      🔋 ACCUMULATION DETECTED (Quiet Accumulation)")
            
        # C. Broken Trend (Risk Control)
        # Rule: Close < SMA20 for 3 consecutive days
        # Get last 3 rows
        last_3 = df.tail(3)
        below_sma_count = sum(row['close'] < row['sma_20'] for _, row in last_3.iterrows())
        if below_sma_count == 3:
            data.is_broken_trend = True
            print("      ⚠️ BROKEN TREND: Close < SMA20 for 3 days")
            
        data.details = f"RVol {latest['rvol']:.1f}x"
        
        return data
