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
python src/link_checker.py \
	--url https://www.entiebank.com.tw/entie/home \
	--output reports/report.csv \
	--use-playwright true
```

範例中的報表檔案預設輸出到 `reports/` 目錄。

日誌：預設輸出到控制台，若使用 `--logfile` 會額外輸出到指定檔案。

注意：所有程式註解與文件使用繁體中文。

## 即時進度可視化

工具預設啟用即時進度顯示，會輸出：

- 目前進度條與百分比
- 已處理頁面數 / 已發現頁面數
- 已檢查連結數 / 已發現連結數
- 失效連結數
- 已耗時與預估剩餘時間（ETA）
- 目前頁面 URL 與連結 URL（可選）

失效連結會以新行即時輸出，不會被進度覆寫。

### 常用參數

- `--progress` / `--no-progress`：啟用或停用進度顯示
- `--progress-interval`：進度更新間隔（預設 `1.0` 秒）
- `--progress-bar-width`：進度條寬度（範圍 `10-50`）
- `--max-failures-display`：即時顯示失效連結上限（範圍 `0-1000`）
- `--no-ansi`：停用 ANSI 覆寫模式，改為純文字追加輸出
- `--show-current-url` / `--no-show-current-url`：是否顯示目前 URL
- `--show-eta` / `--no-show-eta`：是否顯示 ETA

### 範例

```bash
# 預設：啟用進度顯示
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output reports/report.csv --use-playwright true

# 快速測試：只檢查前 10 個連結
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output reports/report_quick.csv --use-playwright true --max-links 10

# 調整更新頻率與進度條寬度
python src/link_checker.py --url https://example.com --output reports/report_example.csv --progress-interval 0.5 --progress-bar-width 30

# 禁用進度顯示（CI/CD 或批次腳本常用）
python src/link_checker.py --url https://example.com --output reports/report_no_progress.csv --no-progress

# 禁用 ANSI（不支援 ANSI 的終端機）
python src/link_checker.py --url https://example.com --output reports/report_no_ansi.csv --no-ansi
```

當標準輸出非互動式（例如輸出重導向）時，工具會自動停用進度覆寫模式，仍會正常輸出 CSV。

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