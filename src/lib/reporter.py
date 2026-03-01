"""報表輸出（CSV）與簡單日誌格式化（繁體中文註解）"""
from typing import List, Dict
import csv


def write_csv(path, rows: List[Dict]) -> None:
    """將結果寫成 CSV，使用 UTF-8 編碼。欄位固定：page_url, raw_href, absolute_url, status_code, elapsed_ms, error"""
    fieldnames = ['url', 'status_code', 'elapsed_ms', 'error']
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})
