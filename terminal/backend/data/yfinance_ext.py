import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import random

import os

class MarketDataProvider:
    def __init__(self, av_api_key=None):
        # Priority: 1. Constructor arg, 2. Env Var, 3. Hardcoded default
        self.av_api_key = av_api_key or os.getenv("AV_API_KEY", "ZJKLZGW09C7FZO9U")

    def get_performance_matrix(self, symbol: str):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            if hist.empty: return {"1W":0, "1M":0, "3M":0, "YTD":0, "1Y":0}
            current = hist['Close'].iloc[-1]
            def get_ret(days):
                if len(hist) < days: return 0
                past = hist['Close'].iloc[-days]
                return ((current - past) / past) * 100
            ytd_hist = hist[hist.index >= f"{datetime.now().year}-01-01"]
            ytd = ((current - ytd_hist['Close'].iloc[0]) / ytd_hist['Close'].iloc[0] * 100) if not ytd_hist.empty else 0
            return {"1W": get_ret(5), "1M": get_ret(21), "3M": get_ret(63), "YTD": ytd, "1Y": get_ret(252)}
        except: return {"1W":0, "1M":0, "3M":0, "YTD":0, "1Y":0}

    def get_order_book(self, price: float):
        if not price or price == 0: price = 150.0
        bids = [{"price": price - (i * 0.05 + random.uniform(0, 0.02)), "size": random.randint(100, 2000)} for i in range(5)]
        asks = [{"price": price + (i * 0.05 + random.uniform(0, 0.02)), "size": random.randint(100, 2000)} for i in range(5)]
        return {"bids": bids, "asks": asks}

    def get_watchlist_data(self, tickers: list):
        data = []
        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                price = info.get('regularMarketPrice') or info.get('currentPrice') or 0
                prev = info.get('previousClose') or price
                cp = ((price - prev) / prev * 100) if prev else 0
                data.append({
                    "Symbol": symbol,
                    "Name": info.get('shortName', 'N/A'),
                    "Price": price,
                    "Change": price - prev,
                    "Pct": cp,
                    "Mkt Cap": self._format_market_cap(info.get('marketCap')),
                    "Sector": info.get('sector', 'TECH'),
                    "Raw Change %": cp
                })
            except: continue
        return data

    def get_full_analysis(self, symbol: str):
        try:
            t = yf.Ticker(symbol)
            info = t.info
            if not info: return None
            return {
                "Profile": {
                    "Name": info.get('shortName', symbol),
                    "Summary": info.get('longBusinessSummary', 'N/A'),
                    "Website": info.get('website', 'N/A'),
                    "HQ": f"{info.get('city', 'N/A')}, {info.get('country', 'N/A')}",
                    "Employees": f"{info.get('fullTimeEmployees', 0):,}",
                },
                "Estimates": {
                    "P/E": f"{info.get('trailingPE', 0):.1f}",
                    "Est P/E": f"{info.get('forwardPE', 0):.1f}",
                    "EPS": f"{info.get('trailingEps', 0):.2f}",
                    "PEG": f"{info.get('pegRatio', 0):.2f}",
                },
                "Ratios": {
                    "Profit Margin": f"{info.get('profitMargins', 0)*100:.1f}%",
                    "ROE": f"{info.get('returnOnEquity', 0)*100:.1f}%",
                    "ROA": f"{info.get('returnOnAssets', 0)*100:.1f}%",
                    "Current Ratio": f"{info.get('currentRatio', 0):.2f}"
                },
                "Management": [{"name": off.get('name', 'N/A'), "title": off.get('title', 'N/A')} for off in (info.get('companyOfficers', []) or [])[:3]],
                "Price": info.get('currentPrice', 0)
            }
        except: return None

    def get_sector_data(self):
        sectors = {"XLK": "TECH", "XLE": "ENER", "XLF": "FINN", "XLV": "HLTH", "XLY": "CONS", "XLI": "INDU", "XLC": "COMM", "XLB": "MATS"}
        data = []
        for sym, name in sectors.items():
            try:
                t = yf.Ticker(sym).fast_info
                cp = ((t.last_price - t.previous_close) / t.previous_close) * 100
                data.append({"name": name, "pct": cp})
            except: continue
        return data

    def get_indices(self):
        indices = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "DOW J"}
        data = []
        for sym, name in indices.items():
            try:
                t = yf.Ticker(sym).fast_info
                cp = ((t.last_price - t.previous_close) / t.previous_close) * 100
                data.append({"name": name, "price": f"{t.last_price:,.0f}", "pct": f"{cp:+.2f}%", "raw_pct": cp})
            except: continue
        return data

    def get_history(self, symbol: str):
        try:
            h = yf.Ticker(symbol).history(period="6mo")
            return h['Close'].tolist() if not h.empty else []
        except: return []

    def get_av_news(self, symbol: str):
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.av_api_key}"
        try:
            r = requests.get(url); d = r.json()
            return [{"title": i['title'], "source": i['source'], "time": i['time_published'][9:13]} for i in d.get("feed", [])[:5]]
        except: return []

    def _format_market_cap(self, val):
        if not val: return "N/A"
        if val >= 1e12: return f"{val/1e12:.2f}T"
        if val >= 1e9: return f"{val/1e9:.1f}B"
        return f"{val/1e6:.0f}M"
