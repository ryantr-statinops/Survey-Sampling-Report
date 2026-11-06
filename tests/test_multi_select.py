"""Unit tests for PLAN §3.3 rules (independent small fixtures)."""

from survey_report.logic import multi_frequency, parse_multi


def test_q31_keeps_comma_inside_option():
    cell = "So sánh IELTS, TOEIC và APTIS, Lộ trình học và ôn thi"
    assert parse_multi(cell, "Q31") == [
        "So sánh IELTS, TOEIC và APTIS",
        "Lộ trình học và ôn thi",
    ]


def test_pet_aliases_merge_and_dedup_with_trailing_comma():
    assert parse_multi("Pet", "Q6") == ["PET (Cambridge)"]
    assert parse_multi("Cambridge (PET)", "Q6") == ["PET (Cambridge)"]
    # Duplicate IELTS counts once; trailing comma fragment dropped.
    assert parse_multi("IELTS, PET Cambridge, IELTS", "Q6") == ["IELTS", "PET (Cambridge)"]
    assert parse_multi("APTIS, ", "Q6") == ["APTIS"]


def test_multi_percent_may_exceed_100_and_uses_answering_denominator():
    rows = [
        {"q": "IELTS, APTIS"},
        {"q": "IELTS"},
        {"q": ""},  # not answering -> excluded from denominator
    ]
    freq = multi_frequency(rows, "q", "Q6")
    by_option = {f["option"]: f for f in freq}
    assert by_option["IELTS"]["denominator"] == 2
    assert by_option["IELTS"]["percent"] == 100.0
    assert by_option["APTIS"]["percent"] == 50.0
    total = sum(f["percent"] for f in freq)
    assert total == 150.0  # documents >100% rule for multi-select
