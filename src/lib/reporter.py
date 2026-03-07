"""報表輸出（Excel）與簡單日誌格式化（繁體中文註解）"""
from __future__ import annotations

from datetime import datetime
from typing import Dict
import csv
from pathlib import Path
from urllib.parse import urlparse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def _compute_url_depth(url: str) -> int:
    parsed = urlparse(url)
    return len([segment for segment in parsed.path.split('/') if segment])


def _build_result_text(status_code: object) -> str:
    if status_code is None:
        return 'Broken'
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return 'Broken'
    return 'OK' if 200 <= code <= 299 else 'Broken'


def _format_scan_time(row: Dict) -> str:
    if row.get('scan_time'):
        return str(row['scan_time'])

    ts = row.get('check_timestamp')
    if ts is None:
        return ''
    try:
        return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M')
    except (TypeError, ValueError, OSError):
        return ''


def _normalize_report_row(row: Dict) -> Dict[str, object]:
    """轉換輸入列為新報表欄位。"""
    link_url = row.get('link_url') or row.get('url') or row.get('absolute_url') or row.get('raw_href') or ''
    status_code = row.get('http_status') if row.get('http_status') is not None else row.get('status_code')
    result_text = row.get('result') or _build_result_text(status_code)
    response_time = row.get('response_time') if row.get('response_time') is not None else row.get('elapsed_ms')
    source = row.get('source') or row.get('source_page_url') or row.get('page_url') or ''
    depth = row.get('depth')
    if depth is None:
        depth = _compute_url_depth(str(link_url)) if link_url else 0

    page_url = row.get('page_url') or row.get('source_page_url') or ''
    # 當 page_url 與 link_url 相同時，不顯示 page_url
    if page_url == link_url:
        page_url = ''

    return {
        'Scan Time': _format_scan_time(row),
        'Page Title': row.get('page_title', ''),
        'Breadcrumb': row.get('breadcrumb', ''),
        'Page URL': page_url,
        'Link Text': row.get('link_text', ''),
        'Link URL': link_url,
        'HTTP Status': status_code,
        'Result': result_text,
        'Response Time': response_time,
        'Source': source,
        'Depth': depth,
    }


def write_csv(path: str | Path, rows: list[Dict]) -> None:
    """將結果寫成 CSV（UTF-8），使用報表欄位格式。（向後兼容用）"""
    fieldnames = [
        'Scan Time',
        'Page Title',
        'Breadcrumb',
        'Page URL',
        'Link Text',
        'Link URL',
        'HTTP Status',
        'Result',
        'Response Time',
        'Source',
        'Depth',
    ]
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    with p.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(_normalize_report_row(r))


def write_excel(path: str | Path, rows: list[Dict]) -> None:
    """將結果寫成 Excel（.xlsx），使用報表欄位格式。"""
    fieldnames = [
        'Scan Time',
        'Page Title',
        'Breadcrumb',
        'Page URL',
        'Link Text',
        'Link URL',
        'HTTP Status',
        'Result',
        'Response Time',
        'Source',
        'Depth',
    ]
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    # 確保副檔名為 .xlsx
    if p.suffix.lower() not in ['.xlsx', '.xls']:
        p = p.with_suffix('.xlsx')

    wb = Workbook()
    ws = wb.active
    ws.title = "Link Check Report"

    # 寫入標題列（加粗、背景色）
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid")
    for col_idx, field in enumerate(fieldnames, start=1):
        cell = ws.cell(row=1, column=col_idx, value=field)
        cell.font = header_font
        cell.fill = header_fill

    # 寫入資料列
    for row_idx, row_data in enumerate(rows, start=2):
        normalized = _normalize_report_row(row_data)
        for col_idx, field in enumerate(fieldnames, start=1):
            ws.cell(row=row_idx, column=col_idx, value=normalized[field])

    # 自動調整欄寬（簡易版）
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)  # 最大寬度50
        ws.column_dimensions[column].width = adjusted_width

    wb.save(str(p))
