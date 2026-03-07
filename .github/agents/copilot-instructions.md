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

---

## 最新技術堆疊更新（002-realtime-progress 分支）

### 即時進度可視化技術
**Branch**: 002-realtime-progress  
**Added**: 2026-03-07

#### 新增技術組件
- **ANSI 終端控制**: 使用 `\r` (carriage return) 和 `\033[K` (清除行尾) 實現單行進度覆寫
- **事件驅動進度更新**: 基於 `asyncio` 的定時任務，預設 1 秒更新間隔
- **進度狀態管理**: `ProgressState` 類別（使用 `asyncio.Lock` 確保線程安全）
- **進度渲染器**: `ProgressRenderer` 類別（純函數式渲染邏輯）
- **動態百分比計算**: `checked_links / discovered_links`（實時調整）
- **線性 ETA 估算**: `(總耗時 / 已檢查數) × 剩餘數量`

#### 新增 CLI 參數
```bash
--progress              # 啟用/禁用進度顯示（預設：true）
--progress-interval     # 更新間隔秒數（預設：1.0）
--progress-bar-width    # 進度條寬度（預設：20）
--max-failures-display  # 最大失效連結顯示數（預設：50）
--no-ansi               # 禁用 ANSI 跳脫序列（降級為追加新行）
--show-current-url      # 顯示當前檢查的 URL（預設：true）
--show-eta              # 顯示預估剩餘時間（預設：true）
```

#### 進度顯示格式示例
```
[=========>          ] 45% | 已檢查: 450/1000 | 失效: 12 | 用時: 02:15 | 剩餘: ~03:00
```

失效連結通知（追加新行）：
```
❌ 失效連結: https://example.com/broken (HTTP 404)
⏱ 失效連結: https://example.com/timeout (連線逾時)
```

最終摘要：
```
檢查完成！
----------
總耗時: 05:30
總連結數: 1000
有效連結: 988
失效連結: 12
----------
```

#### 核心資料結構

**ProgressState**（src/lib/progress.py）：
- `discovered_pages`, `processed_pages`: 頁面數統計
- `discovered_links`, `checked_links`: 連結數統計
- `failed_links`: 失效連結計數
- `current_page_url`, `current_link_url`: 當前檢查 URL
- `failed_link_details: List[FailedLinkDetail]`: 失效連結清單
- `to_snapshot() -> ProgressSnapshot`: 不可變快照生成

**ProgressSnapshot**（不可變）：
- 所有統計數據 + `progress_percentage` + `elapsed_seconds` + `estimated_remaining_seconds`

**ProgressRenderer**：
- `render_progress_line(snapshot) -> str`: 生成進度條字符串
- `render_failed_link_notification(detail) -> str`: 格式化失效通知
- `render_final_summary(snapshot) -> str`: 最終摘要
- `_detect_ansi_support() -> bool`: 終端能力檢測

#### 效能約束
- 進度更新延遲 ≤ 1 秒（FR-017）
- 進度顯示開銷 ≤ 5% 總執行時間（SC-013）
- 統計準確性 100%（SC-009）
- ETA 誤差 ≤ 30%（SC-012）

#### 憲法合規性
- **穩定性**：進度顯示失敗時降級為追加新行模式，不影響核心檢查功能；支援 Ctrl+C 中斷並保留部分結果
- **詳細日誌**：進度輸出使用 `stdout`，日誌輸出使用 `stderr` 或文件，完全分離
- **非同步優先**：進度更新使用 `asyncio.create_task()`，不阻塞主檢查邏輯

#### 快速參考（新增規格文檔）
- 規格：`specs/002-realtime-progress/spec.md`
- 計劃：`specs/002-realtime-progress/plan.md`
- 研究：`specs/002-realtime-progress/research.md`
- 資料模型：`specs/002-realtime-progress/data-model.md`
- CLI 合約：`specs/002-realtime-progress/contracts/cli.md`
- 快速上手：`specs/002-realtime-progress/quickstart.md`

---
**最後更新**：2026-03-07（002-realtime-progress 分支）
