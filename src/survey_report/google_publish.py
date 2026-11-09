"""Publish the configured survey while allowing all 13 faculty categories."""

from __future__ import annotations

import argparse

from visuaslide import SurveyProject, google_publisher, layouts, reporting
from visuaslide import api as api_module


def _build_faculty_readable_content(analysis, report):
    content = _build_content(analysis, report)
    faculty_chart = next(
        chart for chart in content.charts if chart.source_analysis_id == "faculty_counts"
    )
    charts = tuple(
        chart.model_copy(update={"chart_type": "bar"})
        if chart.source_analysis_id == "faculty_counts"
        else chart
        for chart in content.charts
    )
    # Keep this caption inside the template's 640x60 text box; the SDK's default
    # caption serializes all category statistics and otherwise overlaps the chart.
    faculty_caption = (
        f"Phân bố theo {len(faculty_chart.categories)} khoa; "
        f"số phản hồi hợp lệ n={analysis.accepted_rows}."
    )
    text_blocks = tuple(
        item.model_copy(update={"text": faculty_caption})
        if item.object_id == "caption_faculty_counts"
        else item
        for item in content.text_blocks
    )
    return content.model_copy(update={"charts": charts, "text_blocks": text_blocks})


_build_content = reporting.build_presentation_content
_base_layout = layouts.build_default_layout
_base_chart_spec = google_publisher.GoogleReportPublisher._chart_spec


def _layout_with_full_faculty_chart(content):
    from visuaslide.layouts import LayoutLimits

    return _base_layout(content, LayoutLimits(max_chart_categories=15))


def _chart_spec_with_valid_axis(chart, sheet_id):
    spec = _base_chart_spec(chart, sheet_id)
    if chart.chart_type == "bar":
        for series in spec["basicChart"]["series"]:
            series["targetAxis"] = "BOTTOM_AXIS"
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/survey.english_certs.local.toml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume-run-id")
    args = parser.parse_args()

    reporting.build_presentation_content = _build_faculty_readable_content
    api_module.build_default_layout = _layout_with_full_faculty_chart
    google_publisher.build_default_layout = _layout_with_full_faculty_chart
    google_publisher.GoogleReportPublisher._chart_spec = staticmethod(_chart_spec_with_valid_axis)

    project = SurveyProject.from_toml(args.config)
    result = (
        project.resume(args.resume_run_id)
        if args.resume_run_id
        else project.refresh(dry_run=args.dry_run)
    )
    print(
        f"status={result.status.value} stage={result.stage} "
        f"accepted_rows={result.analysis.accepted_rows if result.analysis else 0} "
        f"run_id={result.run_id}"
    )
    return 0 if result.status.value in {"ready", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
