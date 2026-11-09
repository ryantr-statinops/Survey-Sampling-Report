# Repository Guidelines

## Project Structure & Module Organization

This repository contains a reproducible reporting pipeline for English certificate choices across 32 survey questions.

- `README.md`: project overview and workflow.
- `plan/PLAN.md`: survey requirements, statistical rules, deliverables, and acceptance criteria.
- `plan/SDK_USAGE.md`: accepted SDK integration and setup instructions; its dependency approach supersedes the earlier SDK-copy proposal.
- `src/survey_sampling_report/`: consumer pipeline and descriptive statistics.
- `tests/`: synthetic fixture tests; never store real responses here.
- `config/`: shareable example TOML; local credentials belong only in ignored runtime paths.
- `_VisuaSlide_ref/`: ignored local reference clone; never commit or modify it as project implementation.

Planned additions include `config/` for example TOML, `src/` for consumer code, and `tests/fixtures/` for synthetic responses. Keep private runtime artifacts under each developer’s `.visuaslide/<name>/` directory.

## Build, Test, and Development Commands

Use Python 3.12 and `uv`:

```powershell
uv sync --locked --group dev
uv run --locked pytest tests
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
```

These install locked dependencies, run tests, lint, and check formatting. Configure pytest and Ruff when introducing code. Follow `plan/SDK_USAGE.md` for fixture-based `visuaslide refresh --dry-run` and Google sandbox setup. Consume VisuaSlide as a Git dependency pinned to a full commit SHA; commit dependency and lockfile updates together.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions/modules, and `PascalCase` classes. Use Ruff for Python formatting. Name shareable configurations `*.example.toml` and private overrides `*.local.toml`. Preserve Vietnamese question text and labels.

## Testing Guidelines

Use pytest with `test_*.py` files and independently calculated synthetic fixtures. Cover missing values, invalid categories, multi-select deduplication, PET normalization, and Q31’s intact “So sánh IELTS, TOEIC và APTIS” option. No coverage threshold is established. Keep live Google tests opt-in; validate synthetic sandbox refreshes before real-data publishing or scheduling. Visually review chart labels and slide layouts.

## Commit & Pull Request Guidelines

History uses `docs:` and `chore:` prefixes with concise imperative descriptions. Keep documentation, tooling, and code changes focused. PRs should explain the change, reference the relevant issue or plan requirement, and report validation; include sanitized previews for visual changes.

## Data & Configuration Safety

Never commit credentials, tokens, real responses, private snapshots, or email addresses. Report percentages with numerator, denominator, and missing-value policy. Record extraction dates; treat 89 responses as a historical reference. Keep source Sheets read-only and conclusions descriptive.
