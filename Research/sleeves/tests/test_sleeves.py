"""Synthetic-data tests for sleeve selection, triggers, and blending."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from sleeves.fundamentals import attach_sue
from sleeves.lab import Lab
from sleeves.prices import spy_sma_risk_on
from sleeves.rules import FrozenRules
from sleeves.book import run_sleeve
from sleeves.select import select_dual_momentum, select_fcf_quality, select_roic, select_sue
from sleeves.weighting import blend_sleeve_weights


def _metrics(as_of="2024-01-31") -> pd.DataFrame:
    rows = []
    names = [
        ("AAA", 0.40, 1e11, 0.05),
        ("BBB", 0.20, 8e10, 0.08),
        ("CCC", 0.10, 5e10, 0.12),
        ("DDD", 0.02, 4e10, 0.10),
        ("EEE", -0.05, 3e10, 0.09),
        ("FFF", 0.30, 2e10, 0.07),
        ("GGG", 0.25, 1.5e10, 0.06),
        ("HHH", 0.18, 1.2e10, 0.11),
        ("III", 0.15, 1.1e10, 0.04),
        ("JJJ", 0.12, 1.0e10, 0.03),
        ("KKK", 0.08, 9e9, 0.02),
        ("LLL", 0.06, 8e9, 0.15),
        ("MMM", 0.05, 7e9, 0.20),
        ("NNN", 0.04, 6e9, 0.18),
        ("OOO", 0.03, 5e9, 0.16),
        ("PPP", 0.35, 4e9, 0.01),
        ("QQQ", 0.28, 3e9, 0.02),
        ("RRR", 0.22, 2e9, 0.03),
        ("SSS", 0.16, 1.5e9, 0.04),
        ("TTT", 0.14, 1.2e9, 0.05),
        ("UUU", 0.11, 1.0e9, 0.06),
    ]
    for sym, margin, cap, debt in names:
        sales = 1e9
        fcf = margin * sales
        rows.append(
            {
                "symbol": sym,
                "as_of": pd.Timestamp(as_of).date(),
                "market_cap": cap,
                "market_cap_24m": cap,
                "total_debt": debt * cap,
                "cash_and_equiv": 0.02 * cap,
                "interest_bearing_securities": 0.0,
                "receivables": 0.05 * cap,
                "liquid_assets": 0.0,
                "total_revenue": sales,
                "fcf": fcf,
                "roic": 0.20 if margin > 0.05 else 0.08,
                "reinvestment_rate": 0.40 if margin > 0.15 else 0.10,
                "nopat": 1e8,
                "invested_capital": 5e8,
            }
        )
    return pd.DataFrame(rows)


def test_fcf_keeps_top_half():
    rules = FrozenRules().with_fcf(keep_quantile=0.50, min_holdings=5)
    picks = select_fcf_quality(_metrics(), "2024-01-31", rules)
    assert len(picks) >= 5
    assert "AAA" in set(picks["symbol"])
    assert abs(picks["weight"].sum() - 1.0) < 1e-9


def test_roic_floor_drops_low_roic():
    rules = FrozenRules().with_roic(roic_min=0.15, keep_quantile=0.50, min_holdings=5)
    picks = select_roic(_metrics(), "2024-01-31", rules)
    assert (picks["roic"] > 0.15).all()
    assert (picks["reinvestment_rate"] > 0).all()


def test_sma_trigger_off_when_below_average():
    idx = pd.bdate_range("2023-01-02", periods=250)
    # Last close well below the trailing mean
    px = pd.Series(np.linspace(100, 80, len(idx)), index=idx)
    assert spy_sma_risk_on(px, idx[-1], sma_window=200) is False
    px_up = pd.Series(np.linspace(80, 120, len(idx)), index=idx)
    assert spy_sma_risk_on(px_up, idx[-1], sma_window=200) is True


def test_name_cap_and_blend():
    a = pd.Series({"NVDA": 0.9, "MSFT": 0.1})
    b = pd.Series({"NVDA": 0.5, "AAPL": 0.5})
    blended = blend_sleeve_weights(
        {"fcf_quality": a, "roic": b},
        {"fcf_quality": 0.5, "roic": 0.5},
        name_cap=0.40,
    )
    assert blended.max() <= 0.40 + 1e-9
    assert abs(blended.sum() - 1.0) < 1e-9


def test_sue_hold_window():
    dates = pd.bdate_range("2024-01-02", periods=40)
    earnings = pd.DataFrame(
        {
            "symbol": ["AAA"] * 8,
            "announce_date": pd.bdate_range("2023-01-03", periods=8, freq="10B"),
            "ue": [0.1] * 8,
            "surprise_pct": [0.1, 0.12, 0.08, 0.11, 0.09, 0.1, 0.13, 0.5],
        }
    )
    sue = attach_sue(earnings, min_prior=6)
    assert float(sue.iloc[-1]["sue"]) > 2
    metrics = _metrics("2023-12-29")
    # Announce on 2024-01-03, evaluate 5 trading days later
    events = pd.DataFrame(
        {
            "symbol": ["AAA"],
            "announce_date": [date(2024, 1, 3)],
            "sue": [3.0],
            "ue": [0.2],
            "sigma_ue": [0.05],
        }
    )
    rules = FrozenRules().with_sue(hold_trading_days=21, min_holdings=1)
    picks = select_sue(metrics, events, dates, "2024-01-10", rules)
    assert list(picks["symbol"]) == ["AAA"]
    empty = select_sue(metrics, events, dates, "2024-03-01", rules)
    assert empty.empty


def test_lab_evaluate_dual_momentum_cash():
    metrics = _metrics("2024-01-31")
    idx = pd.bdate_range("2023-01-02", periods=260)
    px = pd.DataFrame({sym: np.linspace(100, 70, len(idx)) for sym in metrics["symbol"].unique()})
    px["SPY"] = np.linspace(100, 70, len(idx))
    px.index = idx
    prices = px.stack().rename("adj_close").reset_index()
    prices.columns = ["date", "symbol", "adj_close"]
    hist = pd.DataFrame(
        {
            "symbol": metrics["symbol"],
            "filed_date": pd.Timestamp("2023-12-01"),
            "fcf": metrics["fcf"],
        }
    )
    lab = Lab.from_frames(metrics, prices, fcf_history=hist)
    state = lab.evaluate("2024-01-31", sleeves=("fcf_quality", "dual_momentum"))
    assert state["dual_momentum"].triggered is False
    assert "cash" in state["dual_momentum"].reason.lower() or "below" in state["dual_momentum"].reason.lower()
    assert state["fcf_quality"].n_holdings >= 5


def test_dual_momentum_empty_snapshot_no_keyerror():
    picks = select_dual_momentum(_metrics("2024-01-31"), pd.DataFrame(), "2020-01-31")
    assert picks.empty
    assert list(picks.columns)


def test_run_sleeve_ignores_sue_dates_for_core():
    metrics = _metrics("2024-01-31")
    idx = pd.bdate_range("2023-01-02", periods=260)
    px = pd.DataFrame({sym: np.linspace(80, 120, len(idx)) for sym in metrics["symbol"].unique()})
    px["SPY"] = np.linspace(80, 120, len(idx))
    px.index = idx
    prices = px.stack().rename("adj_close").reset_index()
    prices.columns = ["date", "symbol", "adj_close"]
    lab = Lab.from_frames(
        metrics,
        prices,
        sue_events=pd.DataFrame(
            {
                "symbol": ["AAA"],
                "announce_date": [date(2023, 6, 15)],
                "sue": [3.0],
            }
        ),
        rules=FrozenRules().with_dual_momentum(apply_sma=False, min_holdings=5, keep_quantile=0.5),
    )
    ret, log = run_sleeve(lab, "dual_momentum", start="2023-01-02")
    assert not ret.empty
    if not log.empty:
        assert date(2023, 6, 15) not in set(pd.to_datetime(log["as_of"]).dt.date)
