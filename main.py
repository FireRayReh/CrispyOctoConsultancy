"""Entry point: fetch sources, score items, write a markdown report.

Usage:
    python main.py --window daily
    python main.py --window weekly
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

from pipeline.fetch import fetch_all, load_sources
from pipeline.report import build_report, window_since
from pipeline.score import score_items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--sources", default="sources.yaml")
    parser.add_argument("--out-dir", default="reports")
    args = parser.parse_args()

    sources = load_sources(args.sources)
    fetch_result = fetch_all(sources)
    scored = score_items(fetch_result.items)

    since = window_since(args.window)
    report = build_report(
        scored=scored,
        fetch_result=fetch_result,
        window_label=args.window.capitalize(),
        since=since,
    )

    os.makedirs(args.out_dir, exist_ok=True)
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    out_path = os.path.join(args.out_dir, f"{today}-{args.window}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    latest_path = os.path.join(args.out_dir, f"latest-{args.window}.md")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Wrote {out_path}")
    print(f"OK sources: {len(fetch_result.ok_sources)} | Failed: {len(fetch_result.failed_sources)}")


if __name__ == "__main__":
    main()
