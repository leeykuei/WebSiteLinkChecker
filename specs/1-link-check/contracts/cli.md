# Contracts: CLI 接口定義

## 介面：命令列啟動

範例：

```bash
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --concurrency 10 --timeout 10 --use-playwright true --report-type all --output reports/report.csv
```

參數說明：
- `--url` (required): 目標頁面 URL
- `--concurrency` (optional): 並發連線數，預設 10
- `--timeout` (optional): 單次請求 timeout（秒），預設 10
- `--max-retries` (optional): 最大重試次數，預設 3
- `--use-playwright` (optional): 是否啟用 Playwright 模式以擷取動態連結，預設 false
- `--report-type` (optional): `all` 或 `failures`，預設 `all`
- `--output` (optional): CSV 輸出檔案路徑，預設 `report.csv`（建議指定 `reports/report.csv`）

## 輸出 CSV 欄位範例
- `Scan Time`, `Page Title`, `Breadcrumb`, `Page URL`, `Link Text`, `Link URL`, `HTTP Status`, `Result`, `Response Time`, `Source`, `Depth`

## JSON 範例（若需要機器介面）

```json
{
  "page_url": "https://www.entiebank.com.tw/entie/home",
  "links": [
    {"raw_href":"/entie/about","absolute_url":"https://www.entiebank.com.tw/entie/about","status_code":200,"elapsed_ms":123,"error":null},
    {"raw_href":"/entie/missing","absolute_url":"https://www.entiebank.com.tw/entie/missing","status_code":404,"elapsed_ms":89,"error":"404 Not Found"}
  ]
}
```

**Contracts 完成**: 2026-03-01
