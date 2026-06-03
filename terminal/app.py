from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static, Input, Footer
from textual.containers import Horizontal, Vertical
from terminal.backend.data.yfinance_ext import MarketDataProvider
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import asyncio

# COLORS
BURGUNDY = "#800000"; DARK_BLUE = "#000080"; AMBER = "#FF9F00"; LIME = "#00FF00"; RED = "#FF3333"; BG = "#000000"

class TopBanner(Static):
    def update_ticker(self, symbol, name):
        table = Table.grid(expand=True)
        table.add_column(justify="left", style="white bold"); table.add_column(justify="center", style="white bold"); table.add_column(justify="right", style="white")
        table.add_row(f"{symbol} US Equity", "COMPANY OVERVIEW", "MONTEREY FINANCE | [green]● LIVE[/]")
        self.update(table)

class NavBar(Static):
    def update_active(self, index=0):
        tabs = [(" [0] HOME ",0), (" [1] OVERVIEW ",1), (" [2] ANALYSIS ",2), (" [3] ESTIMATES ",3), (" [4] NEWS ",4)]
        content = Text()
        for label, i in tabs:
            style = f"black on {AMBER}" if i == index else f"white on {DARK_BLUE}"
            content.append(label, style)
        self.update(content)

class PriceChart(Static):
    def update_chart(self, prices, symbol):
        if not prices: self.update(Panel(Text("No Data", justify="center"), title=f"[bold {AMBER}]8) Price Chart | GP »[/]", border_style=AMBER)); return
        cols, rows = 60, 10; b_w, b_h = cols * 2, rows * 4
        min_p, max_p = min(prices), max(prices); rng = (max_p - min_p) or 1
        res = [int((prices[int(i*(len(prices)-1)/(b_w-1))] - min_p)/rng*(b_h-1)) for i in range(b_w)]
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for bx, by in enumerate(res):
            cx, dx = divmod(bx, 2); cy, dy = divmod(b_h-1-by, 4)
            if 0<=cx<cols and 0<=cy<rows: grid[cy][cx] |= [[0x01,0x08],[0x02,0x10],[0x04,0x20],[0x40,0x80]][dy][dx]
        chart_str = "\n".join(["".join(chr(0x2800 + dots) for dots in r) for r in grid])
        style = LIME if prices[-1] >= prices[0] else RED
        y_axis = f"{max_p:>8.2f} ┐\n" + "\n".join(["         │" for _ in range(rows-2)]) + f"\n{min_p:>8.2f} ┘"
        layout = Table.grid(padding=(0,1)); layout.add_row(y_axis, f"[{style}]{chart_str}[/]")
        self.update(Panel(layout, title=f"[bold {AMBER}]8) Price Chart | GP »[/]", border_style=AMBER, padding=0))

class MarketHeatmap(Static):
    def update_heatmap(self, sectors):
        grid = Table.grid(expand=True, padding=0)
        grid.add_column(); grid.add_column()
        for i in range(0, len(sectors), 2):
            row_cells = []
            for s in sectors[i:i+2]:
                color = LIME if s['pct'] > 2 else "#444444" if s['pct'] > 0 else RED if s['pct'] < -2 else "#440000"
                row_cells.append(Panel(f"[bold white]{s['name']}\n{s['pct']:+.1f}%[/]", style=f"on {color}", padding=0))
            grid.add_row(*row_cells)
        self.update(Panel(grid, title=f"[bold {AMBER}]Market Heatmap | WEI[/]", border_style=AMBER, padding=0))

class DenseModule(Static):
    def __init__(self, title, **kwargs): super().__init__(**kwargs); self.title = title
    def update_data(self, data_dict):
        grid = Table.grid(expand=True); grid.add_column(style=f"dim {AMBER}"); grid.add_column(style="white", justify="right")
        for k, v in data_dict.items(): grid.add_row(str(k), str(v))
        self.update(Panel(grid, title=f"[bold {AMBER}]{self.title}[/]", border_style=AMBER, padding=0))

class NewsFeed(Static):
    def update_news(self, news):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column(width=4, style=AMBER); table.add_column(width=10, style="dim white"); table.add_column(width=6, style=DARK_BLUE); table.add_column(style="white")
        if not news: table.add_row("-", "ALPHA-V", "--:--", "No news or API limit reached.")
        else:
            for i, n in enumerate(news): table.add_row(str(i+1), n['source'][:10], n['time'], n['title'][:70])
        self.update(Panel(table, title=f"[bold {AMBER}]Alpha Vantage News Feed[/]", border_style=AMBER, padding=0))

class TickerFooter(Static):
    def update_indices(self, indices):
        parts = [f"{idx['name']} {idx['price']} [{'green' if idx['raw_pct']>0 else 'red'}]{idx['pct']}[/]" for idx in indices]
        self.update("  |  ".join(parts))

class TerminalApp(App):
    CSS = f"""
    Screen {{ background: {BG}; color: white; }}
    TopBanner {{ background: #800000; height: 1; padding: 0 1; }}
    NavBar {{ background: #000080; height: 1; }}
    #command-row {{ height: 1; background: #1a1a1a; }}
    #command-input {{ background: transparent; border: none; height: 1; color: white; padding: 0 1; }}
    .column {{ height: 1fr; border-right: solid #333333; }}
    #left-col {{ width: 55%; }}
    #mid-col {{ width: 22%; }}
    #right-col {{ width: 23%; border: none; }}
    #summary-box {{ height: 4; border-bottom: solid #333333; padding: 0 1; color: #cccccc; }}
    PriceChart {{ height: 12; }}
    #liquidity-bar {{ height: 1; background: #080808; padding: 0 1; color: {AMBER}; }}
    DataTable {{ height: 1fr; border: none; background: {BG}; scrollbar-size: 0 0; }}
    MarketHeatmap {{ width: 20; height: 1fr; border-left: solid #333333; }}
    DenseModule {{ height: auto; }}
    NewsFeed {{ height: 9; background: #050505; }}
    TickerFooter {{ height: 1; background: #111111; color: {AMBER}; }}
    """

    def compose(self) -> ComposeResult:
        yield TopBanner(id="header")
        yield NavBar(id="nav")
        yield Horizontal(Static(" <GO> ", id="go-label"), Input(id="command-input"), id="command-row")
        with Horizontal(id="main-grid"):
            with Vertical(id="left-col", classes="column"):
                yield Static(id="summary-box")
                yield PriceChart()
                with Horizontal():
                    yield DataTable()
                    yield MarketHeatmap()
                yield Static(id="liquidity-bar")
            with Vertical(id="mid-col", classes="column"):
                yield DenseModule("Estimates | EE", id="estimates")
                yield DenseModule("Financial Ratios", id="ratios")
                yield DenseModule("Income Snapshot", id="income")
                yield DenseModule("Dividend | DVD", id="dividends")
            with Vertical(id="right-col", classes="column"):
                yield DenseModule("Corporate Info", id="corporate")
                yield DenseModule("Technical Signals", id="technicals")
                yield DenseModule("Management | MGMT", id="management")
        yield NewsFeed()
        yield TickerFooter()
        yield Footer()

    async def on_mount(self):
        self.query_one(NavBar).update_active(0)
        table = self.query_one(DataTable)
        table.add_columns("SYM", "PX", "CHG", "CHG%", "MKT CAP")
        table.cursor_type = "row"
        self.tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        await self.action_refresh()

    async def action_refresh(self):
        provider = MarketDataProvider()
        ticker_data = await asyncio.to_thread(provider.get_ticker_data, self.tickers)
        sectors = await asyncio.to_thread(provider.get_sector_data)
        indices = await asyncio.to_thread(provider.get_indices)
        
        self.query_one(MarketHeatmap).update_heatmap(sectors)
        self.query_one(TickerFooter).update_indices(indices)
        
        table = self.query_one(DataTable)
        table.clear()
        for row in ticker_data:
            style = LIME if row["Raw Change %"] > 0 else RED
            table.add_row(row["Symbol"], row["Price"], f"[{style}]{row['Change']}[/]", f"[{style}]{row['Change %']}[/]", row["Mkt Cap"], key=row["Symbol"])
        
        if ticker_data: await self.load_ticker(ticker_data[0]['Symbol'])

    async def on_data_table_row_selected(self, event: DataTable.RowSelected):
        await self.load_ticker(str(event.row_key.value))

    async def load_ticker(self, symbol):
        provider = MarketDataProvider()
        data, hist, news = await asyncio.gather(
            asyncio.to_thread(provider.get_full_analysis, symbol),
            asyncio.to_thread(provider.get_history, symbol),
            asyncio.to_thread(provider.get_av_news, symbol)
        )
        if not data: return
        
        tech = provider.calculate_technicals(hist)
        prof = data['Profile']
        self.query_one(TopBanner).update_ticker(symbol, prof['Name'])
        self.query_one("#summary-box").update(f"[dim {AMBER}]Profile | »[/] {prof['Summary'][:250]}...")
        self.query_one(PriceChart).update_chart(hist, symbol)
        
        # Mid Column
        self.query_one("#estimates").update_data(data['Estimates'])
        self.query_one("#ratios").update_data(data['Ratios'])
        self.query_one("#income").update_data(data['Income'])
        self.query_one("#dividends").update_data(data['Dividends'])
        
        # Right Column
        self.query_one("#corporate").update_data({"HQ": prof['HQ'], "Staff": prof['Employees'], "Web": prof['Website']})
        self.query_one("#technicals").update_data({
            "RSI(14)": tech['RSI'],
            "Signal": tech['MA_Signal'],
            "MA50": tech['MA50'],
            "MA200": tech['MA200']
        })
        self.query_one("#management").update_data({m['title']: m['name'] for m in data['Management']})
        
        # Left Liquidity Bar
        liq = data['Liquidity']
        self.query_one("#liquidity-bar").update(f"VOL: {liq['Vol']} | AVG: {liq['Avg Vol']} | RATIO: {liq['Vol/Avg']}")
        
        self.query_one(NewsFeed).update_news(news)

if __name__ == "__main__":
    TerminalApp().run()
