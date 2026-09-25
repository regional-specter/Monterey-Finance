"""Frozen Phase 1B book. Do not retune knobs here without a version bump."""

from __future__ import annotations

from ops.paths import ensure_research_on_path

ensure_research_on_path()

from sleeves.rules import FrozenRules  # noqa: E402

BOOK_VERSION = "1b-fcf-sma-v1"


def live_rules() -> FrozenRules:
    """FCF quality funnel, 10% name cap, whole-NAV SPY SMA to cash."""
    return FrozenRules().with_book(
        sleeve_weights={
            "fcf_quality": 1.0,
            "roic": 0.0,
            "sue": 0.0,
            "dual_momentum": 0.0,
            "high_beta": 0.0,
        },
        name_cap=0.10,
        throttle="spy_sma",
        collapse_share_classes=True,
        cost_bps=10.0,
        rebalance_freq="ME",
        breach_exit="next_open",
        breach_monitor="filings",
        purify_schedule="ex_date",
    )
