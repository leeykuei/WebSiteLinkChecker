# CLI Interface Contract: 即時檢查進度可視化

**Feature**: 002-realtime-progress  
**Date**: 2026-03-07  
**Status**: Phase 1 Complete  
**Contract Type**: Command-Line Interface

## 概述

本文件定義增強後的連結檢查工具 CLI 介面規格，確保向後相容現有功能，同時新增進度可視化相關參數。所有介面變更遵循語義版本控制（Semantic Versioning），保持穩定性與可預測性。

---

## CLI 命令格式

### 基本語法

```bash
python src/link_checker.py --url <URL> [OPTIONS]
```

### 必填參數

| 參數 | 簡寫 | 類型 | 說明 | 範例 |
|-----|------|------|------|------|
| `--url` | `-u` | `string` | 要檢查的起始頁面 URL | `--url https://www.example.com` |

### 選填參數（現有功能）

| 參數 | 簡寫 | 類型 | 預設值 | 說明 |
|-----|------|------|--------|------|
| `--concurrency` | `-c` | `int` | `10` | 並發連線數（範圍 1-50） |
| `--timeout` | `-t` | `int` | `10` | 每次請求 timeout（秒，範圍 3-60） |
| `--max-retries` | `-r` | `int` | `3` | 最大重試次數 |
| `--use-playwright` | `-p` | `bool` | `false` | 是否啟用 Playwright 擷取動態連結 |
| `--report-type` | | `enum` | `all` | 報表類型：`all` 或 `failures` |
| `--output` | `-o` | `string` | `report.csv` | CSV 輸出檔案路徑 |
| `--logfile` | `-l` | `string` | `None` | 日誌檔案路徑（可選） |

### **新增參數（進度可視化）**

| 參數 | 簡寫 | 類型 | 預設值 | 說明 |
|-----|------|------|--------|------|
| `--progress` | | `bool` | `true` | 是否啟用進度顯示（預設啟用） |
| `--progress-interval` | | `float` | `1.0` | 進度更新間隔（秒） |
| `--progress-bar-width` | | `int` | `20` | 進度條字符寬度 |
| `--max-failures-display` | | `int` | `50` | 即時顯示失效連結的最大數量 |
| `--no-ansi` | | `bool` | `false` | 禁用 ANSI 彩色輸出（強制使用純文字） |
| `--show-current-url` | | `bool` | `true` | 是否顯示目前檢查的 URL |
| `--show-eta` | | `bool` | `true` | 是否顯示預估剩餘時間（ETA） |

---

## 參數詳細說明

### `--progress` / 禁用進度 `--no-progress`

**用途**：控制是否啟用即時進度顯示。

**行為**：
- `--progress` 或不指定（預設）：啟用進度顯示
- `--no-progress`：禁用進度顯示，僅輸出失效連結和最終摘要
- 當輸出被重定向時（如 `> output.txt`），自動禁用進度顯示

**範例**：
```bash
# 啟用進度（預設）
python src/link_checker.py --url https://example.com

# 明確禁用進度
python src/link_checker.py --url https://example.com --no-progress
```

---

### `--progress-interval`

**用途**：設定進度更新的時間間隔（秒）。

**約束**：
- 最小值：0.1 秒
- 最大值：10 秒
- 預設值：1.0 秒
- 過低的值可能影響效能，過高的值降低即時性

**範例**：
```bash
# 更頻繁更新（每 0.5 秒）
python src/link_checker.py --url https://example.com --progress-interval 0.5
```

---

### `--progress-bar-width`

**用途**：設定進度條的字符寬度。

**約束**：
- 最小值：10
- 最大值：50
- 預設值：20
- 過長的進度條可能在窄終端機中換行

**範例**：
```bash
# 使用 30 字符寬的進度條
python src/link_checker.py --url https://example.com --progress-bar-width 30
```

---

### `--max-failures-display`

**用途**：限制即時顯示失效連結的最大數量，避免終端機被淹沒。

**行為**：
- 前 N 個失效連結會即時顯示
- 超過 N 個後，顯示摘要訊息：「還有 X 個失效連結，詳見 CSV 報表」
- 所有失效連結仍會記錄到 CSV 報表

**約束**：
- 最小值：0（不即時顯示，僅記錄到 CSV）
- 最大值：1000
- 預設值：50

**範例**：
```bash
# 只即時顯示前 20 個失效連結
python src/link_checker.py --url https://example.com --max-failures-display 20
```

---

### `--no-ansi`

**用途**：禁用 ANSI 跳脫序列，使用純文字模式。

**行為**：
- 進度顯示降級為追加新行模式
- 禁用彩色輸出
- 適用於不支援 ANSI 的終端機或日誌記錄

**範例**：
```bash
# 在不支援 ANSI 的環境中使用
python src/link_checker.py --url https://example.com --no-ansi
```

---

### `--show-current-url`

**用途**：控制是否在進度行中顯示目前正在檢查的 URL。

**行為**：
- `--show-current-url`（預設）：顯示目前 URL
- `--no-show-current-url`：不顯示目前 URL，節省終端機空間

**範例**：
```bash
# 不顯示目前 URL
python src/link_checker.py --url https://example.com --no-show-current-url
```

---

### `--show-eta`

**用途**：控制是否顯示預估剩餘時間（ETA）。

**行為**：
- `--show-eta`（預設）：顯示 ETA
- `--no-show-eta`：不顯示 ETA

**範例**：
```bash
# 不顯示 ETA
python src/link_checker.py --url https://example.com --no-show-eta
```

---

## 完整範例

### 範例 1：基本使用（預設進度顯示）

```bash
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv
```

**預期輸出**：
```
開始擷取連結...
正在檢查: https://www.entiebank.com.tw/about
[=========>          ] 45% | 已檢查: 450/1000 | 失效: 12 | 用時: 01:23 | 剩餘: ~01:50

❌ 失效連結: https://www.entiebank.com.tw/broken (HTTP 404)
❌ 失效連結: https://www.entiebank.com.tw/timeout (請求超時)

檢查完成！
----------
總耗時: 03:12
總連結數: 1000
有效連結: 988
失效連結: 12
----------
輸出報表：report.csv
```

---

### 範例 2：高並發 + 自定義進度設定

```bash
python src/link_checker.py \
  --url https://example.com \
  --concurrency 30 \
  --progress-interval 0.5 \
  --progress-bar-width 30 \
  --max-failures-display 20 \
  --output fast_check.csv
```

**說明**：
- 使用 30 個並發連線
- 每 0.5 秒更新進度
- 使用 30 字符寬的進度條
- 只即時顯示前 20 個失效連結

---

### 範例 3：禁用進度顯示（適用於腳本或 CI/CD）

```bash
python src/link_checker.py \
  --url https://example.com \
  --no-progress \
  --output report.csv \
  > output.log 2>&1
```

**說明**：
- 禁用進度顯示
- 將所有輸出重定向到 `output.log`
- 適合在自動化腳本中使用

---

### 範例 4：動態連結檢查 + 進度可視化

```bash
python src/link_checker.py \
  --url https://modern-spa.com \
  --use-playwright true \
  --progress \
  --show-current-url \
  --show-eta \
  --output spa_check.csv
```

**說明**：
- 啟用 Playwright 擷取動態渲染連結
- 顯示進度、目前 URL、預估剩餘時間

---

## 輸出格式

### 標準輸出（stdout）- 進度資訊

**ANSI 模式**（預設）：
```
正在檢查: https://example.com/page1
[=========>          ] 45% | 已檢查: 450/1000 | 失效: 12 | 用時: 01:23 | 剩餘: ~01:50
```

**純文字模式**（`--no-ansi`）：
```
[2026-03-07 14:30:45] 進度: 45% | 已檢查: 450/1000 | 失效: 12
[2026-03-07 14:30:46] 進度: 46% | 已檢查: 460/1000 | 失效: 12
```

### 失效連結通知（追加新行）

```
❌ 失效連結: https://example.com/broken (HTTP 404)
❌ 失效連結: https://example.com/error (HTTP 500 - Internal Server Error)
⏱ 失效連結: https://example.com/slow (請求超時)
```

### 最終摘要

```
檢查完成！
----------
總耗時: 03:12
總連結數: 1000
有效連結: 988
失效連結: 12
----------
輸出報表：report.csv
```

---

## 錯誤處理

### 參數驗證錯誤

```bash
$ python src/link_checker.py --url https://example.com --concurrency 100
錯誤：--concurrency 必須在 1-50 範圍內，收到: 100
```

```bash
$ python src/link_checker.py --url https://example.com --progress-interval 0.05
錯誤：--progress-interval 必須在 0.1-10 範圍內，收到: 0.05
```

### 執行時錯誤

```bash
$ python src/link_checker.py --url invalid-url
錯誤：無效的 URL 格式: invalid-url
```

```bash
$ python src/link_checker.py --url https://example.com --output /readonly/path/report.csv
錯誤：無法寫入輸出檔案: /readonly/path/report.csv (權限拒絕)
```

---

## 退出碼（Exit Codes）

| 退出碼 | 含義 | 說明 |
|-------|------|------|
| `0` | 成功 | 檢查完成，所有連結有效或僅有預期失效 |
| `1` | 一般錯誤 | 參數錯誤、配置錯誤、檔案 I/O 錯誤 |
| `2` | 檢查失敗 | 發現失效連結（當 `--report-type failures` 時） |
| `130` | 用戶中斷 | 用戶按 Ctrl+C 中途取消檢查 |

**範例**：
```bash
python src/link_checker.py --url https://example.com
echo $?  # 輸出退出碼
0  # 檢查成功完成
```

---

## 向後相容性

### 現有參數保持不變

所有現有參數（v1.0 版本）保持完全相容：
- `--url`, `--concurrency`, `--timeout`, `--max-retries`
- `--use-playwright`, `--report-type`, `--output`, `--logfile`

### 預設行為變更

⚠️ **重要**：v2.0 版本預設啟用進度顯示。若要保持 v1.0 行為，請使用 `--no-progress`。

**遷移指南**：
```bash
# v1.0 行為（無進度顯示）
python src/link_checker.py --url https://example.com

# v2.0 等效命令
python src/link_checker.py --url https://example.com --no-progress
```

---

## 配置檔案支援（可選）

### 配置檔案格式（YAML）

```yaml
# link_checker_config.yaml
url: https://www.entiebank.com.tw/entie/home
concurrency: 20
timeout: 15
use_playwright: false
output: report.csv

# 進度顯示設定
progress:
  enabled: true
  interval_seconds: 1.0
  bar_width: 20
  max_failures_display: 50
  ansi_colors: true
  show_current_url: true
  show_eta: true
```

### 使用配置檔案

```bash
python src/link_checker.py --config link_checker_config.yaml
```

**優先順序**：
1. 命令列參數（最高優先級）
2. 配置檔案
3. 預設值

---

## 環境變數支援

### 支援的環境變數

| 環境變數 | 說明 | 範例 |
|---------|------|------|
| `LINK_CHECKER_URL` | 預設 URL | `export LINK_CHECKER_URL=https://example.com` |
| `LINK_CHECKER_NO_ANSI` | 禁用 ANSI | `export LINK_CHECKER_NO_ANSI=1` |
| `LINK_CHECKER_NO_PROGRESS` | 禁用進度 | `export LINK_CHECKER_NO_PROGRESS=1` |

**應用場景**：
- CI/CD 管道中設定環境變數，統一控制行為
- 容器化部署中設定預設配置

---

## 測試驗證

### 單元測試

```python
def test_cli_argument_parsing():
    """測試 CLI 參數解析"""
    args = parse_args(['--url', 'https://example.com', '--progress-interval', '0.5'])
    assert args.url == 'https://example.com'
    assert args.progress_interval == 0.5

def test_cli_argument_validation():
    """測試參數驗證"""
    with pytest.raises(ValueError, match="concurrency 必須在 1-50 範圍內"):
        validate_args({'concurrency': 100})
```

### 集成測試

```bash
# 測試基本功能
pytest tests/test_cli_integration.py::test_basic_check_with_progress

# 測試參數驗證
pytest tests/test_cli_integration.py::test_invalid_parameters

# 測試進度顯示
pytest tests/test_cli_integration.py::test_progress_display
```

---

## Implementation Notes (2026-03-07)

- 已實作 `--progress/--no-progress`、`--progress-interval`、`--progress-bar-width`、`--max-failures-display`、`--no-ansi`、`--show-current-url`、`--show-eta`。
- 參數範圍驗證由 `Config.validate()` 統一處理，錯誤時以退出碼 `1` 返回。
- 非互動式輸出（`stdout` 非 TTY）會自動停用進度顯示覆寫，CSV 仍正常輸出。
- `--report-type failures` 於執行結束後再過濾，確保最終摘要統計一致。
- 用戶中斷（Ctrl+C）返回退出碼 `130`，並輸出部分結果摘要。

---

**Phase 1 CLI Contract 完成**。所有命令列介面已明確定義，確保向後相容性與使用者友好性。
