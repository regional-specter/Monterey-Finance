"""New 10-Q / 10-K AAOIFI flags on names we hold (or would hold)."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from ops.targets import IntendedBook


def filing_window(as_of: date, lookback_days: int = 10) -> tuple[date, date]:
    return as_of - timedelta(days=int(lookback_days)), as_of


def holdings_tickers(book: IntendedBook) -> list[str]:
    names: set[str] = set()
    for frame in (book.holdings, book.invested):
        if frame is None or frame.empty or "symbol" not in frame.columns:
            continue
        names.update(str(s) for s in frame["symbol"].dropna().unique())
    return sorted(names)


def breach_preview(
    book: IntendedBook,
    *,
    lookback_days: int = 10,
    cache: bool = True,
) -> pd.DataFrame:
    """Fails only. Empty frame if none. Does not sell."""
    tickers = holdings_tickers(book)
    if not tickers:
        return pd.DataFrame()
    import halalquant as hq

    since, as_of = filing_window(book.as_of, lookback_days)
    events = hq.filing_events(
        as_of=as_of,
        since=since,
        tickers=tickers,
        cache=cache,
    )
    if events is None or events.empty:
        return pd.DataFrame()
    if "is_compliant" not in events.columns:
        return events
    fails = events.loc[~events["is_compliant"].fillna(True).astype(bool)].copy()
    return fails.reset_index(drop=True)
