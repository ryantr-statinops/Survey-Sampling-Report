"""CLI: survey-report generate --csv PATH --out report --date YYYY-MM-DD."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from survey_report.quality import audit_responses, load_schema


def load_rows(csv_path: Path) -> tuple[list[dict], list[str]]:
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        headers = reader.fieldnames or []
        for row in reader:
            # Drop email column entirely (A:AG policy) — never keep in memory for outputs.
            rows.append({k: v for k, v in row.items() if k != "Địa chỉ email"})
        return rows, headers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="survey-report")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--csv", type=Path, required=True)
    g.add_argument("--out", type=Path, default=Path("report"))
    g.add_argument("--date", default="2026-11-06")
    g.add_argument("--config", type=Path, default=Path("config/survey.english_certs.example.toml"))
    args = parser.parse_args(argv)
    if args.cmd == "generate":
        from survey_report.charts import generate_charts
        from survey_report.excel import build_workbook
        from survey_report.report import build_markdown

        rows, headers = load_rows(args.csv)
        categorical, multi_headers, required_headers = load_schema(args.config)
        quality = audit_responses(rows, headers, categorical, multi_headers, required_headers)
        charts_dir = args.out / "charts"
        generate_charts(rows, charts_dir)
        build_workbook(rows, args.out / "stats.xlsx")
        (args.out / "report.md").write_text(build_markdown(rows, args.date), encoding="utf-8")
        (args.out / "summary.json").write_text(
            json.dumps({"date": args.date, "n": len(rows)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (args.out / "quality.json").write_text(
            json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Data quality: {quality['issue_count']} unrecognized or invalid values.")
        print(f"OK n={len(rows)} -> {args.out}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
