from pathlib import Path

from survey_report.quality import audit_responses, load_schema

ROOT = Path(__file__).parents[1]


def test_schema_maps_categorical_and_multiselect_headers():
    categorical, multi, required = load_schema(ROOT / "config/survey.english_certs.example.toml")
    assert len(categorical) == 9
    assert multi["Q31"].startswith("Câu 31.")
    assert len(required) == 33


def test_audit_flags_unknown_multiselect_and_invalid_rating():
    categorical, multi, required = load_schema(ROOT / "config/survey.english_certs.example.toml")
    headers = [
        "Câu 1. Giới tính của bạn là gì?",
        "Câu 6. Bạn đã từng thi chứng chỉ tiếng Anh nào? (Có thể chọn nhiều đáp án)",
        "Yếu tố cá nhân [11. Mục tiêu nghề nghiệp]",
    ]
    rows = [{headers[0]: "Nam ", headers[1]: "IELTS, Chứng chỉ lạ", headers[2]: "7"}]
    audit = audit_responses(rows, headers, categorical, multi, required)
    assert {issue["kind"] for issue in audit["issues"]} >= {
        "unknown_multi_option",
        "invalid_likert",
        "missing_headers",
    }
    assert audit["row_count"] == 1


def test_audit_respects_comma_inside_q31_option():
    categorical, multi, required = load_schema(ROOT / "config/survey.english_certs.example.toml")
    header = multi["Q31"]
    audit = audit_responses(
        [{header: "So sánh IELTS, TOEIC và APTIS, Lộ trình học và ôn thi"}],
        list(required),
        categorical,
        multi,
        required,
    )
    assert not audit["issues"]
