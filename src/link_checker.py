#!/usr/bin/env python3
"""主程式：連結檢查工具

使用方式示例：
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv --use-playwright false

所有註解與說明皆為繁體中文。
"""
from __future__ import annotations
import argparse
import asyncio
import logging
import csv
from pathlib import Path
from typing import List

from lib.config import Config
from lib.parser import extract_links_from_html
from lib.fetcher import collect_link_statuses
from lib.reporter import write_csv
from lib.playwright_adapter import fetch_links_with_playwright


def setup_logging(level: int = logging.INFO, logfile: str | None = None) -> None:
    """設定結構化日誌（JSON 支援若安裝 python-json-logger）。"""
    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    handlers = [logging.StreamHandler()]
    if logfile:
        handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


async def main() -> None:
    parser = argparse.ArgumentParser(description='連結檢查工具 (繁體中文)')
    parser.add_argument('--url', required=True, help='要檢查的頁面 URL')
    parser.add_argument('--concurrency', type=int, default=10, help='並發連線數 (預設 10)')
    parser.add_argument('--timeout', type=int, default=10, help='每次請求 timeout (秒)')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重試次數')
    parser.add_argument('--use-playwright', type=lambda s: s.lower() in ('true','1','yes'), default=False, help='是否啟用 Playwright 以擷取動態連結')
    parser.add_argument('--report-type', choices=['all','failures'], default='all', help='報表類型')
    parser.add_argument('--output', default='report.csv', help='CSV 輸出檔案路徑')
    parser.add_argument('--logfile', default=None, help='日誌檔案路徑 (可選)')
    args = parser.parse_args()

    setup_logging(logfile=args.logfile)
    logger = logging.getLogger('link-checker')
    cfg = Config(timeout_seconds=args.timeout, concurrency=args.concurrency, max_retries=args.max_retries, use_playwright=args.use_playwright, report_type=args.report_type)

    logger.info('開始擷取連結', extra={'page': args.url})

    links: List[str] = []
    if cfg.use_playwright:
        try:
            links = await fetch_links_with_playwright(args.url)
        except Exception as e:
            logger.error('Playwright 擷取失敗，將退回至靜態 HTML 擷取', exc_info=e)
    if not links:
        # 若未使用 Playwright 或 Playwright 失敗，改用靜態解析
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(args.url, timeout=cfg.timeout_seconds) as resp:
                html = await resp.text()
        links = extract_links_from_html(html, base_url=args.url)

    logger.info(f'共擷取到 {len(links)} 個連結')

    # 並發檢查連結
    results = await collect_link_statuses(links, cfg)

    # 根據 report_type 過濾
    if cfg.report_type == 'failures':
        results = [r for r in results if not (r['status_code'] and 200 <= r['status_code'] <= 299)]

    outpath = Path(args.output)
    write_csv(outpath, results)
    logger.info(f'輸出報表：{outpath}')


if __name__ == '__main__':
    asyncio.run(main())
