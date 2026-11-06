"""Generate report.md from aggregates (no raw responses in output)."""
# Long Vietnamese report strings are intentional; E501 disabled per module.
# ruff: noqa: E501

from __future__ import annotations

from survey_report.logic import GROUPS, frequency, multi_frequency, numeric_summary

Q11_27 = sum(GROUPS.values(), [])


def _md_freq(freq: list[dict]) -> str:
    lines = ["| Phương án | Số lượt | Tỷ lệ | Mẫu số |", "|---|---:|---:|---:|"]
    for f in freq:
        lines.append(f"| {f['option']} | {f['count']} | {f['percent']}% | {f['denominator']} |")
    return "\n".join(lines)


def build_markdown(rows: list[dict], extraction_date: str) -> str:
    n = len(rows)
    out = [
        "# Báo cáo khảo sát lựa chọn chứng chỉ tiếng Anh — kết quả mẫu đã trả lời",
        "",
        "Nguồn: Google Sheets tab `gid=1653201454` (spreadsheet `14Ic0Zl7V5fr5dOkdo7ae5pwZpzk8v3HPGKliDHEQTiw`).",
        f"Ngày trích xuất: {extraction_date} · Số bản ghi: {n} · 32 câu hỏi + cột thời gian (email bị loại khỏi schema, range A:AG).",
        "",
        "> Đây là mô tả mẫu thuận tiện, **không** suy diễn nhân quả hay đại diện toàn trường. Số bản ghi ≠ số người duy nhất đã xác minh (chưa có cơ chế xác minh trùng lặp). Tỷ lệ làm tròn 1 chữ số; TB giữ precision, làm tròn hiển thị 2 chữ số.",
        "",
        "## 1. Đặc điểm mẫu (Q1–Q5)",
    ]
    for col in [
        "Câu 1. Giới tính của bạn là gì?",
        "Câu 2. Bạn đang là sinh viên năm mấy?",
        "Câu 3. Bạn đang học khoa nào?",
        "Câu 4. Bạn đánh giá trình độ tiếng Anh của mình ở mức nào?",
        "Câu 5. Bạn đã từng ôn thi hoặc thi chứng chỉ tiếng Anh chưa?",
    ]:
        out += [f"### {col}", "", _md_freq(frequency(rows, col)), ""]
    out += [
        "## 2. Chứng chỉ đã thi / dự định thi (Q6–Q10)",
        "",
        "*Câu chọn nhiều đáp án: mẫu số = số bản ghi trả lời; tổng % có thể >100%; mỗi phương án tính 1 lần mỗi bản ghi.*",
        "",
    ]
    for col, qid in [
        ("Câu 6. Bạn đã từng thi chứng chỉ tiếng Anh nào? (Có thể chọn nhiều đáp án)", "Q6"),
        ("Câu 7. Bạn dự định thi chứng chỉ nào trong thời gian tới?", "Q7"),
        ("Câu 8. Bạn muốn thi chứng chỉ tiếng Anh để làm gì? (Có thể chọn nhiều đáp án)", "Q8"),
        ("Câu 9. Bạn dự định thi chứng chỉ khi nào?", "Q9"),
        ("Câu 10. Bạn tìm thông tin về chứng chỉ từ đâu? (Có thể chọn nhiều đáp án)", "Q10"),
    ]:
        freq = (
            multi_frequency(rows, col, qid)
            if qid.startswith("Q") and col.endswith("đáp án)")
            else frequency(rows, col)
        )
        out += [f"### {col}", "", _md_freq(freq), ""]
    out += [
        "## 3. Thang điểm 1–5 (Q11–Q27) — chỉ trình bày điểm số",
        "",
        "| Yếu tố | n | TB | Trung vị | Tỷ lệ 4–5 |",
        "|---|---:|---:|---:|---:|",
    ]
    for col in Q11_27:
        s = numeric_summary(rows, col)
        out.append(f"| {col} | {s['n']} | {s['mean']} | {s['median']} | {s['share_4_5']}% |")
    out += ["", "### TB theo 5 nhóm yếu tố", "", "| Nhóm | TB |", "|---|---:|"]
    for name, cols in GROUPS.items():
        vals = [numeric_summary(rows, c)["mean"] for c in cols]
        vals = [v for v in vals if v is not None]
        out.append(f"| {name} | {round(sum(vals) / len(vals), 2) if vals else ''} |")
    out += ["", "## 4. Đánh giá tổng thể (Q28–Q31)", ""]
    for col in [
        "Câu 28. Chứng chỉ bạn đã chọn hoặc dự định thi phù hợp với bạn ở mức nào?",
        "Câu 29. Bạn có muốn giới thiệu chứng chỉ này cho sinh viên khác không?",
    ]:
        out += [f"### {col}", "", _md_freq(frequency(rows, col)), ""]
    for col, qid in [
        ("Câu 30. Bạn gặp khó khăn gì khi chọn chứng chỉ? (Có thể chọn nhiều đáp án)", "Q30"),
        ("Câu 31. Bạn muốn nhà trường cung cấp thông tin gì? (Có thể chọn nhiều đáp án)", "Q31"),
    ]:
        out += [f"### {col}", "", _md_freq(multi_frequency(rows, col, qid)), ""]
    q32 = "Câu 32. Bạn có góp ý gì để giúp sinh viên chọn chứng chỉ phù hợp?"
    nonempty = sum(1 for r in rows if (r.get(q32) or "").strip())
    out += [
        "## 5. Góp ý mở Q32 (định tính)",
        "",
        f"- Có nội dung: {nonempty} ({round(nonempty * 100 / n, 1) if n else 0}%, mẫu số {n}).",
        f"- Trống: {n - nonempty} ({round((n - nonempty) * 100 / n, 1) if n else 0}%, mẫu số {n}).",
        '- Các câu như "Không", "oke", "N/A" được tính là có nhập nội dung, không tự coi là góp ý thực chất. Chi tiết nguyên văn chỉ đưa vào phụ lục khi đã ẩn danh — không commit văn bản thô có email/định danh.',
        "",
        "## 6. Nhận xét mô tả (không suy diễn nhân quả)",
        "",
        "- Mẫu tập trung ở nhóm đã trả lời (xem Q1–Q3); không khái quát toàn trường.",
        '- Phần lớn mục đích là "Xin việc hoặc phát triển nghề nghiệp" và nguồn thông tin chủ yếu là kênh online (xem Q8, Q10), mô tả nhu cầu tư vấn có cơ sở tham khảo từ kết quả mẫu.',
        "- Khó khăn được nêu nhiều nhất thường liên quan chi phí/độ khó; nhu cầu hỗ trợ nổi bật nhất là lộ trình học/ôn thi và thông tin công nhận/chuẩn đầu ra (xem Q30–Q31).",
        '- TB Q11–Q27 cho biết mức điểm trung bình của mẫu, không gán nhãn "đồng ý/ảnh hưởng" vì chưa có chú giải 1–5.',
        "",
        "## 7. Đề xuất nội dung tư vấn (gắn với kết quả, không khẳng định hiệu quả)",
        "",
        "- Tài liệu so sánh IELTS/TOEIC/APTIS (+ PET/PTE nếu có) theo mục tiêu, trình độ, cấu trúc, chi phí, thời gian.",
        "- Lộ trình học, tự đánh giá trình độ, kênh truyền thông online kết hợp dẫn về nguồn chính thức.",
        "- Đối chiếu quy định công nhận/ chuẩn đầu ra với thông báo hiện hành của nhà trường.",
        "",
        "## 8. Giới hạn",
        "",
        "- Thiết kế lấy mẫu chưa rõ → không weights, CI, kiểm định giả thuyết; không suy luận quần thể.",
        '- Mâu thuẫn cần ghi chú: Q5–Q6 và Q30 (chọn đồng thời "Không gặp khó khăn" + khó khăn khác); Q28 (6 lượt "Chưa chọn chứng chỉ") và Q29 (7 lượt) không đồng nhất hai nhóm.',
        '- PET gộp variants về "PET (Cambridge)"; gốc không sửa. Q31 giữ nguyên "So sánh IELTS, TOEIC và APTIS".',
        "- Refresh qua SDK đọc toàn bộ tab (A:AG) mỗi lần; partial failure phải hiện trong run manifest, không báo success khi mới update một phần.",
        "",
        "## 9. Phương pháp & tái tạo",
        "",
        "- Pipeline: Sheets tab → raw snapshot (API values + metadata, gitignored) → validate/prepare (pandas) → Parquet (gitignored) → DuckDB (SDK) → bảng tổng hợp + charts PNG + Excel + báo cáo. Consumer logic multi-select ở `src/survey_report/logic.py`.",
        "- Tái tạo offline (synthetic): `uv sync --locked --group dev` → `uv run --locked pytest` → SDK dry-run với fixture (xem `docs/google-connect.md`).",
        "- Đối chiếu: tổng số & tỷ lệ kiểm tra chéo independent fixtures nhỏ; biểu đồ kiểm tra không cắt nhãn (PNG 300 dpi, nền trắng).",
    ]
    return "\n".join(out) + "\n"
