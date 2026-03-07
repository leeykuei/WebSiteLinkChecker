# Quickstart — 連結檢查工具（Link Checker）

快速上手：

1. 建置 Python 環境（建議使用 venv 或 conda）：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows (PowerShell)
```

2. 安裝相依套件：

```bash
pip install -r requirements.txt
# 若使用 Playwright，安裝後需執行：
playwright install
```

3. 執行範例：

### 3.1 基礎範例（推薦 - 包含動態連結提取）

```bash
# 使用 Playwright 模式提取靜態 + 動態連結，並檢查所有連結
python src/link_checker.py \
  --url https://www.entiebank.com.tw/entie/home \
  --output reports/report.csv \
  --use-playwright true
```

### 3.2 快速測試範例（測試前 10 個連結）

```bash
# 在 Playwright 模式下只檢查前 10 個連結，適合快速測試
python src/link_checker.py \
  --url https://www.entiebank.com.tw/entie/home \
  --output reports/report_quick.csv \
  --use-playwright true \
  --max-links 10
```

### 3.3 性能優化範例（針對高延遲網站）

針對銀行網站等回應較慢的對象，調整以下參數：

```bash
# 降低並發數、增加超時時間、減少重試次數
python src/link_checker.py \
  --url https://www.entiebank.com.tw/entie/home \
  --output reports/report.csv \
  --use-playwright true \
  --concurrency 3 \
  --timeout 15 \
  --max-retries 2
```

**參數說明**：
- `--concurrency 3`: 同時檢查 3 個連結（預設 10）
- `--timeout 15`: 每個請求 15 秒超時（預設 10）
- `--max-retries 2`: 最多重試 2 次（預設 3）

### 3.4 完整檢查範例（含進度顯示和詳細日誌）

```bash
python src/link_checker.py \
  --url https://www.entiebank.com.tw/entie/home \
  --output reports/report.csv \
  --use-playwright true \
  --progress \
  --progress-interval 1.0 \
  --show-current-url \
  --show-eta \
  --max-failures-display 50 \
  --logfile check.log
```

### 3.5 靜態模式（僅檢查頁面 HTML 中的連結）

```bash
# 不使用 Playwright，只提取靜態 HTML 中的連結（更快）
python src/link_checker.py \
  --url https://www.entiebank.com.tw/entie/home \
  --output reports/report_static.csv \
  --use-playwright false
```

4. 輸出說明：

本文件範例皆輸出到 `reports/` 目錄（例如 `reports/report.csv`），欄位包含：
- `Scan Time`: 掃描時間（例如 `2026-03-08 10:30`）
- `Page Title`: 頁面名稱（`title` 或 `H1`）
- `Breadcrumb`: 網站位置（麵包屑）
- `Page URL`: 頁面網址
- `Link Text`: 連結文字
- `Link URL`: 被檢查的連結
- `HTTP Status`: HTTP 狀態碼
- `Result`: 檢查結果（`OK` / `Broken`）
- `Response Time`: 回應時間（毫秒）
- `Source`: 來源頁面（通常為頁面名稱）
- `Depth`: 網站層級（以 URL path 深度估算）

範例結果：
```
Scan Time,Page Title,Breadcrumb,Page URL,Link Text,Link URL,HTTP Status,Result,Response Time,Source,Depth
2026-03-08 10:30,代收代繳服務,個人金融 > 存匯,https://www.entiebank.com.tw/entie/home,申請服務,https://www.entiebank.com.tw/entie/1_1_1,200,OK,520,payment page,3
2026-03-08 10:30,代收代繳服務,個人金融 > 存匯,https://www.entiebank.com.tw/entie/home,客服中心,https://www.entiebank.com.tw/entie/missing,404,Broken,612,payment page,3
```

註記：
- 初次執行 Playwright 模式時會下載瀏覽器二進位檔，需耐心等待。
- HEAD→GET 自動降級：當伺服器不支援 HEAD 請求時，工具會自動改用 GET 進行檢查，確保準確性。

**Quickstart 完成**: 2026-03-01
