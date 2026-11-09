# SDK Usage Guide — VisuaSlide trong Survey-Sampling-Report

> **Trạng thái:** *Accepted* cho cách tích hợp (dependency, không copy SDK); *Open* cho phần Google live acceptance — chưa qua sandbox nên mọi lệnh Google phải dùng synthetic data trước.
> **SDk nguồn:** [VisuaSlide](https://github.com/ryantr-statinops/VisuaSlide) — **chưa publish lên PyPI**, phải dùng dạng Git dependency.
> **Tài liệu mẹ:** [plan/PLAN.md](PLAN.md) (spec nghiệp vụ 32 câu) · [README.md](../README.md) (tổng quan repo)

## 1. Nguyên tắc tích hợp (tóm tắt)

- **Không clone/copy SDK vào repo này.** `Survey-Sampling-Report` chỉ khai VisuaSlide là dependency trong `pyproject.toml` / `uv.lock`. Thư mục `_VisuaSlide_ref/` đã git-ignore, chỉ để đọc, không commit.
- **1 repo consumer = 1 TOML + 1 `project_dir` riêng** (`.visuaslide/<tên-dev>/`). Token, snapshot, `google_outputs.json` nằm chung trong `project_dir`, không chia sẻ.
- **1 nguồn duy nhất:** đúng 1 tab `spreadsheet_id` + `sheet_id` (gid). App chỉ đọc nguồn; reporting spreadsheet + Slides là file app-managed (output), không phải nguồn thứ hai.
- **Config là TOML**, không phải `.env`. VisuaSlide không tự load `.env`; biến môi trường chỉ dùng cho sandbox test (`VISUASLIDE_SANDBOX_CONFIG`).
- **Python 3.12 + `uv` bắt buộc** (`requires-python = ">=3.12,<3.13"`). Mọi lệnh dùng `uv run --locked ...` để tôn trọng lockfile.

## 2. Chuẩn bị môi trường

**Yêu cầu máy dev:**
- CPython 3.12 (`uv python install 3.12`)
- `uv` mới nhất (`uv --version`)
- Tài khoản Google để tạo sandbox (chỉ khi tới Phase 3)
- Git + PowerShell (repo này đang dùng Windows; lệnh dưới dùng PowerShell)

**Kiểm tra nhanh:**
```powershell
uv python --version
uv --version
```

## 3. Cài SDK vào repo này (chỉ làm 1 lần)

> Đây là cách *consume* SDK từ VisuaSlide `docs/collaborating-and-consuming.md`. Người đóng góp ngược lại SDK thì fork VisuaSlide — không phải scope repo này.

**Bước 1 — Gắn Git dependency và chốt revision:**

```powershell
uv add git+https://github.com/ryantr-statinops/VisuaSlide.git --rev <FULL_COMMIT_SHA>
uv lock
```
- Thay `<FULL_COMMIT_SHA>` bằng hash đầy đủ đã review trên `origin/main` của VisuaSlide (xem HEAD hiện tại bằng `git ls-remote https://github.com/ryantr-statinops/VisuaSlide.git HEAD`).
- `uv add` sẽ ghi vào `pyproject.toml` + `uv.lock`. **Commit cả 2 file** ở 1 commit riêng (`chore: add VisuaSlide as git dependency`) để dev khác tái hiện được.
- Cập nhật SDK = đổi `--rev` một cách chủ ý, không để track branch động.

**Bước 2 — Cài môi trường:**

```powershell
uv sync --locked --group dev
```

**Kiểm tra cài đúng:**
```powershell
uv run --locked python -c "from visuaslide import SurveyProject; print('sdk ok')"
```

**`.gitignore` đã có sẵn trong repo này** (không cần thêm):
```
.visuaslide/
*.local.toml
google_outputs.json
client_secret*.json
token.json
*.parquet
```
Không bao giờ commit TOML local, token, snapshot chứa dữ liệu thật, screenshot private.

## 4. Tạo config TOML cho khảo sát chứng chỉ tiếng Anh

**Bước 3 — Copy khuôn và đặt `project_dir` riêng:**

```powershell
New-Item -ItemType Directory -Force -Path config | Out-Null
Copy-Item _VisuaSlide_ref/examples/survey.example.toml config/survey.english_certs.example.toml
Copy-Item config/survey.english_certs.example.toml config/survey.english_certs.local.toml
```
- File `*.example.toml` **có commit** (public, không chứa token/ID riêng tư ngoài sheet public).
- File `*.local.toml` **không commit** (đã ignore). Mỗi dev tự tạo 1 bản local.

**Bước 4 — Sửa `config/survey.english_certs.local.toml` theo 3 khối:**

```toml
project_dir = "../.visuaslide/english-certs"

[source]
spreadsheet_id = "14Ic0Zl7V5fr5dOkdo7ae5pwZpzk8v3HPGKliDHEQTiw"
sheet_id = 1653201454
header_row = 1
column_range = "A:BG"  # bao hết Dấu thời gian đến Địa chỉ email

[schema]
# 32 biến: xem plan/PLAN.md §3 — categorical cho single/multi, numeric 1-5 cho Q11-27, text cho Q32
# Q31 giữ nguyên "So sánh IELTS, TOEIC và APTIS", Q6 gộp PET variants, loại cột email khỏi schema public
```

- Khuôn chi tiết xem `_VisuaSlide_ref/examples/survey.example.toml` (variables → `{ name, source_header, kind, required?, categories? }`).
- `[analysis]` khai specifications (frequency cho Q1-5/7/9/28-29, frequency multi cho Q6/8/10/30/31, numeric_summary cho Q11-27, crosstab nếu cần).
- `[report]` giữ `title`, `locale = "vi-VN"`, `display_timezone = "Asia/Ho_Chi_Minh"`, `research_question`, `sampling_method`, `collection_period`, `conclusion` — copy format từ `survey.example.toml`.

**Quy tắc:**
- `project_dir` là relative so với folder chứa TOML. Mỗi dev dùng 1 tên khác nhau (`../.visuaslide/english-certs-<tên-dev>`) để token/snapshot/mapping không chồng.
- Không bỏ OAuth JSON/token vào TOML. Chỉ truyền `client_secret.json` qua flag `--client-secret` khi chạy `auth`.

## 5. Phase 1 — Chạy offline (không cần Google) *(Accepted)*

Dùng synthetic fixture để verify trước; không cần tài khoản Google.

```powershell
# Offline SDK example (in-memory)
uv run --locked python _VisuaSlide_ref/examples/offline_workflow.py --config config/survey.english_certs.local.toml
# Note: offline_workflow.py hiện đọc fixture trong VisuaSlide; khi đã cài SDK thì chạy test fixture tương đương.

# CLI dry-run — chỉ snapshot + validate + prepare + analyze, không publish
uv run --locked visuaslide refresh --config config/survey.english_certs.local.toml --fixture-json tests/fixtures/synthetic_responses.json --dry-run

# Validate / analyze / inspect artifacts đã lưu (không đọc Google)
uv run --locked visuaslide validate --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
uv run --locked visuaslide analyze --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
uv run --locked visuaslide inspect-run --config config/survey.english_certs.local.toml --run-id <run-id>
```

**Python API tương đương:**
```python
from visuaslide import SurveyProject
project = SurveyProject.from_toml("config/survey.english_certs.local.toml")
run = project.refresh(dry_run=True)
print(run.run_id, run.status)
# status READY = qua validate + analyze, chưa publish
```

**Gate P1:** run `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run pytest tests`, `uv build --wheel` trong VisuaSlide phải pass; số liệu offline khi sửa fixture phải khớp tính tay trên fixture nhỏ.

## 6. Phase 2 — Google sandbox (live, opt-in) *(Open)*

> **Chỉ với synthetic Sheets**, không dùng dữ liệu thật cho tới khi gate này pass. Kiểm chứng theo `docs/google-setup-and-recovery.md` của VisuaSlide.

**Bước 5 — Chuẩn bị Google Cloud (1 lần):**
1. Tạo Google Cloud project → enable **Sheets API, Slides API, Drive API**.
2. Tạo OAuth consent screen → **Desktop app** client → download `client_secret.json` về máy (không commit).
3. Tạo Sheets synthetic **riêng** (header khớp `survey.english_certs.example.toml`), ghi `spreadsheet_id` + `gid`.

**Bước 6 — Auth + bootstrap:**

```powershell
uv run --locked visuaslide auth --config config/survey.english_certs.local.toml --client-secret C:\private\client_secret.json
# Auth là lệnh duy nhất mở browser. Token lưu ở <project_dir>/oauth/token.json (ignored).

uv run --locked visuaslide bootstrap-outputs --config config/survey.english_certs.local.toml
# Tạo hoặc reuse: reporting spreadsheet + Slides template + presentation riêng.
# Mapping lưu ở <project_dir>/google_outputs.json — đừng xoá khi recovery.
```

**Bước 7 — Dry-run → Publish → Review:**

Dự án cung cấp `survey-report-publish` làm consumer entrypoint để giữ tương thích bố cục Q3 (13 khoa) và Google Sheets bar chart. Dùng entrypoint này cho refresh/resume bên dưới.

```powershell
uv run --locked survey-report-publish --config config/survey.english_certs.local.toml --dry-run
uv run --locked survey-report-publish --config config/survey.english_certs.local.toml
uv run --locked visuaslide review-layout --config config/survey.english_certs.local.toml
```
- Dry-run đọc toàn bộ tab, validate, lưu snapshot + analysis, **không publish**.
- Refresh thật đọc lại toàn bộ bảng (thêm/sửa/xóa đều 반영) → ghi bảng tổng hợp + linked Sheets charts + text/tables qua Slides API. Sheets và Slides không phải 1 transaction → partial failure phải hiện trong `run manifest`.
- `review-layout` tải thumbnail từng slide — check tiếng Việt, label dài, chart order/màu, table overflow trước khi coi là xong.

**Bước 8 — Sandbox test chuẩn gate:**

```powershell
$env:VISUASLIDE_SANDBOX_CONFIG = "config/survey.english_certs.local.toml"
uv run --locked pytest tests/sandbox -q
```
- Chỉ chạy khi set biến môi trường; thiếu biến = skipped. Test add → refresh → đối chiếu 3 nơi (source rows, workbook, Slides + thumbnail). Kết quả ghi private, không commit responses/screenshots.

## 7. Recovery và vận hành

```powershell
# Xem trạng thái run
uv run --locked visuaslide inspect-run --config config/survey.english_certs.local.toml --run-id <run-id>

# Resume run dở (dùng analysis đã lưu, bỏ qua checkpoint đã xong, không đọc lại source)
uv run --locked survey-report-publish --config config/survey.english_certs.local.toml --resume-run-id <run-id>

# Replay snapshot cũ không cần Google
uv run --locked visuaslide validate --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
uv run --locked visuaslide analyze  --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
```

- Nếu token hết hạn (Testing-mode refresh token có thể hết sau 7 ngày) → chạy lại `auth` tương tác. `refresh`/`resume` **không** mở browser.
- Chống overlapping refresh: `ProjectLock` theo `project_dir` — chạy 1 lần tại 1 thời điểm.
- Scheduling (Windows Task Scheduler) **chỉ bật sau khi gate sandbox pass**; cloud scheduling cần quyết định auth/storage riêng (*Open*).

## 8. Liên hệ với plan nghiệp vụ (`plan/PLAN.md`)

| Giai đoạn SDK | Nhiệm vụ trong repo này | Gate |
|---|---|---|
| Offline (Phase 4 trong VisuaSlide, C01–C38) | TOML cho 32 câu, snapshot → pandas → Parquet → DuckDB | Synthetic pass, số liệu đối chiếu được |
| Reporting | Reporting spreadsheet + 16 charts PNG + Excel workbook | Stock label không cắt, % kèm mẫu số |
| Publishing (C39–C53) | `bootstrap-outputs` + Slides refresh | Sandbox add/edit/delete pass, không duplicate |
| Scheduling | Task Scheduler / Actions (sau) | Token lifecycle đã verified |

## 9. Checklist cho dev mới clone repo này

- [ ] `git clone https://github.com/ryantr-statinops/Survey-Sampling-Report.git`
- [ ] Đọc `README.md` → `plan/PLAN.md` → file này
- [ ] `uv sync --locked --group dev` (sau khi `pyproject.toml` + `uv.lock` đã được commit)
- [ ] Copy `config/survey.english_certs.example.toml` → `config/survey.english_certs.local.toml`, đặt `project_dir` riêng, sửa `spreadsheet_id`/`sheet_id` nếu dùng sandbox
- [ ] Chạy Phase 1 offline dry-run, gửi `run_id` để team review
- [ ] Chỉ qua Phase 2 khi được giao sandbox synthetic và đã có `client_secret.json` local

## 10. Xử lý lỗi thường gặp

| Triệu chứng | Nguyên nhân hay gặp | Fix |
|---|---|---|
| `ConfigurationError` khi load TOML | Sai header, trùng header, thiếu tab, `sheet_id` sai | Đối chiếu header row 1 với Sheet, copy lại từ `example.toml` |
| Validation fail, không có clean dataset | Unknown category, invalid value 1–5, empty input | Xem validation report trong `project_dir`, chỉ fix ở fixture/config, giữ raw snapshot |
| Auth báo thiếu scope | Consent chưa bật Sheets/Slides/Drive | Bật 3 APIs trong Google Cloud Console, chạy lại `auth` |
| Refresh tạo file trùng | `google_outputs.json` bị xoá hoặc `project_dir` khác nhau | Giữ nguyên `project_dir` + registry; dùng `resume` thay vì start mới |
| Label chart bị cắt | Tiếng Việt dài + font Slides | Tăng size/lọc label ở `review-layout`, không chỉ sửa Slides lẻ |

> Mọi log phải không chứa response payload/credential. Mọi lệnh live phải tách khỏi CI mặc định.
