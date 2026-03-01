# Copilot 指令檔：連結檢查工具 (Link Checker)

## 專案摘要
建立一個以 Python 為核心的 CLI 工具 `link_checker.py`，輸入目標 URL 後自動擷取該頁面上的所有連結（含靜態與 JavaScript 動態渲染產生的連結），以非同步並發方式檢查每個連結之 HTTP 回應，最終輸出 UTF-8 編碼的 CSV 報表並記錄結構化日誌。

## 主要技術（在本次計劃中新增）
- 語言：Python 3.9+
- 非同步：`asyncio`, `aiohttp`
- 瀏覽器模擬：`playwright`（啟用動態檢測時使用）
- 日誌：Python `logging`（建議採用結構化 JSON 輸出）
- 測試：`pytest`

## 核心原則（必須遵守）
- 穩定性：所有網路請求需有 timeout 與重試（最多 3 次，指數退避），並支援優雅關閉（graceful shutdown）。
- 詳細日誌：採用分級（DEBUG/INFO/WARNING/ERROR/CRITICAL）且結構化的日誌，記錄時戳、URL、狀態碼、耗時與完整錯誤堆疊。
- 非同步優先：核心檢查引擎應以 `asyncio` + `aiohttp` 設計以提升吞吐量。

## 快速安裝與執行（開發者指令）
1. 建立與啟動虛擬環境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
```

2. 安裝相依套件：

```bash
pip install -r requirements.txt
# 若使用 Playwright 模式，需執行一次瀏覽器安裝：
playwright install
```

3. 範例執行：

```bash
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv --concurrency 10 --timeout 10
```

## CLI 參數範例
- `--url` (required) 目標頁面 URL
- `--concurrency` (optional) 並發數（預設 10）
- `--timeout` (optional) 單次請求超時秒數（預設 10）
- `--max-retries` (optional) 最大重試次數（預設 3）
- `--use-playwright` (optional) 是否啟用 Playwright（動態模式，預設 false）
- `--report-type` (optional) `all` 或 `failures`（預設 `all`）
- `--output` (optional) CSV 輸出路徑（預設 `report.csv`）

## 日誌 & 報表規範
- 日誌格式建議為 JSON 結構，並包含 `timestamp`, `level`, `page_url`, `link`, `status_code`, `elapsed_ms`, `error`。
- CSV 欄位：`page_url, raw_href, absolute_url, status_code, elapsed_ms, error`，使用 UTF-8 編碼。

## 開發與 PR 檢查清單（必做）
- 所有公開函式加上繁體中文 docstring，包含參數、回傳與可能拋出的例外。
- 使用 type hints，並通過靜態檢查（如 ruff/mypy 或團隊工具）。
- 包含非同步單元測試覆蓋關鍵錯誤路徑（目標覆蓋率 ≥ 80%）。
- 請確認：
  - 每個 HTTP 請求有 timeout
  - 重試邏輯正確實作（指數退避）
  - 異常與堆疊資訊被日誌化
  - 支援優雅關閉（例如接收到 SIGINT/SIGTERM 時等待進行中任務完成或取消）

## 快速參考：重要檔案
- 規格：`specs/1-link-check/spec.md`
- 計劃：`specs/1-link-check/plan.md`
- 研究：`specs/1-link-check/research.md`
- 資料模型：`specs/1-link-check/data-model.md`
- 快速上手：`specs/1-link-check/quickstart.md`

## 注意事項
- Playwright 初次啟動需下載瀏覽器二進位檔，測試時請預留時間。
- 若目標網站有嚴格的 rate-limit 或反爬策略，請先取得授權或降低速率。

---
**自動生成於**：2026-03-01
