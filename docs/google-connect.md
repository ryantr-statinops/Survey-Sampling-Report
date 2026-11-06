# Kết nối Google Sheets → Google Slides (VisuaSlide SDK)

> Trạng thái: **Implemented** (offline/consuming SDK + local charts/Excel/report),
> **Open** (live Google sandbox chưa chạy — chưa có `client_secret.json`/OAuth trên máy này).
> Hướng dẫn dưới đây để bạn (owner) tự kết nối lần đầu; agent không thể thay bạn đăng nhập Google.

Tài liệu liên quan: [plan/SDK_USAGE.md](../plan/SDK_USAGE.md), [plan/PLAN.md](../plan/PLAN.md) §6,
SDK consumer docs: `_VisuaSlide_ref/docs/collaborating-and-consuming.md` (nếu có clone ref).

## 0. Nguyên tắc (đã chốt với owner)

- 1 nguồn duy nhất: spreadsheet `14Ic0Zl7V5fr5dOkdo7ae5pwZpzk8v3HPGKliDHEQTiw`, tab `gid=1653201454`, range **A:AG**
  (cột **email AH bị loại từ đầu** — app/SDK không đọc).
- Reporting spreadsheet + Slides là **output do app quản lý**, không phải nguồn thứ hai.
- Không commit `*.local.toml`, `client_secret*.json`, token, snapshot/raw chứa dữ liệu thật.
- Manual refresh trước, scheduling (Task Scheduler) chỉ sau khi sandbox pass.

## 1. Chạy offline trước (không cần Google) — đã verify

```powershell
uv sync --locked --group dev
uv run --locked pytest -q
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
```

Tạo lại báo cáo/charts/Excel từ CSV public (ghi chú: CSV thô **không** commit):

```powershell
# tải CSV từ tab (đúng cột A:AG, email bị loại ở consumer)
Invoke-WebRequest -Uri 'https://docs.google.com/spreadsheets/d/14Ic0Zl7V5fr5dOkdo7ae5pwZpzk8v3HPGKliDHEQTiw/export?format=csv&gid=1653201454' -OutFile $env:TEMP\survey.csv
uv run --locked survey-report generate --csv $env:TEMP\survey.csv --out report --date 2026-11-06
```

Output: `report/report.md`, `report/stats.xlsx`, `report/charts/*.png` (16 file),
`report/summary.json`. Đây là deliverable đọc độc lập + chèn Slides thủ công được ngay.

SDK dry-run synthetic (Core pipeline, không publish):

```powershell
Copy-Item config/survey.english_certs.example.toml config/survey.english_certs.local.toml
# sửa project_dir = "../.visuaslide/english-certs-<ten-cua-ban>" nếu nhiều dev
uv run --locked visuaslide refresh --config config/survey.english_certs.local.toml --fixture-json tests/fixtures/synthetic_responses.json --dry-run
```

## 2. Tạo Google Cloud project + OAuth (làm 1 lần, làm tay)

1. Vào [Google Cloud Console](https://console.cloud.google.com/) → tạo project (vd. `survey-report`).
2. **APIs & Services → Enable APIs**: `Google Sheets API`, `Google Slides API`, `Google Drive API`.
3. **APIs & Services → OAuth consent screen**: User type **Desktop app**.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID** (Desktop app) → tải `client_secret.json`
   về máy, để ngoài repo: `C:\private\client_secret.json`

## 3. Auth + bootstrap (làm tay, mở browser 1 lần)

```powershell
Copy-Item config/survey.english_certs.example.toml config/survey.english_certs.local.toml
# kiểm tra: spreadsheet_id, sheet_id = 1653201454, column_range = "A:AG", project_dir riêng
uv sync --locked --group dev
uv run --locked visuaslide auth --config config/survey.english_certs.local.toml --client-secret C:\private\client_secret.json
# browser mở -> chọn đúng tài khoản Google -> Allow (scopes: spreadsheets.readonly + drive.file)
# token lưu ở <project_dir>/oauth/token.json (gitignored)
uv run --locked visuaslide bootstrap-outputs --config config/survey.english_certs.local.toml
# tạo/reuse reporting spreadsheet + Slides template + presentation; mapping -> <project_dir>/google_outputs.json
```

> Nhắc: `refresh`/`resume` **không** mở browser. Testing-mode token có thể hết hạn ~7 ngày → chạy lại `auth` khi hết hạn.

## 4. Refresh + review (manual trước)

```powershell
uv run --locked visuaslide refresh --config config/survey.english_certs.local.toml --dry-run
uv run --locked visuaslide refresh --config config/survey.english_certs.local.toml
uv run --locked visuaslide review-layout --config config/survey.english_certs.local.toml
```

- Dry-run: đọc toàn bộ tab A:AG, validate, snapshot + analysis, **không publish**.
- Refresh thật: đọc lại toàn bộ bảng (thêm/sửa/xóa đều 반영) → ghi bảng tổng hợp + linked Sheets charts + text/tables qua Slides API.
  Sheets/Slides không phải 1 transaction → partial failure hiện trong run manifest; **không báo success khi chỉ update một phần** → dùng `resume` thay vì chạy mới.
- `review-layout`: tải thumbnail từng slide — check tiếng Việt, label dài, chart order/màu, table overflow, Q3 có 13 khoa dễ chật/cắt nhãn (PLAN §10 Risk).

## 5. Sandbox check chuẩn (synthetic, trước khi dùng dữ liệu thật)

```powershell
$env:VISUASLIDE_SANDBOX_CONFIG = "config/survey.english_certs.local.toml"
uv run --locked pytest tests/sandbox -q   # thiếu biến = skipped; cần Sheets synthetic riêng
```

Gate: add → refresh → đối chiếu 3 nơi (source rows, workbook, Slides + thumbnail). Kết quả ghi private, không commit responses/screenshots.

## 6. Cách nhanh đưa lên Slides hôm nay (không cần OAuth SDK)

Nếu bạn muốn nộp ngay: dùng `report/` đã sinh — upload `report/charts/*.png` lên Google Drive →
chèn ảnh vào Google Slides (Insert → Image), paste bảng từ `report/report.md` / `report/stats.xlsx`,
chèn tiêu đề/kết luận từ `report.md`. Đây là đường độc lập (Issue §4: ảnh riêng dùng trong thuyết trình)
và không thay thế refresh SDK tự động ở mục 3–5.

## 7. Recovery

```powershell
uv run --locked visuaslide inspect-run --config config/survey.english_certs.local.toml --run-id <run-id>
uv run --locked visuaslide resume --config config/survey.english_certs.local.toml --run-id <run-id>
uv run --locked visuaslide validate --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
uv run --locked visuaslide analyze --config config/survey.english_certs.local.toml --snapshot-id <snapshot-id>
```

- Token hết hạn: chạy lại `auth` (mục 3).
- Refresh tạo file trùng: giữ nguyên `project_dir` + `google_outputs.json`; dùng `resume`, don't xoá registry.
- Label bị cắt: fix ở config/template + `review-layout`, đừng sửa tay từng slide lẻ (refresh sẽ ghi đè vùng SDK-managed).
