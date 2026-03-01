<!-- Sync Impact Report: Constitution v1.0.0 (Initial)
  - Version: 0.0.0 → 1.0.0 (MINOR: Initial constitutional framework)
  - Added Principles: Stability, Comprehensive Logging, Async-First Architecture
  - Added Section: Technology Stack & Language Requirements (Python specification)
  - Added Section: Development Standards & Quality Gates
  - Templates Status: ✅ plan-template.md (no changes needed) | ✅ spec-template.md (no changes needed) | ✅ tasks-template.md (no changes needed)
  - Deferred: None
-->

# 官網連結檢查程式 (Website Link Checker) 憲法

## 核心原則

### I. 穩定性 (Stability)
MUST：確保連結檢查程式在持續運行時的高可靠性與容錯能力。
- 所有網路請求必須包含重試機制（最多 3 次重試，指數退避策略）
- 支援 timeout 設置，預設 10 秒，可由用戶自訂（3-60 秒範圍）
- 異常捕捉必須完整，避免未預期的程式中斷
- 支援優雅關閉（graceful shutdown）機制，確保正在進行的檢查完整
- 定期進行穩定性測試，每次版本更新前必須執行壓力測試

### II. 詳細的錯誤紀錄 (Comprehensive Logging)
MUST：實施結構化、分級的日誌系統，便於除錯與監控。
- 日誌必須包含以下層級：DEBUG、INFO、WARNING、ERROR、CRITICAL
- 每筆連結檢查紀錄必須記錄：時戳、目標 URL、HTTP 狀態碼、檢查耗時、完整錯誤訊息
- 日誌格式採用結構化形式（JSON），支援機器解析
- 支援多輸出目標：檔案輸出、標準輸出於控制台
- 異常堆疊追蹤（stack trace）MUST 被完整記錄，便於問題根源分析
- 日誌保留期：預設 30 天，可由配置檔調整

### III. 非同步處理 (Async-First Architecture)
MUST：使用 Python asyncio 實現高效並發連結檢查，提升整體吞吐量。
- 核心檢查引擎必須採用 asyncio 框架
- 支援可配置的並發限制（預設 10 個並發連線，範圍 1-50）
- 必須使用 aiohttp 進行非同步 HTTP 請求
- 明確處理連接池資源，防止資源洩漏
- 進度追蹤必須即時更新，支援估計完成時間（ETA）顯示

## 技術棧與語言要求

**程式語言**：Python 3.9+

**核心相依套件**：
- `aiohttp` ≥ 3.8.0 - 非同步 HTTP 客戶端
- `asyncio` - Python 標準函式庫
- `logging` - Python 標準函式庫
- `dataclasses` - 用於結構化資料定義
- `json` - 結構化日誌輸出

**所有文檔、規格、程式碼註解、錯誤訊息、使用說明**：必須使用**繁體中文**

**目標檢查網站**：https://www.entiebank.com.tw/entie/home

## 開發標準與品質守門

### 程式碼品質
- 所有公開函式 MUST 包含完整 docstring（繁體中文），說明參數、回傳值、可能的例外
- 類型提示（type hints）MUST 應用於所有函式簽署，提升程式碼可讀性與檢查精確度
- 複雜邏輯必須附帶範例或測試說明用途

### 測試與驗證
- 單元測試覆蓋率 MUST ≥ 80%，重點覆蓋非同步邏輯與錯誤處理路徑
- 每次版本更新前必須執行完整測試套組與手動煙霧測試（smoke test）
- 集成測試必須驗證連結檢查的完整流程（連線建立→檢查→日誌記錄→結果輸出）

### 配置管理
- 所有可調參數必須可透過配置檔（YAML 或 JSON）設定，避免硬編碼
- 提供完整的配置範例檔案（with 繁體中文註解）
- 支援環境變數覆蓋配置檔案設定

## 治理原則 (Governance)

**憲法效力**：本憲法為本專案的最高指導文件，優先於所有開發實踐。任何違反核心原則的實現必須經過明確的豁免文檔與批准流程。

**修訂流程**：
1. 提出修訂建議並記錄理由
2. 評估版本號變更類型（MAJOR/MINOR/PATCH）
3. 更新憲法文檔若干關聯範本
4. 通過審查後推進開發計劃

**版本控制策略**：
- MAJOR：移除或重新定義核心原則
- MINOR：新增原則或實質擴展指導
- PATCH：文字澄清、修正或非語義改進

**合規檢查**：
- 所有 PR/Pull Request 必須驗證是否遵守本憲法的核心原則（特別是穩定性、日誌、非同步處理）
- 複雜設計決策必須在 spec 文檔中通過憲法原則的驗證記錄
- 每個季度進行一次合規審查，確保實踐與憲法保持一致

**運行時指導**：詳細開發指導請參閱 `.specify/templates/` 下的規格範本、計劃範本與工作清單

**版本**：1.0.0 | **批准日期**：2026-03-01 | **最後修訂**：2026-03-01
