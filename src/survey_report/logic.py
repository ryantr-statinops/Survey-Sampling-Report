"""Survey aggregation logic (consumer layer).

SDK handles single-choice + numeric + text (raw). This module handles the
multi-select questions Q6/Q8/Q10/Q30/Q31 with a known-option parser:

- P1: trim whitespace, drop empty fragments after trailing commas.
- P2: known-option matching (longest first) instead of naive comma split,
  so Q31 keeps "So sánh IELTS, TOEIC và APTIS" intact.
- P3: PET aliases merged to "PET (Cambridge)" without mutating raw values.
- P4: each option counts once per response (dedup within a cell).
- P5: percent denominator = records answering that question (non-empty).
"""

from __future__ import annotations

import statistics
from collections import Counter

# Stable output order = order listed here (matches PLAN §3).
KNOWN_OPTIONS: dict[str, list[str]] = {
    "Q6": ["IELTS", "TOEIC", "APTIS", "PET (Cambridge)", "PTE", "Chưa thi chứng chỉ nào"],
    "Q8": [
        "Đáp ứng điều kiện tốt nghiệp",
        "Phục vụ học tập",
        "Xin việc hoặc phát triển nghề nghiệp",
        "Du học",
        "Phát triển bản thân",
        "không thi",
    ],
    "Q10": [
        "Nhà trường hoặc khoa",
        "Giảng viên",
        "Bạn bè hoặc người thân",
        "Trung tâm ngoại ngữ",
        "Mạng xã hội hoặc Internet",
    ],
    "Q30": [
        "Thiếu thông tin để so sánh các chứng chỉ",
        "Chưa rõ yêu cầu chuẩn đầu ra",
        "Chi phí học hoặc thi cao",
        "Khó đánh giá chứng chỉ nào phù hợp với năng lực",
        "Lo ngại độ khó hoặc khả năng đạt điểm",
        "Không gặp khó khăn",
    ],
    "Q31": [
        "So sánh IELTS, TOEIC và APTIS",
        "Quy định công nhận chứng chỉ và chuẩn đầu ra",
        "Lộ trình học và ôn thi",
        "Thông tin chi phí và địa điểm thi",
        "Tư vấn chọn chứng chỉ theo mục tiêu cá nhân",
        "không cần",
    ],
}

PET_CANONICAL = "PET (Cambridge)"
PET_ALIASES = ("Pet", "Cambridge (PET)", "PET Cambridge", "PET")


def parse_multi(cell: str | None, question: str) -> list[str]:
    """Return deduped known options present in one cell, in known order."""
    if cell is None:
        return []
    text = str(cell).strip()
    if not text:
        return []
    options = KNOWN_OPTIONS[question]
    found: set[str] = set()
    # Longest-first matching avoids matching "PET" inside "PET (Cambridge)"
    # and keeps comma-containing options (Q31) whole.
    candidates = sorted(options, key=len, reverse=True)
    for option in candidates:
        if option == PET_CANONICAL:
            if any(alias in text for alias in PET_ALIASES):
                # "PET (Cambridge)" itself contains "PET"; covered above.
                found.add(option)
        elif option in text:
            found.add(option)
    # Unknown fragments are ignored here (they are not part of known options);
    # raw cell is always preserved by callers.
    return [option for option in options if option in found]


def frequency(rows: list[dict], column: str) -> list[dict]:
    counts = Counter((row.get(column) or "").strip() for row in rows)
    counts.pop("", None)
    denominator = sum(counts.values())
    return [
        {
            "option": option,
            "count": count,
            "percent": round(count * 100 / denominator, 1) if denominator else 0.0,
            "denominator": denominator,
        }
        for option, count in counts.most_common()
    ]


def multi_frequency(rows: list[dict], column: str, question: str) -> list[dict]:
    per_row = [parse_multi(row.get(column), question) for row in rows]
    answered = [opts for opts in per_row if opts]
    denominator = len(answered)
    counter: Counter[str] = Counter()
    for opts in per_row:
        counter.update(opts)
    return [
        {
            "option": option,
            "count": counter.get(option, 0),
            "percent": (
                round(counter.get(option, 0) * 100 / denominator, 1) if denominator else 0.0
            ),
            "denominator": denominator,
        }
        for option in KNOWN_OPTIONS[question]
        if counter.get(option, 0) > 0
    ]


def numeric_summary(rows: list[dict], column: str) -> dict:
    values: list[float] = []
    for row in rows:
        cell = (row.get(column) or "").strip()
        if cell:
            values.append(float(cell))
    levels = [Counter(values).get(float(level), 0) for level in (1, 2, 3, 4, 5)]
    return {
        "n": len(values),
        "levels": levels,  # counts for 1..5
        "mean": round(statistics.mean(values), 2) if values else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "sd": round(statistics.pstdev(values), 2) if len(values) > 1 else 0.0,
        "share_4_5": (round(sum(levels[3:]) * 100 / len(values), 1) if values else 0.0),
    }


GROUPS = {
    "Yếu tố cá nhân (11–13)": [
        "Yếu tố cá nhân [11. Mục tiêu nghề nghiệp]",
        "Yếu tố cá nhân [12. Nhu cầu sử dụng tiếng Anh]",
        "Yếu tố cá nhân [13. Sự phù hợp của bài thi với trình độ tiếng Anh của bạn]",
    ],
    "Đặc điểm của chứng chỉ (14–17)": [
        "Đặc điểm của chứng chỉ [14. Độ khó của bài thi]",
        "Đặc điểm của chứng chỉ [15. Các kỹ năng và dạng câu hỏi trong bài thi]",
        "Đặc điểm của chứng chỉ [16. Thời lượng bài thi và lịch thi]",
        "Đặc điểm của chứng chỉ [17. Khả năng đạt điểm mong muốn]",
    ],
    "Chi phí (18–20)": [
        "Chi phí [18. Lệ phí thi]",
        "Chi phí [19. Chi phí luyện thi]",
        "Chi phí [20. Khả năng tài chính của bản thân hoặc gia đình]",
    ],
    "Ý kiến/thông tin từ người khác (21–24)": [
        "Ý kiến và thông tin từ người khác [21. Sự giới thiệu của bạn bè]",
        "Ý kiến và thông tin từ người khác [22. Ý kiến của giảng viên]",
        "Ý kiến và thông tin từ người khác [23. Thông tin trên mạng xã hội]",
        "Ý kiến và thông tin từ người khác [24. Tư vấn từ trung tâm ngoại ngữ]",
    ],
    "Yếu tố từ nhà trường (25–27)": [
        "Yếu tố từ nhà trường [25. Yêu cầu chuẩn đầu ra tiếng Anh]",
        "Yếu tố từ nhà trường [26. Thông tin và tư vấn từ nhà trường]",
        "Yếu tố từ nhà trường [27. Việc chứng chỉ được nhà trường công nhận]",
    ],
}
