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

3. 範例執行：

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

註記：初次執行 Playwright 模式時會下載瀏覽器二進位檔，需耐心等待。

**Quickstart 完成**: 2026-03-01
