# Research: Phase 0 — 連結檢查工具研究報告

## 決策總結

- 瀏覽器自動化工具：Playwright（選擇）
  - 理由：相較 Selenium 與 Pyppeteer，Playwright 提供更佳的速度、跨瀏覽器支援、現代 API 與較佳的 headless 模式整合；同時官方提供 Python binding，安裝與管理較為便利。
  - 替代方案：Selenium（成熟但較慢）；Pyppeteer（較輕量但維護性較差）。

- 有效 HTTP 狀態碼定義：接受所有 2xx 為有效（選擇）
  - 理由：涵蓋各類成功回應（200、204、206 等），較不會因非 200 的成功回應誤判有效連結為失效。
  - 替代方案：嚴格限定 200；或提供用戶自訂有效狀態碼列表。

- CSV 報表內容：預設輸出完整報表（所有連結）
  - 理由：完整報表利於稽核與驗證，報表可由後續參數選擇只輸出失效連結。

## Playwright 研究要點

- 安裝：`pip install playwright`，需執行 `playwright install` 下載瀏覽器二進位檔（Chrome/Firefox/WebKit）
- 使用方式：使用 `async_playwright()` 啟動 browser，建立 `page`，使用 `page.goto(url)` 並等待 `networkidle` 或 `load`，再使用 `page.query_selector_all('a')` 或 `page.evaluate('Array.from(document.querySelectorAll("a"), a=>a.href)')` 擷取連結
- 注意事項：首次下載二進位檔會花時間；需處理 headless 與 headful 模式設定；若網站有反爬行為，需調整 user-agent、延遲或隨機化行為

## aiohttp 與非同步檢查要點

- 使用單一 `aiohttp.ClientSession` 並搭配 `TCPConnector(limit=...)` 控制同時 TCP 連線數，避免資源耗盡
- 對每個連結以 `session.get`（或 `session.head`）發起請求；對於某些伺服器不正確支援 HEAD，需 fallback 到 GET
- 實作重試：3 次重試、指數退避（例如 0.5s、1s、2s），並可排除 4xx 類錯誤不重試

## 日誌與報表

- 日誌：採用 Python `logging`，並使用 `logging.Formatter` 輸出 JSON（或使用 `python-json-logger`）以利機器解析
- CSV：使用 `csv` 模組輸出，確保 `encoding='utf-8-sig'` 或 `utf-8`（視 Excel 相容性需求）

## 安全與法遵

- 建議使用者確認目標網站的 robots 規範與使用條款；在 README 強調速率限制與禮貌性檢查

## 決定紀錄（可追蹤）

- `browser_engine`: Playwright
- `valid_status_codes`: 200-299
- `report_default`: all


**研究完成**: 2026-03-01
