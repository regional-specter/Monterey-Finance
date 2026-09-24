"""Synthetic-data tests for sleeve selection, triggers, and blending."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from sleeves.fundamentals import attach_sue
from sleeves.lab import Lab
from sleeves.prices import spy_sma_risk_on
from sleeves.rules import FrozenRules
from sleeves.book import run_sleeve
from sleeves.costs import apply_flat_costs, l1_trade, one_way, trade_calendar
from sleeves.exits import apply_breach_exits, detect_breaches, drop_name, exit_session
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


def _two_month_metrics() -> pd.DataFrame:
    jan = _metrics("2024-01-31")
    feb = _metrics("2024-02-29")
    jan["filed_date"] = pd.Timestamp("2023-12-15")
    feb["filed_date"] = pd.Timestamp("2023-12-15")
    blow = feb["symbol"] == "AAA"
    feb.loc[blow, "filed_date"] = pd.Timestamp("2024-02-12")
    cap = float(feb.loc[blow, "market_cap_24m"].iloc[0])
    feb.loc[blow, "total_debt"] = 0.45 * cap
    feb.loc[blow, "debt_ratio"] = 0.45
    both = pd.concat([jan, feb], ignore_index=True)
    both["report_date"] = both["as_of"]
    return both


def test_exit_session_lags():
    idx = pd.bdate_range("2024-02-12", periods=5)
    assert exit_session(idx, date(2024, 2, 12), "same_day") == date(2024, 2, 12)
    assert exit_session(idx, date(2024, 2, 12), "next_open") == date(2024, 2, 13)
    assert exit_session(idx, date(2024, 2, 10), "same_day") == date(2024, 2, 12)
    assert exit_session(idx, date(2024, 2, 12), "month_end") is None


def test_filing_breach_and_same_day_drop():
    metrics = _two_month_metrics()
    idx = pd.bdate_range("2024-01-02", periods=45)
    px = pd.DataFrame({sym: np.linspace(100, 110, len(idx)) for sym in metrics["symbol"].unique()})
    px["SPY"] = np.linspace(100, 110, len(idx))
    px.index = idx
    prices = px.stack().rename("adj_close").reset_index()
    prices.columns = ["date", "symbol", "adj_close"]
    rules = FrozenRules().with_fcf(min_holdings=5).with_book(
        sleeve_weights={"fcf_quality": 1.0},
        name_cap=0.10,
        throttle="off",
        breach_exit="month_end",
    )
    lab = Lab.from_frames(metrics, prices, rules=rules, start="2024-01-31", end="2024-02-29")
    _, log = lab.book().run(start="2024-01-31")
    events = detect_breaches(metrics, log, lab.price_panel(), rules=rules, monitor="filings")
    assert not events.empty
    assert "AAA" in set(events["symbol"])
    assert events.iloc[0]["source"] == "filing"

    jan = date(2024, 1, 31)
    weights = {jan: log[pd.to_datetime(log["as_of"]).dt.date == jan].set_index("symbol")["weight"]}
    same = apply_breach_exits(weights, events, idx, lag="same_day", name_cap=0.10)
    nxt = apply_breach_exits(weights, events, idx, lag="next_open", name_cap=0.10)
    hold = apply_breach_exits(weights, events, idx, lag="month_end", name_cap=0.10)
    assert date(2024, 2, 12) in same
    assert "AAA" not in same[date(2024, 2, 12)].index
    assert date(2024, 2, 13) in nxt
    assert "AAA" not in nxt[date(2024, 2, 13)].index
    assert list(hold) == [jan]

    leftover = drop_name(weights[jan], "AAA", 0.10)
    assert "AAA" not in leftover.index
    assert abs(float(leftover.sum()) - 1.0) < 1e-9


def test_purify_ex_date_vs_year_end():
    from sleeves.purify import apply_purification, held_dividends, weight_on

    idx = pd.bdate_range("2024-01-02", periods=20)
    weights = {date(2024, 1, 2): pd.Series({"AAA": 0.10})}
    panel = pd.DataFrame({"AAA": np.full(len(idx), 100.0)}, index=idx)
    purified = pd.DataFrame(
        {
            "symbol": ["AAA"],
            "ex_date": [date(2024, 1, 3)],
            "dividend": [2.0],
            "impure_ratio": [0.05],
            "purification_amount": [0.10],
        }
    )
    events = held_dividends(purified, weights, panel)
    assert len(events) == 1
    assert events.iloc[0]["nav_frac"] == pytest.approx(0.10 * 0.10 / 100.0)

    rets = pd.Series(0.0, index=idx)
    rets.iloc[5] = 0.10
    net_ex = apply_purification(rets, events, schedule="ex_date", price_index=idx)
    net_ye = apply_purification(rets, events, schedule="year_end", price_index=idx)
    eq_ex = (1 + net_ex).cumprod().iloc[-1]
    eq_ye = (1 + net_ye).cumprod().iloc[-1]
    eq_gr = (1 + rets).cumprod().iloc[-1]
    assert eq_ex < eq_gr
    assert eq_ye < eq_gr
    # Delayed cheque lets the 10% up-day run on a larger NAV.
    assert eq_ye > eq_ex
    assert weight_on(weights, "AAA", date(2024, 1, 3)) == 0.10
    off = pd.Series(False, index=idx)
    assert weight_on(weights, "AAA", date(2024, 1, 3), throttle_on=off) == 0.0


def test_turnover_to_cash_and_flat_cost():
    prev = pd.Series({"AAA": 0.6, "BBB": 0.4})
    curr = pd.Series({"AAA": 0.5, "CCC": 0.5})
    assert l1_trade(prev, curr) == pytest.approx(1.0)  # 0.1+0.4 + 0.5
    assert one_way(prev, pd.Series(dtype=float)) == pytest.approx(0.5)
    assert l1_trade(prev, pd.Series(dtype=float)) == pytest.approx(1.0)

    idx = pd.bdate_range("2024-01-02", periods=5)
    weights = {date(2024, 1, 2): prev}
    throttle = pd.Series([True, True, False, False, False], index=idx)
    trades = trade_calendar(weights, idx, throttle_on=throttle)
    assert (trades["to_cash"] == True).any()
    assert float(trades.loc[trades["to_cash"], "traded_nav"].iloc[0]) == pytest.approx(1.0)

    rets = pd.Series(0.01, index=idx)
    net = apply_flat_costs(rets, trades, cost_bps=10)
    # 10 bp on 100% NAV the cash day
    cash_day = pd.Timestamp(trades.loc[trades["to_cash"], "date"].iloc[0])
    assert net.loc[cash_day] == pytest.approx(0.01 - 0.001)



