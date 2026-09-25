"""One weekday pass: optional refresh, intended book, breach preview, files."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from ops.breaches import breach_preview
from ops.data import load_lab, refresh_facts, resolve_as_of
from ops.persist import persist_session
from ops.targets import IntendedBook, build_intended_book
from ops.paths import ensure_research_on_path

ensure_research_on_path()

from sleeves.lab import Lab  # noqa: E402


@dataclass
class SessionResult:
    book: IntendedBook
    folder: Path
    breaches: pd.DataFrame
    coverage: pd.DataFrame | None = None
    refresh: pd.DataFrame | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def run_session(
    as_of: date | str | None = "today",
    *,
    lab: Lab | None = None,
    refresh: bool = False,
    coverage: bool = False,
    persist: bool = True,
    breaches: bool = True,
    lookback_days: int = 550,
    symbols: Sequence[str] | None = None,
    breach_lookback_days: int = 10,
    runs_root: Path | None = None,
) -> SessionResult:
    want = resolve_as_of(as_of)
    refresh_frame = None
    if refresh:
        refresh_frame = refresh_facts(want)

    session_lab = lab or load_lab(
        want,
        symbols=symbols,
        lookback_days=lookback_days,
        cache=True,
    )
    book = build_intended_book(session_lab, want)
    fails = (
        breach_preview(book, lookback_days=breach_lookback_days, cache=True)
        if breaches
        else pd.DataFrame()
    )

    coverage_frame = None
    if coverage:
        coverage_frame = _coverage_sheet(symbols or list(session_lab.metrics["symbol"].unique()), book.as_of)

    extra = {
        "n_filing_fails": 0 if fails.empty else int(len(fails)),
        "refreshed": refresh,
    }
    folder = Path()
    if persist:
        folder = persist_session(
            book,
            breaches=fails,
            coverage=coverage_frame,
            refresh=refresh_frame,
            extra=extra,
            root=runs_root,
        )
    return SessionResult(
        book=book,
        folder=folder,
        breaches=fails,
        coverage=coverage_frame,
        refresh=refresh_frame,
        extra=extra,
    )


def _coverage_sheet(symbols: Sequence[str], as_of: date) -> pd.DataFrame:
    import halalquant as hq

    detail = hq.coverage_report(tickers=list(symbols), as_of=as_of, cache=True)
    return hq.coverage_summary(detail)
