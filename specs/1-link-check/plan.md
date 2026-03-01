# Implementation Plan: 1-link-check

**Branch**: `1-link-check` | **Date**: 2026-03-01 | **Spec**: specs/1-link-check/spec.md
**Input**: Feature specification from `specs/1-link-check/spec.md`

## Summary

建立一個以 Python 為主的 CLI 工具 `link_checker.py`，輸入目標 URL 後自動擷取頁面上所有靜態與動態產生的連結，並以非同步並發方式檢查每個連結的 HTTP 回應。支援 Playwright 模式以擷取 JavaScript 動態渲染之連結，最終輸出 UTF-8 編碼的 CSV 報表並記錄結構化日誌。

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: `aiohttp`, `asyncio`, `aiohttp_retry` (或自實作重試)、`playwright`、`yarl` 或 `urllib.parse`、`pytest`、`pydantic`（選用）  
**Storage**: N/A (輸出檔案 CSV)  
**Testing**: `pytest`，重點測試非同步程式與錯誤處理路徑  
**Target Platform**: 跨平台（Windows / Linux）以 CLI 執行  
**Project Type**: CLI 工具 + 可選 headless 瀏覽器擷取模組  
**Performance Goals**: 支援在 3 分鐘內完成含 100 個靜態連結的檢查（預設並發 10）  
**Constraints**: 單次 HTTP timeout 預設 10 秒；並發數預設 10（1-50）；重試最多 3 次，使用指數退避。

## Constitution Check

根據專案憲法 `.specify/memory/constitution.md`，本計劃必須通過以下守門條件：
- 穩定性：要求重試、timeout、優雅關閉，計劃包含重試與 timeout 設定，並會處理例外。  
- 詳細日誌：計劃使用結構化 JSON 日誌，包含層級與堆疊追蹤。  
- 非同步處理：核心檢查引擎採用 `asyncio` + `aiohttp`。  

結論：計劃符合憲法要求，GATE 通過。

## Project Structure

specs/1-link-check/
- plan.md (本檔)
- research.md (Phase 0)
- data-model.md (Phase 1)
- quickstart.md (Phase 1)
- contracts/
- spec.md

src/
- link_checker.py
- lib/
  - fetcher.py
  - parser.py
  - reporter.py
  - config.py
  - playwright_adapter.py

tests/
- unit tests for parser、fetcher、reporter

## Phase 0: Outline & Research

Unknowns already resolved in `spec.md`:
- 瀏覽器選擇：Playwright（選擇：Playwright）
- 有效狀態碼：接受所有 2xx 視為有效（選擇：2xx）
- 報表內容：預設輸出完整報表（所有連結）

Research tasks (Phase 0):
- Research Playwright 使用於 headless scraping 的最佳實作，包含安裝、可用 API 與 Python 整合範例
- Research `aiohttp` 的連線池與最佳並發模式（ClientSession、TCPConnector 設定）
- Research robust retry patterns 與 timeout 管理（指數退避參考實作）

Deliverable: `research.md`（已由 Phase 0 生成）

## Phase 1: Design & Contracts (next)

Deliverables:
- `data-model.md`（連結、檢查結果、配置）
- `contracts/cli.md`（CLI 介面定義與 JSON/CSV 報表範例）
- `quickstart.md`（安裝、執行範例）

## Risks

- 目標網站可能有反爬蟲或 rate-limit，需在用戶文件中提醒並提供速率限制參數  
- Playwright 須下載瀏覽器二進位檔，初次啟動會較慢

## Next Steps

1. 生成 `research.md`（Phase 0） — 目前進行中  
2. 生成 `data-model.md`、`contracts/`、`quickstart.md`（Phase 1） — 待完成  
3. 執行 `update-agent-context.ps1 -AgentType copilot` 更新 agent context

---

**Plan generated**: 2026-03-01
