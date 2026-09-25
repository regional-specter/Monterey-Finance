"""python -m ops run — paper-fund session."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ops",
        description="Build today's intended Halal book from the frozen FCF + SMA rules.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Refresh (optional), write target weights, preview filing fails.")
    run.add_argument("--as-of", default="today", help="YYYY-MM-DD or today.")
    run.add_argument("--skip-refresh", action="store_true", help="Do not call halalquant refresh.")
    run.add_argument("--coverage", action="store_true", help="Write coverage_summary from the cache.")
    run.add_argument("--lookback-days", type=int, default=550, help="Price/metrics window into the cache.")
    run.add_argument("--no-persist", action="store_true", help="Print only; do not write ops/runs/.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    from ops.session import run_session

    try:
        result = run_session(
            args.as_of,
            refresh=not args.skip_refresh,
            coverage=args.coverage,
            persist=not args.no_persist,
            lookback_days=args.lookback_days,
        )
    except Exception as exc:
        sys.stderr.write(f"ops run failed: {exc}\n")
        return 1

    summary = result.book.summary()
    summary.update(result.extra)
    if result.folder:
        summary["run_dir"] = str(result.folder)
    print(json.dumps(summary, indent=2, default=str))
    if result.breaches is not None and not result.breaches.empty:
        print("\nFiling fails (library reports; fund sells next open):")
        cols = [c for c in ("symbol", "form", "filed_date", "reason") if c in result.breaches.columns]
        print(result.breaches[cols].to_string(index=False) if cols else result.breaches.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
