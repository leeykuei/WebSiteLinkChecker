# Data Model

## Entities

### Link
- `raw_href`: 原始在 DOM 中看到的 href（string）
- `absolute_url`: 解析後的絕對 URL（string）
- `status_code`: 最終 HTTP 回應碼（int or null if failed）
- `elapsed_ms`: 檢查耗時（毫秒）
- `error`: 錯誤訊息（若有）
- `checked_at`: 檢查時間戳（ISO 8601）

### CheckResult
- `page_url`: 被檢查的頁面 URL
- `started_at`: 檢查啟動時間
- `finished_at`: 檢查結束時間
- `total_links`: 提取到的連結數量
- `valid_links`: 狀態碼在 2xx 的數量
- `invalid_links`: 非 2xx 或錯誤的數量
- `timeout_count`: 超時次數
- `links`: List[Link]

### Configuration
- `timeout_seconds`: int (預設 10)
- `concurrency`: int (預設 10)
- `max_retries`: int (預設 3)
- `retry_backoff_initial`: float (預設 0.5)
- `use_playwright`: bool (預設 False)
- `report_type`: enum ("all" | "failures")

## Validation Rules
- `absolute_url` 必須是可解析的 HTTP/HTTPS URL
- `status_code` 若存在必為整數
- `elapsed_ms` >= 0

**資料模型完成**: 2026-03-01
