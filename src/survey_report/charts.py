"""16 charts (9 pie, 5 bar, 100% stacked, mean comparison) -> PNG 300dpi.

Font: DejaVu Sans supports Vietnamese diacritics. White background,
no clipped labels (tight bbox), stable option order from logic.KNOWN_OPTIONS.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from survey_report.logic import (  # noqa: E402
    GROUPS,
    frequency,
    multi_frequency,
    numeric_summary,
)

plt.rcParams["font.family"] = "DejaVu Sans"

SINGLE = [
    ("Câu 1. Giới tính của bạn là gì?", "q01_gioi_tinh"),
    ("Câu 2. Bạn đang là sinh viên năm mấy?", "q02_nam_hoc"),
    ("Câu 3. Bạn đang học khoa nào?", "q03_khoa"),
    ("Câu 4. Bạn đánh giá trình độ tiếng Anh của mình ở mức nào?", "q04_trinh_do"),
    ("Câu 5. Bạn đã từng ôn thi hoặc thi chứng chỉ tiếng Anh chưa?", "q05_kinh_nghiem"),
    ("Câu 7. Bạn dự định thi chứng chỉ nào trong thời gian tới?", "q07_du_dinh"),
    ("Câu 9. Bạn dự định thi chứng chỉ khi nào?", "q09_thoi_gian"),
    ("Câu 28. Chứng chỉ bạn đã chọn hoặc dự định thi phù hợp với bạn ở mức nào?", "q28_phu_hop"),
    ("Câu 29. Bạn có muốn giới thiệu chứng chỉ này cho sinh viên khác không?", "q29_gioi_thieu"),
]
MULTI = [
    (
        "Câu 6. Bạn đã từng thi chứng chỉ tiếng Anh nào? (Có thể chọn nhiều đáp án)",
        "Q6",
        "q06_da_thi",
    ),
    (
        "Câu 8. Bạn muốn thi chứng chỉ tiếng Anh để làm gì? (Có thể chọn nhiều đáp án)",
        "Q8",
        "q08_muc_dich",
    ),
    (
        "Câu 10. Bạn tìm thông tin về chứng chỉ từ đâu? (Có thể chọn nhiều đáp án)",
        "Q10",
        "q10_nguon_tin",
    ),
    (
        "Câu 30. Bạn gặp khó khăn gì khi chọn chứng chỉ? (Có thể chọn nhiều đáp án)",
        "Q30",
        "q30_kho_khan",
    ),
    (
        "Câu 31. Bạn muốn nhà trường cung cấp thông tin gì? (Có thể chọn nhiều đáp án)",
        "Q31",
        "q31_mong_muon",
    ),
]
Q11_27 = sum(GROUPS.values(), [])


def _pie(rows, column, title, path: Path) -> None:
    freq = frequency(rows, column)
    labels = [f"{f['option']} ({f['count']}, {f['percent']}%)" for f in freq]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie([f["count"] for f in freq], labels=labels, autopct="", startangle=90)
    ax.set_title(title, fontsize=13)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _bar(rows, column, qid, title, path: Path) -> None:
    freq = multi_frequency(rows, column, qid)
    fig, ax = plt.subplots(figsize=(10, 6))
    options = [f["option"] for f in freq]
    percents = [f["percent"] for f in freq]
    ax.barh(options, percents)
    ax.set_xlabel(f"Tỷ lệ (%) — mẫu số n={freq[0]['denominator'] if freq else 0}")
    ax.set_title(title, fontsize=13)
    for i, (f, p) in enumerate(zip(freq, percents, strict=False)):
        ax.text(p + 0.5, i, f"{f['count']} ({p}%)", va="center", fontsize=9)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_charts(rows: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for column, slug in SINGLE:
        p = out_dir / f"{slug}.png"
        _pie(rows, column, column, p)
        paths.append(p)
    for column, qid, slug in MULTI:
        p = out_dir / f"{slug}.png"
        _bar(rows, column, qid, column, p)
        paths.append(p)
    # 100% stacked distribution Q11-27
    p = out_dir / "q11_q27_100pct.png"
    fig, ax = plt.subplots(figsize=(12, 8))
    labels = [c.split("[", 1)[1].rsplit("]", 1)[0] for c in Q11_27]
    left = [0.0] * len(Q11_27)
    colors = ["#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#2980b9"]
    for level in range(5):
        vals = []
        for col in Q11_27:
            s = numeric_summary(rows, col)
            vals.append(s["levels"][level] * 100 / s["n"] if s["n"] else 0)
        ax.barh(labels, vals, left=left, label=f"Điểm {level + 1}", color=colors[level])
        left = [a + v for a, v in zip(left, vals, strict=False)]
    ax.set_xlabel("Tỷ lệ (%)")
    ax.set_title("Phân bố điểm 1–5 các yếu tố Q11–Q27 (100% stacked)")
    ax.legend()
    fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    paths.append(p)
    # Mean comparison
    p = out_dir / "q11_q27_mean.png"
    means = [numeric_summary(rows, c)["mean"] for c in Q11_27]
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(labels, means)
    ax.set_xlabel("Điểm trung bình (thang 1–5)")
    ax.set_xlim(1, 5)
    ax.set_title("Điểm trung bình 17 yếu tố Q11–Q27")
    fig.savefig(p, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    paths.append(p)
    return paths
