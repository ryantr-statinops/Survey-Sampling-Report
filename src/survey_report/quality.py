"""Local data-quality audit that never rewrites or emits raw response text."""

from __future__ import annotations

import re
import tomllib
from collections import Counter
from pathlib import Path

from survey_report.logic import KNOWN_OPTIONS, PET_ALIASES, PET_CANONICAL


def load_schema(config_path: Path) -> tuple[dict[str, set[str]], dict[str, str], set[str]]:
    """Return expected categories, multi-select headers, and required headers."""
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    variables = config["schema"]["variables"]
    categorical = {
        variable["source_header"]: set(variable.get("categories", []))
        for variable in variables
        if variable["kind"] == "categorical"
    }
    multi = {
        f"Q{index}": next(
            variable["source_header"]
            for variable in variables
            if variable["source_header"].startswith(f"Câu {index}.")
        )
        for index in (6, 8, 10, 30, 31)
    }
    required = {variable["source_header"] for variable in variables}
    return categorical, multi, required


def _unmatched_multi(value: str, question: str) -> list[str]:
    """Find unrecognized comma-delimited fragments while respecting known labels."""
    options = sorted(KNOWN_OPTIONS[question], key=len, reverse=True)
    text = value.strip()
    if question == "Q6":
        for alias in PET_ALIASES:
            text = re.sub(re.escape(alias), PET_CANONICAL, text, flags=re.IGNORECASE)
        options = sorted(set(options) | {PET_CANONICAL}, key=len, reverse=True)
    unknown: list[str] = []
    while text.strip(" ,;\n\t"):
        text = text.lstrip(" ,;\n\t")
        match = next(
            (option for option in options if text.casefold().startswith(option.casefold())), None
        )
        if match:
            text = text[len(match) :]
            continue
        fragment, separator, rest = text.partition(",")
        fragment = fragment.strip(" ;\n\t")
        if fragment:
            unknown.append(fragment)
        text = rest if separator else ""
    return unknown


def audit_responses(
    rows: list[dict[str, str]],
    headers: list[str],
    categorical: dict[str, set[str]],
    multi_headers: dict[str, str],
    required_headers: set[str],
) -> dict:
    """Summarize structural and value anomalies without copying free-text answers."""
    duplicate_headers = sorted({header for header in headers if headers.count(header) > 1})
    issues: list[dict] = []
    if duplicate_headers:
        issues.append(
            {
                "kind": "duplicate_headers",
                "count": len(duplicate_headers),
                "values": duplicate_headers,
            }
        )
    missing_headers = sorted(required_headers - set(headers))
    if missing_headers:
        issues.append(
            {"kind": "missing_headers", "count": len(missing_headers), "values": missing_headers}
        )
    for header, expected in categorical.items():
        unexpected = Counter(
            value.strip()
            for row in rows
            if (value := row.get(header, "") or "").strip() and value.strip() not in expected
        )
        for value, count in unexpected.most_common():
            issues.append(
                {"kind": "unknown_category", "field": header, "value": value, "count": count}
            )
    for question, header in multi_headers.items():
        unexpected = Counter(
            fragment
            for row in rows
            for fragment in _unmatched_multi(row.get(header, "") or "", question)
        )
        for value, count in unexpected.most_common():
            issues.append(
                {"kind": "unknown_multi_option", "field": header, "value": value, "count": count}
            )
    numeric_headers = [h for h in headers if re.search(r"\[(1[1-9]|2[0-7])\.", h)]
    invalid_scores: Counter[tuple[str, str]] = Counter()
    for row in rows:
        for header in numeric_headers:
            raw = (row.get(header, "") or "").strip()
            if raw:
                try:
                    valid = float(raw) in {1, 2, 3, 4, 5}
                except ValueError:
                    valid = False
                if not valid:
                    invalid_scores[(header, raw)] += 1
    for (header, value), count in invalid_scores.items():
        issues.append({"kind": "invalid_likert", "field": header, "value": value, "count": count})
    return {"row_count": len(rows), "issue_count": len(issues), "issues": issues}
