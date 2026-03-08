# Contracts: CLI 接口定義

## 介面：命令列啟動

範例：

```bash
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --concurrency 10 --timeout 10 --max-retries 3 --use-playwright true --report-type all --output reports/report.xlsx
```

參數說明：
- `--url` (required): 目標頁面 URL
- `--concurrency` (optional): 並發連線數，預設 10
- `--timeout` (optional): 單次請求 timeout（秒），預設 10
- `--max-retries` (optional): 最大重試次數，預設 3
- `--use-playwright` (optional): 是否啟用 Playwright 模式以擷取動態連結，預設 false
- `--report-type` (optional): `all` 或 `failures`，預設 `all`
- `--output` (optional): 報表輸出路徑，預設 `report.xlsx`（若給 `.csv` 也會自動轉成 `.xlsx`）
- `--max-links` (optional): 限制檢查連結數（測試用途）
- `--progress` / `--no-progress` (optional): 是否啟用即時進度顯示，預設啟用
- `--progress-interval` (optional): 進度更新間隔（秒），預設 `1.0`
- `--progress-bar-width` (optional): 進度條寬度，範圍 `10-50`，預設 `20`
- `--max-failures-display` (optional): 即時顯示失效連結上限，範圍 `0-1000`，預設 `50`
- `--no-ansi` (optional): 停用 ANSI 單行覆寫模式
- `--show-current-url` / `--no-show-current-url` (optional): 是否顯示目前檢查 URL，預設顯示
- `--show-eta` / `--no-show-eta` (optional): 是否顯示預估剩餘時間，預設顯示
- `--compact-mode-threshold` (optional): 連結數達門檻時切換精簡顯示，預設 `50`

## 輸出 Excel 欄位（固定 11 欄）
- `Scan Time`
- `Page Title`
- `Breadcrumb`
- `Page URL`
- `Link Text`
- `Link URL`
- `HTTP Status`
- `Result`
- `Response Time`
- `Source`
- `Depth`

規則：
- `Page URL` 欄位一律輸出實際值（即使與 `Link URL` 相同也不省略）。
- `Result` 欄位：HTTP 2xx 為 `OK`，其餘為 `Broken`。

## JSON 範例（若需要機器介面）

```json
{
  "scan_time": "2026-03-08 13:06",
  "page_title": "Example Domains",
  "breadcrumb": "help > example-domains",
  "page_url": "http://www.iana.org/help/example-domains",
  "link_text": "Learn more",
  "link_url": "https://iana.org/domains/example",
  "http_status": 200,
  "result": "OK",
  "response_time": 1521,
  "source": "Example Domain",
  "depth": 2
}
```

**Contracts 完成**: 2026-03-01
