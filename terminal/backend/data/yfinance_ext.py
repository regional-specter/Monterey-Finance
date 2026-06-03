import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime

class MarketDataProvider:
    def __init__(self, av_api_key="demo"):
        self.av_api_key = av_api_key

    def get_sector_data(self):
        """Fetches major sector performance for the heatmap."""
        sectors = {
            "XLK": "TECH", "XLE": "ENER", "XLF": "FINN", 
            "XLV": "HLTH", "XLY": "CONS", "XLI": "INDU"
        }
        data = []
        for sym, name in sectors.items():
            try:
                t = yf.Ticker(sym).fast_info
                cp = ((t.last_price - t.previous_close) / t.previous_close) * 100
                data.append({"name": name, "pct": cp})
            except: continue
        return data

    def get_ticker_data(self, tickers: list):
        data = []
        for symbol in tickers:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                if not info: continue
                price = info.get('regularMarketPrice') or info.get('currentPrice')
                prev_close = info.get('previousClose')
                change = (price - prev_close) if price and prev_close else 0
                cp = (change / prev_close * 100) if prev_close else 0
                data.append({
                    "Symbol": symbol,
                    "Price": f"{price:.2f}",
                    "Change": f"{change:+.2f}",
                    "Change %": f"{cp:+.2f}%",
                    "Mkt Cap": self._format_market_cap(info.get('marketCap')),
                    "Raw Change %": cp
                })
            except: continue
        return data

    def get_full_analysis(self, symbol: str):
        try:
            t = yf.Ticker(symbol)
            info = t.info
            if not info: return None
            
            # Financial Ratios
            ratios = {
                "Profit Margin": f"{info.get('profitMargins', 0)*100:.2f}%",
                "Oper. Margin": f"{info.get('operatingMargins', 0)*100:.2f}%",
                "ROA": f"{info.get('returnOnAssets', 0)*100:.2f}%",
                "ROE": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                "Current Ratio": f"{info.get('currentRatio', 0):.2f}"
            }

            # Income Statement (Mini)
            income = {
                "Revenue": self._format_market_cap(info.get('totalRevenue')),
                "Gross Profit": self._format_market_cap(info.get('grossProfits')),
                "Net Income": self._format_market_cap(info.get('netIncomeToCommon')),
            }

            # Liquidity
            vol = info.get('regularMarketVolume', 0)
            avg_vol = info.get('averageVolume', 1)
            
            return {
                "Profile": {
                    "Name": info.get('shortName', symbol),
                    "Summary": info.get('longBusinessSummary', 'N/A'),
                    "Website": info.get('website', 'N/A'),
                    "HQ": f"{info.get('city', 'N/A')}, {info.get('country', 'N/A')}",
                    "Employees": f"{info.get('fullTimeEmployees', 0):,}",
                },
                "Ratios": ratios,
                "Income": income,
                "Liquidity": {
                    "Vol": self._format_market_cap(vol),
                    "Avg Vol": self._format_market_cap(avg_vol),
                    "Vol/Avg": f"{vol/avg_vol:.2f}x"
                },
                "Estimates": {
                    "P/E": f"{info.get('trailingPE', 0):.2f}",
                    "Est P/E": f"{info.get('forwardPE', 0):.2f}",
                    "EPS": f"{info.get('trailingEps', 0):.2f}",
                    "PEG": f"{info.get('pegRatio', 0):.2f}",
                },
                "Dividends": {
                    "Yield": f"{info.get('dividendYield', 0)*100:.2f}%",
                    "Rate": f"{info.get('dividendRate', 0):.2f}",
                },
                "Management": [{"name": off.get('name'), "title": off.get('title')} for off in (info.get('companyOfficers', []) or [])[:3]],
                "Stats": {
                    "52W H": info.get('fiftyTwoWeekHigh', 0),
                    "52W L": info.get('fiftyTwoWeekLow', 0),
                    "Price": info.get('currentPrice', 0)
                }
            }
        except: return None

    def calculate_technicals(self, prices):
        if len(prices) < 20: return {"RSI": "N/A", "MA_Signal": "N/A", "MA50": "N/A", "MA200": "N/A"}
        
        # RSI Calculation
        deltas = np.diff(prices)
        up = deltas[deltas >= 0].sum() if len(deltas[deltas >= 0]) > 0 else 0
        down = -deltas[deltas < 0].sum() if len(deltas[deltas < 0]) > 0 else 0
        rs = up / down if down != 0 else 0
        rsi = 100. - (100. / (1. + rs))
        
        # MA Crossover
        ma50 = np.mean(prices[-50:]) if len(prices) >= 50 else 0
        ma200 = np.mean(prices[-200:]) if len(prices) >= 200 else 0
        signal = "BULLISH" if ma50 > ma200 else "BEARISH" if ma50 < ma200 else "NEUTRAL"
        
        return {
            "RSI": f"{rsi:.1f}",
            "MA_Signal": signal,
            "MA50": f"{ma50:.1f}" if ma50 > 0 else "N/A",
            "MA200": f"{ma200:.1f}" if ma200 > 0 else "N/A"
        }

    def get_av_news(self, symbol: str):
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.av_api_key}"
        try:
            r = requests.get(url)
            data = r.json()
            feed = data.get("feed", [])
            news = []
            for item in feed[:8]:
                raw_time = item.get("time_published", "")
                formatted_time = f"{raw_time[9:11]}:{raw_time[11:13]}" if len(raw_time) > 11 else "--:--"
                news.append({"title": item.get("title", "No Title"), "source": item.get("source", "Unknown"), "time": formatted_time})
            return news
        except: return []

    def get_indices(self):
        indices = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "DOW J"}
        data = []
        for sym, name in indices.items():
            try:
                t = yf.Ticker(sym).fast_info
                cp = ((t.last_price - t.previous_close) / t.previous_close) * 100
                data.append({"name": name, "price": f"{t.last_price:,.2f}", "pct": f"{cp:+.2f}%", "raw_pct": cp})
            except: continue
        return data

    def get_history(self, symbol: str):
        try:
            h = yf.Ticker(symbol).history(period="6mo")
            return h['Close'].tolist() if not h.empty else []
        except: return []

    def _format_market_cap(self, val):
        if not val: return "N/A"
        if val >= 1e12: return f"{val/1e12:.2f}T"
        if val >= 1e9: return f"{val/1e9:.2f}B"
        return f"{val/1e6:.2f}M"
