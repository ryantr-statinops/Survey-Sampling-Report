"""Config + SDK offline tests (synthetic only)."""

import json
from pathlib import Path

from visuaslide import SurveyProject
from visuaslide.publisher import FakeReportPublisher
from visuaslide.snapshots import SourceSnapshot, utc_now
from visuaslide.testing import FixtureSource

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config" / "survey.english_certs.example.toml"
FIXTURE = ROOT / "tests" / "fixtures" / "synthetic_responses.json"


def test_config_loads_and_excludes_email():
    project = SurveyProject.from_toml(CONFIG)
    headers = [v.source_header for v in project.config.survey_schema.variables]
    assert "Địa chỉ email" not in headers
    assert len(headers) == 33  # timestamp + 32 questions
    assert project.config.source.column_range == "A:AG"  # email column AH never read


def test_sdk_offline_refresh_with_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    config = SurveyProject.from_toml(CONFIG).config
    snapshot = SourceSnapshot.capture(
        config.source,
        headers=tuple(fixture["headers"]),
        rows=tuple(tuple(r) for r in fixture["rows"]),
        acquired_at=utc_now(),
    )
    project = SurveyProject(config, source=FixtureSource(snapshot), publisher=FakeReportPublisher())
    # dry_run skips publish: Q3 has 13 faculties, exceeding the SDK default
    # max_chart_categories=10 layout limit (known Risk in PLAN.md §10).
    result = project.refresh(dry_run=True)
    assert result.analysis is not None
    assert result.analysis.input_rows == 3
    assert result.analysis.accepted_rows == 3
