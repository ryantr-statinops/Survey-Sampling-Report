"""stats.xlsx — aggregate tables openable in Excel (no raw responses)."""
# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from survey_report.logic import GROUPS, frequency, multi_frequency, numeric_summary

SINGLE = [
    ("Câu 1. Giới tính của bạn là gì?", "Q01"),
    ("Câu 2. Bạn đang là sinh viên năm mấy?", "Q02"),
    ("Câu 3. Bạn đang học khoa nào?", "Q03"),
    ("Câu 4. Bạn đánh giá trình độ tiếng Anh của mình ở mức nào?", "Q04"),
    ("Câu 5. Bạn đã từng ôn thi hoặc thi chứng chỉ tiếng Anh chưa?", "Q05"),
    ("Câu 7. Bạn dự định thi chứng chỉ nào trong thời gian tới?", "Q07"),
    ("Câu 9. Bạn dự định thi chứng chỉ khi nào?", "Q09"),
    ("Câu 28. Chứng chỉ bạn đã chọn hoặc dự định thi phù hợp với bạn ở mức nào?", "Q28"),
    ("Câu 29. Bạn có muốn giới thiệu chứng chỉ này cho sinh viên khác không?", "Q29"),
]
MULTI = [
    ("Câu 6. Bạn đã từng thi chứng chỉ tiếng Anh nào? (Có thể chọn nhiều đáp án)", "Q6", "Q06"),
    ("Câu 8. Bạn muốn thi chứng chỉ tiếng Anh để làm gì? (Có thể chọn nhiều đáp án)", "Q8", "Q08"),
    ("Câu 10. Bạn tìm thông tin về chứng chỉ từ đâu? (Có thể chọn nhiều đáp án)", "Q10", "Q10"),
    ("Câu 30. Bạn gặp khó khăn gì khi chọn chứng chỉ? (Có thể chọn nhiều đáp án)", "Q30", "Q30"),
    ("Câu 31. Bạn muốn nhà trường cung cấp thông tin gì? (Có thể chọn nhiều đáp án)", "Q31", "Q31"),
]
Q11_27 = sum(GROUPS.values(), [])


def _write_freq(ws, title: str, freq: list[dict]) -> None:
    ws["A1"] = title
    ws["A1"].font = Font(bold=True)
    ws.append(["Phương án", "Số lượt", "Tỷ lệ (%)", "Mẫu số (n)"])
    for f in freq:
        ws.append([f["option"], f["count"], f["percent"], f["denominator"]])


def build_workbook(rows: list[dict], out_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    ws["A1"] = "Bảng thống kê khảo sát lựa chọn chứng chỉ tiếng Anh"
    ws["A2"] = (
        f"N bản ghi: {len(rows)}. Mỗi % kèm số lượt và mẫu số. Câu chọn nhiều đáp án: mẫu số = số bản ghi trả lời câu đó, tổng % có thể >100%."
    )
    ws["A3"] = (
        "Không chứa email hoặc văn bản thô. Q31 giữ nguyên 'So sánh IELTS, TOEIC và APTIS'. PET variants gộp thành 'PET (Cambridge)'."
    )
    for column, sheet in SINGLE:
        ws2 = wb.create_sheet(sheet)
        _write_freq(ws2, column, frequency(rows, column))
    for column, qid, sheet in MULTI:
        ws2 = wb.create_sheet(sheet)
        _write_freq(ws2, column, multi_frequency(rows, column, qid))
    ws2 = wb.create_sheet("Q11_Q27")
    ws2["A1"] = "Điểm 1–5: số lượt từng mức, TB, trung vị, min/max/SD mô tả, tỷ lệ chọn 4–5"
    ws2["A1"].font = Font(bold=True)
    ws2.append(
        [
            "Yếu tố",
            "n",
            "1",
            "2",
            "3",
            "4",
            "5",
            "TB",
            "Trung vị",
            "min",
            "max",
            "SD",
            "Tỷ lệ 4–5 (%)",
        ]
    )
    for col in Q11_27:
        s = numeric_summary(rows, col)
        ws2.append(
            [
                col,
                s["n"],
                *s["levels"],
                s["mean"],
                s["median"],
                s["min"],
                s["max"],
                s["sd"],
                s["share_4_5"],
            ]
        )
    ws2 = wb.create_sheet("Q32")
    ws2["A1"] = "Q32 góp ý mở (định tính, không chấm tần suất giả)"
    nonempty = sum(
        1
        for r in rows
        if (
            r.get("Câu 32. Bạn có góp ý gì để giúp sinh viên chọn chứng chỉ phù hợp?") or ""
        ).strip()
    )
    ws2.append(["Chỉ tiêu", "Số bản ghi", "Tỷ lệ (%)", "Mẫu số"])
    ws2.append(
        ["Có nội dung", nonempty, round(nonempty * 100 / len(rows), 1) if rows else 0, len(rows)]
    )
    ws2.append(
        [
            "Trống",
            len(rows) - nonempty,
            round((len(rows) - nonempty) * 100 / len(rows), 1) if rows else 0,
            len(rows),
        ]
    )
    wb.save(out_path)
    return out_path
