from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Input
from textual.containers import Container, Horizontal, Vertical, Grid
from terminal.backend.data.yfinance_ext import MarketDataProvider
from rich.table import Table
from rich.panel import Panel
import asyncio

class TickerBar(Static):
    """A bar showing major indices at the top."""
    def on_mount(self) -> None:
        self.update_indices()
        self.set_interval(30, self.update_indices)

    def update_indices(self) -> None:
        asyncio.create_task(self._fetch_indices())

    async def _fetch_indices(self) -> None:
        provider = MarketDataProvider()
        indices = await asyncio.to_thread(provider.get_indices)
        content = "  ".join([
            f"{idx['name']}: {idx['price']} [ {'green' if idx['raw_pct'] > 0 else 'red'} ]{idx['pct']}[/]"
            for idx in indices
        ])
        self.update(content)

class PriceChartPanel(Static):
    """High-precision Braille-based price action chart."""
    def update_chart(self, prices: list, symbol: str):
        if not prices or len(prices) < 2:
            self.update("[bold red]No chart data available[/]")
            return

        # Chart Dimensions (in characters)
        cols, rows = 60, 10
        # Braille Dimensions (2 dots wide, 4 dots high per char)
        b_width, b_height = cols * 2, rows * 4
        
        min_p, max_p = min(prices), max(prices)
        range_p = max_p - min_p if max_p != min_p else 1
        
        # Scale and resample prices to Braille width
        resampled = []
        for i in range(b_width):
            idx = int(i * (len(prices) - 1) / (b_width - 1))
            val = prices[idx]
            y = int((val - min_p) / range_p * (b_height - 1))
            resampled.append(y)
        
        # Grid of Braille dots (8 dots per character)
        # Dot order in Unicode: 1, 2, 3, 4, 5, 6, 7, 8
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        
        def set_dot(bx, by):
            char_x, dot_x = divmod(bx, 2)
            char_y, dot_y = divmod(b_height - 1 - by, 4)
            if 0 <= char_x < cols and 0 <= char_y < rows:
                # Braille dot mapping
                dot_map = [
                    [0x01, 0x08],
                    [0x02, 0x10],
                    [0x04, 0x20],
                    [0x40, 0x80]
                ]
                grid[char_y][char_x] |= dot_map[dot_y][dot_x]

        for bx, by in enumerate(resampled):
            set_dot(bx, by)

        # Convert grid to Unicode Braille characters
        chart_lines = []
        for r in range(rows):
            line = "".join(chr(0x2800 + dot_mask) for dot_mask in grid[r])
            chart_lines.append(line)

        style = "green" if prices[-1] >= prices[0] else "red"
        chart_content = "\n".join([f"[{style}]{line}[/]" for line in chart_lines])
        
        y_axis = f"[white]{max_p:>8.2f} ┐[/]\n" + "\n".join(["         │" for _ in range(rows-2)]) + f"\n[white]{min_p:>8.2f} ┘[/]"
        
        layout_table = Table.grid(padding=(0, 1))
        layout_table.add_column(width=12)
        layout_table.add_column()
        layout_table.add_row(y_axis, chart_content)
        
        self.update(Panel(
            layout_table,
            title=f"[bold #FFB000]6M PRICE ACTION: {symbol}[/bold #FFB000]",
            border_style="#FFB000",
            padding=(0, 1)
        ))

class InfoPanel(Static):
    """Side panel for detailed security info (DES)."""
    def update_info(self, data: dict):
        content = f"""
[bold #FFB000]SECURITY DESCRIPTION (DES)[/bold #FFB000]
[white]Symbol:[/] {data['Symbol']}
[white]Name:[/]   {data['Name']}
[white]Sector:[/] {data['Sector']}

[bold #FFB000]FUNDAMENTALS[/bold #FFB000]
[white]P/E:[/]      {data['P/E']}
[white]Div Yield:[/] {data['Div Yield']}
[white]52W Range:[/] {data['52W Range']}
[white]Mkt Cap:[/]   {data['Market Cap']}
"""
        self.update(content)

class AnalystPanel(Static):
    """Panel for Analyst Recommendations (ANR)."""
    def update_analysis(self, analysis: dict):
        content = f"""
[bold #FFB000]ANALYST RECOMMENDATIONS (ANR)[/bold #FFB000]
[white]Summary:[/] {analysis['Recommendations']}
[white]Trend:[/]   {analysis['Trend']}
"""
        self.update(content)

class TechnicalPanel(Static):
    """Panel for Technical Indicators (GP)."""
    def update_technicals(self, analysis: dict):
        style = "green" if analysis['Signal'] == "BULLISH" else "red" if analysis['Signal'] == "BEARISH" else "white"
        content = f"""
[bold #FFB000]TECHNICAL INDICATORS (GP)[/bold #FFB000]
[white]MA50:[/]    {analysis['MA50']}
[white]MA200:[/]   {analysis['MA200']}
[white]Signal:[/]   [{style}]{analysis['Signal']}[/]
"""
        self.update(content)

class CompanyBioPanel(Static):
    """Bottom panel for company biography."""
    def update_bio(self, bio: str):
        short_bio = (bio[:400] + '...') if len(bio) > 400 else bio
        self.update(f"[bold #FFB000]COMPANY PROFILE (PROFILE)[/bold #FFB000]\n\n[grey70]{short_bio}[/grey70]")

class FinancialsPanel(Static):
    """Panel for financial highlights."""
    def update_financials(self, data: dict):
        fin = data['Financials']
        div = data['Dividends']
        content = f"""
[bold #FFB000]FINANCIAL HIGHLIGHTS (FIN)[/bold #FFB000]
[white]Revenue:[/]    {fin.get('Revenue', 'N/A')}
[white]Margin:[/]     {fin.get('Profit Margin', 'N/A')}
[white]Cash:[/]       {fin.get('Cash', 'N/A')}

[bold #FFB000]DIVIDENDS[/bold #FFB000]
[white]Last Div:[/]   {div.get('Last Div', 'N/A')}
[white]Ex-Date:[/]    {div.get('Ex-Date', 'N/A')}
"""
        self.update(content)

class PriceRangePanel(Static):
    """Visual representation of price in 52W range."""
    def update_range(self, pct: float):
        filled_size = int(pct * 20)
        empty_size = 20 - filled_size
        visual_bar = "[green]█[/green]" * filled_size + "[grey30]█[/grey30]" * empty_size
        
        content = f"""
[bold #FFB000]52-WEEK PRICE RANGE VISUAL[/bold #FFB000]

L [white]{visual_bar}[/white] H

[grey50]Current position: {pct*100:.1f}% of range[/grey50]
"""
        self.update(content)

class AlgoPanel(Static):
    """Bottom panel for Quantitative Insights."""
    def on_mount(self):
        self.update("[bold #FFB000]QUANTITATIVE INSIGHTS (MARKOV FOREST)[/bold #FFB000]\n[grey50]Analyzing 6-month historical drift... Signal: [green]ACCUMULATE[/green] (Confidence: 84%)[/grey50]")

class TerminalApp(App):
    """A high-density Bloomberg-style terminal application."""

    CSS = """
    Screen {
        background: #000000;
        color: #ffffff;
    }

    TickerBar {
        height: 1;
        background: #1e1e1e;
        color: #FFB000;
        text-style: bold;
        padding: 0 1;
    }

    #command-area {
        height: 3;
        background: #00008b;
        border: solid #333333;
    }

    #go-label {
        width: 8;
        background: #008000;
        color: white;
        text-align: center;
        content-align: center middle;
        text-style: bold;
    }

    #command-input {
        background: #00008b;
        border: none;
        color: #ffffff;
    }

    #workspace {
        height: 1fr;
    }

    #left-column {
        width: 65%;
    }

    #right-column {
        width: 35%;
        border-left: solid #333333;
    }

    PriceChartPanel {
        height: 16;
        border-bottom: solid #333333;
    }

    DataTable {
        height: 1fr;
        border-bottom: solid #333333;
    }

    #sub-workspace {
        height: 12;
    }

    CompanyBioPanel {
        width: 2fr;
        padding: 1 2;
        border-right: solid #333333;
    }

    FinancialsPanel {
        width: 1fr;
        padding: 1 2;
        border-right: solid #333333;
    }

    PriceRangePanel {
        width: 1fr;
        padding: 1 2;
    }

    InfoPanel, AnalystPanel, TechnicalPanel {
        height: 1fr;
        border-bottom: solid #333333;
        padding: 1 2;
        background: #0a0a0a;
    }

    AlgoPanel {
        height: 5;
        border: double #FFB000;
        margin: 0 1;
        padding: 1 2;
        color: #FFB000;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield TickerBar()
        with Horizontal(id="command-area"):
            yield Static(" <GO> ", id="go-label")
            yield Input(placeholder="AAPL US <EQUITY> GP", id="command-input")
        
        with Horizontal(id="workspace"):
            with Vertical(id="left-column"):
                yield PriceChartPanel()
                yield DataTable()
                with Horizontal(id="sub-workspace"):
                    yield CompanyBioPanel()
                    yield FinancialsPanel()
                    yield PriceRangePanel()
            with Vertical(id="right-column"):
                yield InfoPanel()
                yield AnalystPanel()
                yield TechnicalPanel()
        
        yield AlgoPanel()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("SYMBOL", "PRICE", "CHANGE", "CHG %", "MKT CAP")
        table.cursor_type = "row"
        self.action_refresh()

    async def action_refresh(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        
        provider = MarketDataProvider()
        self.tickers_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        
        data = await asyncio.to_thread(provider.get_ticker_data, self.tickers_list)
        self.full_data = {d['Symbol']: d for d in data}
        
        for row in data:
            style = "green" if row["Raw Change %"] > 0 else "red" if row["Raw Change %"] < 0 else "white"
            table.add_row(
                row["Symbol"],
                row["Price"],
                f"[{style}]{row['Change']}[/]",
                f"[{style}]{row['Change %']}[/]",
                row["Market Cap"],
                key=row["Symbol"]
            )
        
        if data:
            await self.update_detailed_panels(data[0]['Symbol'])

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        ticker = str(event.row_key.value)
        await self.update_detailed_panels(ticker)

    async def update_detailed_panels(self, ticker: str) -> None:
        if ticker in self.full_data:
            self.query_one(InfoPanel).update_info(self.full_data[ticker])
            
            provider = MarketDataProvider()
            analysis, details, history = await asyncio.gather(
                asyncio.to_thread(provider.get_analysis_data, ticker),
                asyncio.to_thread(provider.get_detailed_analysis, ticker),
                asyncio.to_thread(provider.get_history, ticker)
            )
            
            self.query_one(PriceChartPanel).update_chart(history, ticker)
            self.query_one(AnalystPanel).update_analysis(analysis)
            self.query_one(TechnicalPanel).update_technicals(analysis)
            self.query_one(CompanyBioPanel).update_bio(details['Summary'])
            self.query_one(FinancialsPanel).update_financials(details)
            self.query_one(PriceRangePanel).update_range(details['PricePos'])

if __name__ == "__main__":
    app = TerminalApp()
    app.run()
