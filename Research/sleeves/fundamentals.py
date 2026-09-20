"""Point-in-time joins for FCF, ROIC, and SUE signals."""

from __future__ import annotations

import numpy as np
import pandas as pd


def attach_latest_value(
    metrics: pd.DataFrame,
    history: pd.DataFrame,
    value_cols: list[str],
    on_date: str = "filed_date",
) -> pd.DataFrame:
    """As-of join: latest filing known on each metrics snapshot (no look-ahead)."""
    if metrics.empty:
        return metrics.copy()
    if history is None or history.empty:
        out = metrics.copy()
        for col in value_cols:
            if col not in out.columns:
                out[col] = np.nan
        return out

    hist = history.copy()
    hist[on_date] = pd.to_datetime(hist[on_date])
    keep = ["symbol", on_date] + [c for c in value_cols if c in hist.columns]
    hist = hist[keep].dropna(subset=["symbol", on_date]).sort_values(["symbol", on_date])

    pieces: list[pd.DataFrame] = []
    for as_of, snap in metrics.groupby("as_of", sort=True):
        as_of_ts = pd.Timestamp(as_of)
        known = hist[hist[on_date] <= as_of_ts]
        if known.empty:
            extra = snap.copy()
            for col in value_cols:
                if col not in extra.columns:
                    extra[col] = np.nan
            pieces.append(extra)
            continue
        latest = known.sort_values(on_date).groupby("symbol", as_index=False).tail(1)
        drop_cols = [c for c in value_cols if c in snap.columns]
        left = snap.drop(columns=drop_cols, errors="ignore")
        pieces.append(left.merge(latest.drop(columns=[on_date]), on="symbol", how="left"))
    return pd.concat(pieces, ignore_index=True)


def attach_latest_fcf(metrics: pd.DataFrame, fcf_history: pd.DataFrame) -> pd.DataFrame:
    return attach_latest_value(metrics, fcf_history, ["fcf"])


def attach_latest_roic(metrics: pd.DataFrame, roic_history: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "roic",
        "reinvestment_rate",
        "nopat",
        "invested_capital",
        "capex_to_sales",
        "rd",
    ]
    return attach_latest_value(metrics, roic_history, cols)


def score_cash_generation(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    fcf = pd.to_numeric(out["fcf"], errors="coerce")
    revenue = pd.to_numeric(out.get("total_revenue"), errors="coerce")
    cap = pd.to_numeric(out.get("market_cap"), errors="coerce")
    debt = pd.to_numeric(out.get("total_debt"), errors="coerce").fillna(0)
    cash = pd.to_numeric(out.get("cash_and_equiv"), errors="coerce").fillna(0)
    out["fcf_margin"] = fcf / revenue.replace(0, np.nan)
    out["market_cap"] = cap
    ev = cap + debt - cash
    out["fcf_yield"] = fcf / ev.replace(0, np.nan)
    return out


def score_compounding(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    for col in ("roic", "reinvestment_rate", "nopat", "invested_capital", "market_cap"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def robust_sigma(hist: pd.Series) -> float:
    h = hist.dropna().astype(float)
    if len(h) < 3:
        return np.nan
    lo, hi = h.quantile(0.05), h.quantile(0.95)
    clipped = h.clip(lo, hi)
    sigma = float(clipped.std(ddof=1))
    floor = 0.5 * float(h.abs().median())
    sigma = max(sigma, floor, 1e-8)
    return sigma if np.isfinite(sigma) else np.nan


def attach_sue(earnings: pd.DataFrame, min_prior: int = 6) -> pd.DataFrame:
    """Point-in-time SUE on % surprise when available, else EPS forecast error."""
    if earnings.empty:
        out = earnings.copy()
        out["sue"] = pd.Series(dtype=float)
        out["sigma_ue"] = pd.Series(dtype=float)
        out["n_prior"] = pd.Series(dtype=int)
        out["sue_source"] = pd.Series(dtype=str)
        return out

    pieces: list[pd.DataFrame] = []
    for _, grp in earnings.groupby("symbol", sort=False):
        g = grp.sort_values("announce_date").copy()
        pct = (
            g["surprise_pct"].astype(float)
            if "surprise_pct" in g.columns
            else pd.Series(np.nan, index=g.index)
        )
        ue = g["ue"].astype(float)
        sigmas, sues, priors, srcs = [], [], [], []
        for i in range(len(g)):
            hist_pct = pct.iloc[:i].dropna()
            hist_ue = ue.iloc[:i].dropna()
            if len(hist_pct) >= min_prior and pd.notna(pct.iloc[i]):
                sigma = robust_sigma(hist_pct)
                n_prior = int(len(hist_pct))
                src = "surprise_pct"
                err = float(pct.iloc[i])
            elif len(hist_ue) >= min_prior:
                sigma = robust_sigma(hist_ue)
                n_prior = int(len(hist_ue))
                src = "ue"
                err = float(ue.iloc[i])
            else:
                sigmas.append(np.nan)
                sues.append(np.nan)
                priors.append(int(max(len(hist_pct), len(hist_ue))))
                srcs.append("")
                continue
            priors.append(n_prior)
            srcs.append(src)
            if not np.isfinite(sigma) or sigma <= 0:
                sigmas.append(np.nan)
                sues.append(np.nan)
                continue
            sigmas.append(sigma)
            sues.append(err / sigma)
        g["sigma_ue"] = sigmas
        g["sue"] = sues
        g["n_prior"] = priors
        g["sue_source"] = srcs
        pieces.append(g)
    return pd.concat(pieces, ignore_index=True)


def qualifying_prints(sue_events: pd.DataFrame, sue_threshold: float = 2.0) -> pd.DataFrame:
    return sue_events[
        sue_events["sue"].notna()
        & np.isfinite(sue_events["sue"])
        & (sue_events["sue"] > sue_threshold)
        & (sue_events["ue"].fillna(0) > 0)
    ].copy()


def latest_events_as_of(sue_events: pd.DataFrame, as_of) -> pd.DataFrame:
    if sue_events.empty:
        return sue_events.iloc[0:0].copy()
    as_of_d = pd.Timestamp(as_of).date()
    snap = sue_events[pd.to_datetime(sue_events["announce_date"]).dt.date <= as_of_d].copy()
    if snap.empty:
        return snap
    snap = snap.sort_values(["symbol", "announce_date"])
    return snap.groupby("symbol", as_index=False).tail(1)
