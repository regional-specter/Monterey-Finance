from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static, Input, Footer
from textual.containers import Horizontal, Vertical
from terminal.backend.data.yfinance_ext import MarketDataProvider
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import asyncio

# COLORS
BURGUNDY = "#800000"; DARK_BLUE = "#000080"; AMBER = "#FF9F00"; LIME = "#00FF00"; RED = "#FF3333"; BG = "#000000"; BORDER = "#222222"

class TopBanner(Static):
    def update_ticker(self, symbol):
        t = Table.grid(expand=True)
        t.add_column(); t.add_column(justify="center"); t.add_column(justify="right")
        t.add_row(f"[bold white]{symbol} US Equity[/]", "TERMINAL OVERVIEW", "MONTEREY | [green]● LIVE[/]")
        self.update(t)

class NavBar(Static):
    def update_active(self, index=0):
        tabs = [(" HOME ",0), (" OVERVIEW ",1), (" ANALYSIS ",2), (" NEWS ",3)]
        c = Text()
        for lbl, i in tabs:
            style = f"black on {AMBER}" if i == index else "white on #000080"
            c.append(f" [{i}] {lbl} ", style)
        self.update(c)

class PriceChart(Static):
    def update_chart(self, p, s):
        if not p: return
        cols, rows = 70, 9; b_w, b_h = cols*2, rows*4
        min_p, max_p = min(p), max(p); rng = (max_p - min_p) or 1
        res = [int((p[int(i*(len(p)-1)/(b_w-1))] - min_p)/rng*(b_h-1)) for i in range(b_w)]
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for bx, by in enumerate(res):
            cx, dx = divmod(bx, 2); cy, dy = divmod(b_h-1-by, 4)
            if 0<=cx<cols and 0<=cy<rows: grid[cy][cx] |= [[1,8],[2,16],[4,32],[64,128]][dy][dx]
        c_str = "\n".join(["".join(chr(0x2800 + dots) for dots in r) for r in grid])
        style = LIME if p[-1]>=p[0] else RED
        self.update(Panel(f"[{style}]{c_str}[/]", title=f"[bold {AMBER}]Price Chart | GP[/]", border_style=AMBER, padding=0))

class MarketHeatmap(Static):
    def update_heatmap(self, sectors):
        g = Table.grid(expand=True, padding=(0,1))
        for i in range(0, len(sectors), 4):
            row = []
            for s in sectors[i:i+4]:
                c = LIME if s['pct']>1.5 else "#004400" if s['pct']>0 else RED if s['pct']<-1.5 else "#440000"
                row.append(Panel(f"[bold white]{s['name']}\n{s['pct']:+.1f}%[/]", style=f"on {c}", padding=0))
            g.add_row(*row)
        self.update(Panel(g, title=f"[bold {AMBER}]Sector Performance | Heatmap[/]", border_style=AMBER, padding=0))

class DenseModule(Static):
    def __init__(self, title, **kwargs): super().__init__(**kwargs); self.title = title
    def update_data(self, d):
        g = Table.grid(expand=True); g.add_column(style="dim white"); g.add_column(style="white", justify="right")
        if d:
            for k, v in d.items(): g.add_row(str(k), str(v))
        else:
            g.add_row("N/A", "No data")
        self.update(Panel(g, title=f"[bold {AMBER}]{self.title}[/]", border_style=AMBER, padding=0))

class NewsFeed(Static):
    def update_news(self, news):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column(width=4, style=AMBER); table.add_column(width=10, style="dim white"); table.add_column(width=6, style=DARK_BLUE); table.add_column(style="white")
        if not news: table.add_row("-", "ALPHA-V", "--:--", "No news or API limit reached.")
        else:
            for i, n in enumerate(news): table.add_row(str(i+1), n['source'][:10], n['time'], n['title'][:90])
        self.update(Panel(table, title=f"[bold {AMBER}]Alpha Vantage News Feed | NEWS[/]", border_style=AMBER, padding=0))

class OrderBook(Static):
    def update_book(self, data):
        g = Table.grid(expand=True)
        g.add_column(style=LIME); g.add_column(justify="right", style="dim white")
        g.add_column(width=2); g.add_column(style=RED); g.add_column(justify="right", style="dim white")
        if data:
            for b, a in zip(data.get('bids', []), data.get('asks', [])):
                g.add_row(f"{b['price']:.2f}", str(b['size']), "", f"{a['price']:.2f}", str(a['size']))
        self.update(Panel(g, title=f"[bold {AMBER}]Level 2 Depth | L2[/]", border_style=AMBER, padding=0))

class PerformanceMatrix(Static):
    def update_matrix(self, data):
        g = Table.grid(expand=True, padding=(0,1))
        if data:
            g.add_row(*[f"[dim white]{k}[/]" for k in data.keys()])
            g.add_row(*[f"[{LIME if v>0 else RED}]{v:+.1f}%[/]" for v in data.values()])
        self.update(Panel(g, title=f"[bold {AMBER}]Historical Returns[/]", border_style=AMBER, padding=0))

class TerminalApp(App):
    CSS = f"""
    Screen {{ background: {BG}; color: white; }}
    TopBanner {{ background: #800000; height: 1; padding: 0 1; }}
    NavBar {{ background: #000080; height: 1; }}
    #command-row {{ height: 1; background: #1a1a1a; }}
    .column {{ height: 1fr; border-right: solid {BORDER}; }}
    #left-col {{ width: 55%; }}
    #mid-col {{ width: 22%; }}
    #right-col {{ width: 23%; border: none; }}
    #summary-box {{ height: 4; border-bottom: solid {BORDER}; padding: 0 1; color: #ccc; }}
    PriceChart {{ height: 11; }}
    DataTable {{ height: 1fr; border: none; scrollbar-size: 0 0; }}
    DenseModule {{ height: auto; }}
    OrderBook {{ height: 7; }}
    PerformanceMatrix {{ height: 4; }}
    MarketHeatmap {{ height: 7; }}
    NewsFeed {{ height: 8; background: #050505; }}
    #footer-idx {{ height: 1; background: #111111; color: {AMBER}; }}
    """

    def compose(self) -> ComposeResult:
        yield TopBanner(id="header")
        yield NavBar(id="nav")
        yield Horizontal(Static(" <GO> ", id="go-label"), Input(id="command-input"), id="command-row")
        with Horizontal(id="main-grid"):
            with Vertical(id="left-col", classes="column"):
                yield Static(id="summary-box")
                yield PriceChart()
                yield DataTable()
            with Vertical(id="mid-col", classes="column"):
                yield DenseModule("Estimates | EE", id="estimates")
                yield DenseModule("Financials | FIN", id="ratios")
                yield PerformanceMatrix(id="perf")
                yield MarketHeatmap(id="heatmap")
            with Vertical(id="right-col", classes="column"):
                yield DenseModule("Corporate Info", id="corporate")
                yield DenseModule("Management", id="management")
                yield OrderBook(id="book")
        yield NewsFeed()
        yield Static(id="footer-idx")
        yield Footer()

    async def on_mount(self):
        self.query_one(NavBar).update_active(0)
        t = self.query_one(DataTable)
        t.add_columns("ASSET", "PRICING")
        t.cursor_type = "row"
        self.tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        await self.action_refresh()

    async def action_refresh(self):
        p = MarketDataProvider()
        watchlist = await asyncio.to_thread(p.get_watchlist_data, self.tickers)
        indices = await asyncio.to_thread(p.get_indices)
        sectors = await asyncio.to_thread(p.get_sector_data)
        
        self.query_one("#heatmap").update_heatmap(sectors)
        idx_str = "  |  ".join([f"{i['name']} {i['price']} [{LIME if i['raw_pct']>0 else RED}]{i['pct']}[/]" for i in indices])
        self.query_one("#footer-idx").update(idx_str)
        
        t = self.query_one(DataTable)
        t.clear()
        for r in watchlist:
            line1_left = Text.assemble((f"{r['Symbol']:<6}", "bold white"), (f" {r['Name'][:15]}", "dim white"))
            line2_left = Text.assemble((f" [black on #0000FF] {r.get('Sector','TECH')} [/] ", "bold"), (f" MKT CAP: {r['Mkt Cap']}", "dim white"))
            asset_card = Text.assemble(line1_left, "\n", line2_left)
            s = LIME if r['Pct']>0 else RED
            line1_right = Text.assemble((f"{r['Price']:>10.2f}", "bold white"), (f" {r['Change']:>+7.2f}", s))
            line2_right = Text.assemble((f"{r['Pct']:>+18.2f}%", s))
            pricing_card = Text.assemble(line1_right, "\n", line2_right)
            t.add_row(asset_card, pricing_card, key=r['Symbol'])
        if watchlist: await self.load_ticker(watchlist[0]['Symbol'])

    async def on_data_table_row_selected(self, e):
        await self.load_ticker(str(e.row_key.value))

    async def load_ticker(self, symbol):
        p = MarketDataProvider()
        d, h, perf, news = await asyncio.gather(
            asyncio.to_thread(p.get_full_analysis, symbol),
            asyncio.to_thread(p.get_history, symbol),
            asyncio.to_thread(p.get_performance_matrix, symbol),
            asyncio.to_thread(p.get_av_news, symbol)
        )
        if not d: return
        self.query_one(TopBanner).update_ticker(symbol)
        prof = d.get('Profile', {})
        self.query_one("#summary-box").update(f"[dim {AMBER}]Profile | »[/] {prof.get('Summary', '')[:280]}...")
        self.query_one(PriceChart).update_chart(h, symbol)
        self.query_one("#estimates").update_data(d.get('Estimates', {}))
        self.query_one("#ratios").update_data(d.get('Ratios', {}))
        self.query_one("#corporate").update_data({"HQ": prof.get('HQ', 'N/A'), "Staff": prof.get('Employees', 'N/A'), "Web": prof.get('Website', 'N/A')})
        mgmt = d.get('Management', [])
        self.query_one("#management").update_data({m.get('title', 'N/A'): m.get('name', 'N/A') for m in mgmt})
        self.query_one("#perf").update_matrix(perf)
        self.query_one("#book").update_book(p.get_order_book(d.get('Price', 0)))
        self.query_one(NewsFeed).update_news(news)

if __name__ == "__main__":
    TerminalApp().run()
