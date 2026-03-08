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
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output reports/report.xlsx --use-playwright true
```

4. 預設輸出為 `report.xlsx`（Excel 格式）；若 `--output` 給 `.csv` 也會自動轉成 `.xlsx`。

5. 報表欄位固定為：
`Scan Time`, `Page Title`, `Breadcrumb`, `Page URL`, `Link Text`, `Link URL`, `HTTP Status`, `Result`, `Response Time`, `Source`, `Depth`。

6. 失效連結專用報表範例：

```bash
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --report-type failures --output reports/failures.xlsx
```

註記：
- 初次執行 Playwright 模式時會下載瀏覽器二進位檔，需耐心等待。
- HEAD→GET 自動降級：當伺服器不支援 HEAD 請求時，工具會自動改用 GET 進行檢查，確保準確性。

**Quickstart 完成**: 2026-03-01
