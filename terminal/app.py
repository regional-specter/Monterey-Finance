import os
import json
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Header, Footer, Static, Label
from textual.widget import Widget

class BusinessCard(Widget):
    """A horizontal card displaying a single SME listing's metadata and financials."""
    
    def __init__(self, data: dict):
        super().__init__()
        self.data = data

    def format_val(self, val, raw, currency="USD"):
        """Formats numbers into clean financial notation ($150K, £1.2M, etc.)."""
        if val is None:
            return raw or "On Request"
            
        symbols = {"USD": "$", "AUD": "$", "GBP": "£", "EUR": "€", "CAD": "$"}
        sym = symbols.get(currency, "$")
        
        def to_human(n):
            if n >= 1000000:
                return f"{sym}{n/1000000:.1f}M"
            elif n >= 1000:
                return f"{sym}{n/1000:.0f}K"
            return f"{sym}{n:.0f}"
            
        if isinstance(val, dict):
            min_v = val.get("min")
            max_v = val.get("max")
            if min_v is not None and max_v is not None:
                if min_v == 0:
                    return f"Under {to_human(max_v)}"
                return f"{to_human(min_v)} - {to_human(max_v)}"
            elif min_v is not None:
                return f"Over {to_human(min_v)}"
            elif max_v is not None:
                return f"Under {to_human(max_v)}"
        return to_human(val)

    def compose(self) -> ComposeResult:
        # 1. Info block
        city = self.data["location"]["city"] or "Unknown City"
        country = self.data["location"]["country"] or "Global"
        loc_str = f"{city}, {country}"
        
        info_markup = (
            f"[bold cyan]{self.data['name']}[/]\n"
            f"[dim]{loc_str}[/]\n"
            f"[dim blue]{self.data['url'][:50]}...[/]"
        )
        
        # 2. Financials block
        fin = self.data["financials"]
        currency = self.data["currency"]
        
        ask_f = self.format_val(fin["asking_price"], fin["asking_price_raw"], currency)
        rev_f = self.format_val(fin["revenue"], fin["revenue_raw"], currency)
        cf_f = self.format_val(fin["cash_flow"], fin["cash_flow_raw"], currency)
        
        mult = fin.get("multiple")
        mult_str = f"[bold green]{mult}x[/]" if mult else "[dim]N/A[/]"
        
        fin_markup = (
            f"[bold]Ask Price:[/] {ask_f}\n"
            f"[bold]Revenue:  [/] {rev_f}\n"
            f"[bold]Cash Flow:[/] {cf_f} [dim](SDE)[/]  |  [bold]Mult:[/] {mult_str}"
        )
        
        # 3. Description & Tags
        desc = self.data["description"]
        if len(desc) > 130:
            desc = desc[:127] + "..."
            
        tags = []
        if mult and mult < 3.5:
            tags.append("[black on green] GEM [/]")
        if not fin["cash_flow"]:
            tags.append("[black on yellow] NO-CF [/]")
            
        tag_line = "  ".join(tags)
        desc_markup = f"[dim]{desc}[/]\n{tag_line}"
        
        yield Static(info_markup, classes="card-column card-info")
        yield Static(fin_markup, classes="card-column card-financials")
        yield Static(desc_markup, classes="card-column card-desc")


class MontereyTerminal(App):
    """The main Monterey SME M&A Bloomberg-style Terminal application."""
    
    TITLE = "MONTEREY M&A TERMINAL"
    SUB_TITLE = "SME Acquisition Pipeline Analyzer"
    CSS_PATH = "styles.tcss"
    
    def on_mount(self) -> None:
        self.render_stats()

    def load_data(self) -> None:
        """Loads and processes listing data from listings_output.json."""
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "listings_output.json"
        )
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                self.listings = json.load(f)
        else:
            self.listings = []

    def render_stats(self) -> None:
        """Renders summary analytics to the top header panel."""
        total = len(self.listings)
        
        # Calculate average multiples
        multiples = [
            item["financials"]["multiple"]
            for item in self.listings
            if item["financials"].get("multiple") is not None
        ]
        avg_mult = round(sum(multiples) / len(multiples), 2) if multiples else 0.0
        
        # Calculate listings with Cash Flow
        with_cf = sum(1 for item in self.listings if item["financials"].get("cash_flow") is not None)
        
        stats_markup = (
            f"[bold]Active Pipeline Listings:[/] [cyan]{total}[/]    |    "
            f"[bold]Avg SDE Multiple:[/] [green]{avg_mult}x[/]    |    "
            f"[bold]Fully Analyzed (with CF):[/] [yellow]{with_cf}/{total}[/]"
        )
        self.query_one("#header-stats", Static).update(stats_markup)

    def compose(self) -> ComposeResult:
        self.load_data()
        yield Header(show_clock=True)
        
        # Top analytics stats dashboard
        yield Static("", id="header-stats")
        
        # Main Listings View
        with VerticalScroll(id="listings-container"):
            for listing in self.listings:
                yield BusinessCard(listing)
                
        yield Footer()


if __name__ == "__main__":
    app = MontereyTerminal()
    app.run()
