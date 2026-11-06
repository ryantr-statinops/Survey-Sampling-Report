# Survey-Sampling-Report

**University report project: survey sampling results for English certificate selection.**

This repository holds the reproducible report and presentation pipeline for the survey on English certificate choices (32 questions, 89 responses in the 04/11/2026 reference snapshot). Data is extracted from Google Sheets and published as refreshable Google Slides content via the VisuaSlide SDK pattern.

## Links

- Task spec: [Issue #1 — Tổng hợp và trực quan hóa kết quả khảo sát lựa chọn chứng chỉ tiếng Anh](https://github.com/ryantr-statinops/Survey-Sampling-Report/issues/1)
- Source data: [Google Sheets — Phiếu khảo sát lựa chọn chứng chỉ tiếng Anh (tab `gid=1653201454`)](https://docs.google.com/spreadsheets/d/14Ic0Zl7V5fr5dOkdo7ae5pwZpzk8v3HPGKliDHEQTiw/edit?gid=1653201454)
- Reference analysis: [VisuaSlide Issue #1](https://github.com/ryantr-statinops/VisuaSlide/issues/1)
- SDK reference: [VisuaSlide](https://github.com/ryantr-statinops/VisuaSlide) — Python SDK/CLI for survey → Sheets → Slides (see `_VisuaSlide_ref/` locally, git-ignored)

## Read first

- **Implementation plan:** [plan/PLAN.md](plan/PLAN.md) — scope for 32 questions, cleaning rules, 16 required charts (9 pie, 5 bar, 100% stacked Q11–27, mean comparison), Excel + report deliverables, automation roadmap, and acceptance criteria.

## Repository layout

```
.
├── README.md          # this file
├── .gitignore         # excludes _VisuaSlide_ref/ and Google runtime artifacts
├── plan/
│   └── PLAN.md        # detailed implementation plan (Proposed)
└── _VisuaSlide_ref/   # local clone for SDK study only — never commit (git-ignored)
```

## Intended workflow (VisuaSlide pattern)

```
One Google Sheets tab (spreadsheet_id + sheet_id)
  → Raw snapshot with metadata
  → Validate & prepare (pandas)
  → Clean dataset (Parquet)
  → Aggregate analysis (DuckDB SQL)
  → Reporting spreadsheet (aggregate tables + Sheets charts)
  → Google Slides (linked charts, tables, text)
```

Core stack: Python 3.12, `uv`, `google-api-python-client`, Pydantic/TOML, pandas, PyArrow, DuckDB, Typer.

Manual refresh comes first (`auth` → `bootstrap-outputs` → `refresh --dry-run` → `refresh` → `review-layout`); scheduling only after sandbox acceptance passes. Never commit credentials, tokens, real survey responses, or private snapshots.

Chi tiết kết nối Google Sheets/Slides + cách chèn PNG/Excel thủ công ngay hôm nay: [docs/google-connect.md](docs/google-connect.md).
Báo cáo độc lập: [report/report.md](report/report.md) · Bảng Excel: [report/stats.xlsx](report/stats.xlsx) · Biểu đồ: [report/charts/](report/charts/).

## Status

- `main` contains the plan and ignore rules (both pushed to `origin/main`).
- P1 offline pipeline → P2 charts + Excel → P3 report: **Implemented** on `feat/full-report-pipeline`
  (VisuaSlide pinned `2a566477`, TOML 32 câu A:AG, synthetic fixtures, 16 PNG + `report/stats.xlsx` + `report/report.md`, xem [docs/google-connect.md](docs/google-connect.md)).
- P4 automation acceptance (live Google sandbox): **Open** — cần owner tạo Google Cloud OAuth + chạy auth/bootstrap/refresh (hướng dẫn ở [docs/google-connect.md](docs/google-connect.md)).

## Contributing

- Keep commits small and separated (docs vs chore vs code) so reviewers can follow history.
- Do not commit `*.local.toml`, `google_outputs.json`, `client_secret*.json`, or runtime data.
- All percentages must show numerator, denominator, and missing-value policy; Q31 keeps `"So sánh IELTS, TOEIC và APTIS"` intact (no comma split).
