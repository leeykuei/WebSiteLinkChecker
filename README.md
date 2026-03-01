# Link Checker — 快速說明（繁體中文）

此工具會擷取指定頁面的超連結（含動態渲染），並以非同步方式檢查每個連結的 HTTP 回應，最終輸出 CSV 報表。

快速上手：

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt
# 若要使用 Playwright 模式：
playwright install
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv
```

日誌：預設輸出到控制台，若使用 `--logfile` 會額外輸出到指定檔案。

注意：所有程式註解與文件使用繁體中文。

## 執行測試

本專案使用 `pytest` 進行單元測試。建議在虛擬環境中安裝相依並執行測試：

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 若尚未安裝 pytest，可執行：
pip install pytest

# 執行測試：
pytest -q
```

備註：若未安裝 `beautifulsoup4`，`tests/test_parser.py` 會自動跳過；若使用 Playwright 相關測試，請先執行 `playwright install` 下載瀏覽器二進位檔。