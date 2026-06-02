import yfinance as yf
import pandas as pd

class MarketDataProvider:
    def __init__(self):
        pass

    def get_ticker_data(self, tickers: list):
        """
        Fetches comprehensive data for the provided tickers.
        """
        data = []
        for ticker_symbol in tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                price = info.get('regularMarketPrice') or info.get('currentPrice')
                prev_close = info.get('previousClose')
                
                change = 0
                change_pct = 0
                if price and prev_close:
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100

                data.append({
                    "Symbol": ticker_symbol,
                    "Name": info.get('shortName', 'N/A'),
                    "Price": f"{price:.2f}" if price else "N/A",
                    "Change": f"{change:+.2f}",
                    "Change %": f"{change_pct:+.2f}%",
                    "Market Cap": self._format_market_cap(info.get('marketCap')),
                    "P/E": f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A",
                    "Div Yield": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "N/A",
                    "52W Range": f"{info.get('fiftyTwoWeekLow', 0):.2f} - {info.get('fiftyTwoWeekHigh', 0):.2f}",
                    "Sector": info.get('sector', 'N/A'),
                    "Raw Change %": change_pct
                })
            except Exception as e:
                data.append({
                    "Symbol": ticker_symbol,
                    "Name": "N/A",
                    "Price": "N/A",
                    "Change": "N/A",
                    "Change %": "N/A",
                    "Market Cap": "N/A",
                    "P/E": "N/A",
                    "Div Yield": "N/A",
                    "52W Range": "N/A",
                    "Sector": "N/A",
                    "Raw Change %": 0
                })
        return data

    def get_indices(self):
        """Fetches major market indices."""
        indices = {
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ",
            "^DJI": "DOW J",
            "BTC-USD": "BTC"
        }
        data = []
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                price = info.last_price
                prev_close = info.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100
                data.append({
                    "name": name,
                    "price": f"{price:,.2f}",
                    "pct": f"{change_pct:+.2f}%",
                    "raw_pct": change_pct
                })
            except:
                continue
        return data

    def get_analysis_data(self, ticker_symbol: str):
        """
        Fetches analysis data for a specific ticker.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # Analyst Recommendations
            recs = ticker.recommendations
            rec_summary = "N/A"
            if recs is not None and not recs.empty:
                # Get the most recent period's recommendations
                latest = recs.iloc[-1]
                rec_summary = f"Strong Buy: {latest.get('strongBuy', 0)} | Buy: {latest.get('buy', 0)} | Hold: {latest.get('hold', 0)} | Sell: {latest.get('sell', 0)}"

            # Historical Performance (Quick trend)
            hist = ticker.history(period="1mo")
            trend = "Flat"
            if not hist.empty:
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                perf = ((end_price - start_price) / start_price) * 100
                trend = f"{perf:+.2f}% (1M)"

            # Technicals (Simple Moving Averages)
            hist_long = ticker.history(period="1y")
            ma50 = hist_long['Close'].rolling(window=50).mean().iloc[-1]
            ma200 = hist_long['Close'].rolling(window=200).mean().iloc[-1]

            return {
                "Recommendations": rec_summary,
                "Trend": trend,
                "MA50": f"{ma50:.2f}" if not pd.isna(ma50) else "N/A",
                "MA200": f"{ma200:.2f}" if not pd.isna(ma200) else "N/A",
                "Signal": "BULLISH" if ma50 > ma200 else "BEARISH" if ma50 < ma200 else "NEUTRAL"
            }
        except Exception as e:
            return {
                "Recommendations": "Error fetching",
                "Trend": "N/A",
                "MA50": "N/A",
                "MA200": "N/A",
                "Signal": "N/A"
            }

    def get_history(self, ticker_symbol: str, period="6mo"):
        """Fetches historical close prices for charting."""
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period=period)
            if hist.empty:
                return []
            return hist['Close'].tolist()
        except:
            return []

    def get_detailed_analysis(self, ticker_symbol: str):
        """
        Fetches even more detailed data for a specific ticker.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Financial Highlights
            financials = {
                "Revenue": self._format_market_cap(info.get('totalRevenue')),
                "Profit Margin": f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/A",
                "EBITDA": self._format_market_cap(info.get('ebitda')),
                "Cash": self._format_market_cap(info.get('totalCash')),
            }

            # Dividend Info
            div_info = {
                "Last Div": f"{info.get('lastDividendValue', 0):.2f}" if info.get('lastDividendValue') else "0.00",
                "Ex-Date": info.get('exDividendDate', 'N/A'),
            }

            # Price Visual Data (Current position in 52W range)
            low = info.get('fiftyTwoWeekLow', 0)
            high = info.get('fiftyTwoWeekHigh', 0)
            current = info.get('regularMarketPrice') or info.get('currentPrice', 0)
            
            range_pct = 0
            if high > low:
                range_pct = (current - low) / (high - low)

            return {
                "Summary": info.get('longBusinessSummary', 'No summary available.'),
                "Financials": financials,
                "Dividends": div_info,
                "PricePos": range_pct
            }
        except Exception as e:
            return {
                "Summary": "Error fetching data.",
                "Financials": {},
                "Dividends": {},
                "PricePos": 0
            }

    def _format_market_cap(self, market_cap):
        if not market_cap:
            return "N/A"
        if market_cap >= 1e12:
            return f"{market_cap / 1e12:.2f}T"
        if market_cap >= 1e9:
            return f"{market_cap / 1e9:.2f}B"
        if market_cap >= 1e6:
            return f"{market_cap / 1e6:.2f}M"
        return str(market_cap)

if __name__ == "__main__":
    # Quick test
    provider = MarketDataProvider()
    test_data = provider.get_ticker_data(["AAPL", "MSFT", "GOOGL"])
    print(test_data)
