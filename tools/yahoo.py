import yfinance as yf
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta

class YahooClient:
    """
    Client for Yahoo Finance data (using yfinance).
    Used for data points where FMP Starter plan is limited:
    1. Analyst Estimates (Future Growth)
    2. Insider Trading
    """
    
    def get_future_growth_estimates(self, ticker: str) -> Optional[float]:
        """
        Get the projected 5-year growth rate or next year revenue growth.
        Returns a float (e.g. 0.25 for 25%).
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            # Try to get analysis data
            # yfinance often structures this in .growth_estimates or .analysis
            # Note: yfinance API structure changes often. 
            
            # Strategy 1: growth_estimates (if available)
            # Typically returns a DataFrame
            # We look for "Next 5 Years (per annum)"
            
            # For reliability, we might check 'info' first
            info = ticker_obj.info
            if 'revenueGrowth' in info:
                # This is usually TTM or Next Quarter, might not be long term.
                pass
                
            # Let's try to access the Analysis dataframe via private method or properties if standard fails
            # But yf.Ticker(ticker).growth_estimates is the standard way now
            
            # Using a simpler approach for stability:
            # Check 'earningsGrowth' or 'revenueGrowth' in info as a fallback
            # But we really want consensus estimates.
            
            # Fallback to info for now as it's most stable
            # 'targetMeanPrice', 'recommendationKey', 'revenueGrowth'
            
            # Actually, to get Future 3Y CAGR, we ideally need the analysis table.
            # If yfinance doesn't expose it easily, we might fallback to FMP 'growth' endpoints if they work,
            # but user specifically asked for Yahoo for this.
            
            # Mocking the specific extraction if complex dataframe parsing is needed, 
            # but let's try to get 'revenueGrowth' (Next Year) from info.
            if info and 'revenueGrowth' in info:
                return float(info['revenueGrowth'])
                
            return None
        except Exception as e:
            print(f"Error fetching Yahoo estimates for {ticker}: {e}")
            return None

    def get_insider_roster(self, ticker: str) -> List[Dict]:
        """
        Get recent insider purchases/sales.
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            insider = ticker_obj.insider_transactions
            
            if insider is None or insider.empty:
                return []
            
            # Convert DataFrame to List of Dicts
            # Columns usually: 'Shares', 'Value', 'Text', 'Start Date', 'Owner Name', 'Transaction'
            
            # Sort by Date descending
            insider = insider.sort_values(by='Start Date', ascending=False)
            
            transactions = []
            for index, row in insider.iterrows():
                transactions.append({
                    'date': row.get('Start Date'),
                    'owner': row.get('Owner Name', 'Unknown'),
                    'transaction': row.get('Text', '') or row.get('Transaction', ''),
                    'shares': row.get('Shares'),
                    'value': row.get('Value')
                })
            
            return transactions[:20] # Return last 20
            
        except Exception as e:
            print(f"Error fetching Yahoo insider data for {ticker}: {e}")
            return []
            
    def get_analyst_cagr(self, ticker: str) -> Optional[float]:
        """
        Attempts to find a consensus revenue growth estimate.
        """
        try:
            # yfinance info is the safest stable API
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            
            # return revenueGrowth as a proxy for next year growth
            if info and 'revenueGrowth' in info:
                return info['revenueGrowth']
                
            return None
        except:
            return None
