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
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv
```

4. 預設會輸出 `report.csv`，欄位包含：`page_url, raw_href, absolute_url, status_code, elapsed_ms, error`。

註記：初次執行 Playwright 模式時會下載瀏覽器二進位檔，需耐心等待。

**Quickstart 完成**: 2026-03-01
