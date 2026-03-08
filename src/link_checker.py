#!/usr/bin/env python3
"""主程式：連結檢查工具

使用方式示例：
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.xlsx --use-playwright false

所有註解與說明皆為繁體中文。
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from lib.config import Config
from lib.parser import (
    extract_link_items_from_html,
    extract_page_metadata_from_html,
)
from lib.fetcher import collect_link_statuses
from lib.reporter import write_excel
from lib.playwright_adapter import PlaywrightFetchError, fetch_link_items_with_playwright
from lib.progress import (
    ProgressState,
    ProgressRenderer,
    ProgressDisplayConfig,
    display_progress_loop,
)


def setup_logging(level: int = logging.INFO, logfile: str | None = None) -> None:
    """設定結構化日誌（JSON 支援若安裝 python-json-logger）。"""
    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    handlers = [logging.StreamHandler()]
    if logfile:
        handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def _bool_arg(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ('true', '1', 'yes', 'y'):
        return True
    if normalized in ('false', '0', 'no', 'n'):
        return False
    raise argparse.ArgumentTypeError(f'無效布林值: {value}')


def _validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='連結檢查工具 (繁體中文)')
    parser.add_argument('--url', required=True, help='要檢查的頁面 URL')
    parser.add_argument('--concurrency', type=int, default=10, help='並發連線數 (預設 10)')
    parser.add_argument('--timeout', type=int, default=10, help='每次請求 timeout (秒)')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重試次數')
    parser.add_argument(
        '--use-playwright',
        type=_bool_arg,
        default=False,
        help='是否啟用 Playwright 以擷取動態連結',
    )
    parser.add_argument('--report-type', choices=['all', 'failures'], default='all', help='報表類型')
    parser.add_argument('--output', default='report.xlsx', help='Excel 輸出檔案路徑')
    parser.add_argument('--logfile', default=None, help='日誌檔案路徑 (可選)')
    parser.add_argument('--max-links', type=int, default=None, help='限制檢查連結數（可選）')
    return parser


def _build_breadcrumb_from_url(url: str) -> str:
    parsed = urlparse(url)
    segments = [segment for segment in parsed.path.split('/') if segment]
    return ' > '.join(segments)


def _compute_depth(url: str) -> int:
    parsed = urlparse(url)
    return len([segment for segment in parsed.path.split('/') if segment])


def _dedup_keep_order(links: List[str]) -> List[str]:
    seen: set[str] = set()
    output: List[str] = []
    for link in links:
        if link in seen:
            continue
        seen.add(link)
        output.append(link)
    return output


async def _fetch_static_page_data(url: str, timeout: int) -> Dict[str, object]:
    """抓取靜態 HTML 並提取頁面與連結資料。"""
    import aiohttp

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
            html = await resp.text()

    page_title, breadcrumb = extract_page_metadata_from_html(html, page_url=url)
    link_items = extract_link_items_from_html(html, base_url=url)
    return {
        'page_title': page_title,
        'breadcrumb': breadcrumb,
        'link_items': link_items,
    }


async def _fetch_target_page_metadata_with_playwright(
    urls: List[str],
    timeout: int,
    concurrency: int,
) -> Dict[str, Dict[str, str]]:
    """使用 Playwright 抓取目標頁面的 title/breadcrumb（支援動態內容）。"""
    from playwright.async_api import async_playwright
    
    unique_urls: List[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)

    if not unique_urls:
        return {}

    metadata: Dict[str, Dict[str, str]] = {}
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 3)))  # 限制 Playwright 並發數

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        async def worker(url: str) -> None:
            async with semaphore:
                try:
                    page = await browser.new_page()
                    await page.goto(url, wait_until='domcontentloaded', timeout=timeout * 1000)
                    await page.wait_for_timeout(2000)  # 等待 JS 執行
                    
                    html = await page.content()
                    final_url = page.url
                    
                    page_title, breadcrumb = extract_page_metadata_from_html(html, page_url=final_url)
                    metadata[url] = {
                        'page_url': final_url,
                        'page_title': page_title,
                        'breadcrumb': breadcrumb,
                    }
                    
                    await page.close()
                except Exception:
                    # 失敗時使用 URL fallback
                    metadata[url] = {
                        'page_url': url,
                        'page_title': '',
                        'breadcrumb': _build_breadcrumb_from_url(url),
                    }

        await asyncio.gather(*(worker(url) for url in unique_urls))
        await browser.close()

    return metadata


async def _fetch_target_page_metadata_map(
    urls: List[str],
    timeout: int,
    concurrency: int,
) -> Dict[str, Dict[str, str]]:
    """抓取每個目標連結頁面的 title/breadcrumb。"""
    import aiohttp

    unique_urls: List[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)

    if not unique_urls:
        return {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 5)))
    metadata: Dict[str, Dict[str, str]] = {}

    async with aiohttp.ClientSession(headers=headers) as session:

        async def worker(url: str) -> None:
            async with semaphore:
                try:
                    async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                        if not (200 <= resp.status <= 299):
                            return

                        final_url = str(resp.url)
                        content_type = (resp.headers.get('Content-Type') or '').lower()
                        if 'text/html' not in content_type and content_type:
                            metadata[url] = {
                                'page_url': final_url,
                                'page_title': '',
                                'breadcrumb': _build_breadcrumb_from_url(final_url),
                            }
                            return

                        html = await resp.text(errors='ignore')
                        page_title, breadcrumb = extract_page_metadata_from_html(html, page_url=final_url)
                        metadata[url] = {
                            'page_url': final_url,
                            'page_title': page_title,
                            'breadcrumb': breadcrumb,
                        }
                except Exception:
                    return

        await asyncio.gather(*(worker(url) for url in unique_urls))

    return metadata


async def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    setup_logging(logfile=args.logfile)
    logger = logging.getLogger('link-checker')

    if not _validate_url(args.url):
        logger.error('無效的 URL 格式: %s', args.url)
        return 1

    cfg = Config(
        timeout_seconds=args.timeout,
        concurrency=args.concurrency,
        max_retries=args.max_retries,
        use_playwright=args.use_playwright,
        report_type=args.report_type,
        max_links=args.max_links,
    )

    try:
        cfg.validate()
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    logger.info('開始擷取連結', extra={'page': args.url})

    dynamic_link_items: List[Dict[str, str]] = []
    if cfg.use_playwright:
        try:
            dynamic_link_items = await fetch_link_items_with_playwright(
                args.url,
                timeout=cfg.timeout_seconds * 1000,
            )
        except PlaywrightFetchError as exc:
            logger.error('Playwright 擷取失敗，將退回至靜態 HTML 擷取: %s', exc)

    static_page_data = await _fetch_static_page_data(args.url, cfg.timeout_seconds)
    static_link_items = static_page_data.get('link_items', [])
    if not isinstance(static_link_items, list):
        static_link_items = []

    # 優先保留有文字的連結內容
    link_text_by_url: Dict[str, str] = {}
    for item in static_link_items:
        if not isinstance(item, dict):
            continue
        link_url = str(item.get('url') or '')
        link_text = str(item.get('text') or '').strip()
        if link_url and link_text:
            link_text_by_url[link_url] = link_text

    for item in dynamic_link_items:
        link_url = str(item.get('url') or '')
        link_text = str(item.get('text') or '').strip()
        if link_url and link_text and not link_text_by_url.get(link_url):
            link_text_by_url[link_url] = link_text

    dynamic_links = [str(item.get('url') or '') for item in dynamic_link_items if item.get('url')]
    static_links = [str(item.get('url') or '') for item in static_link_items if isinstance(item, dict) and item.get('url')]
    links = _dedup_keep_order(dynamic_links + static_links)

    if cfg.max_links is not None and cfg.max_links > 0:
        links = links[: cfg.max_links]

    logger.info('共擷取到 %s 個連結', len(links))

    # 創建進度追蹤系統
    progress_state = ProgressState()
    progress_config = ProgressDisplayConfig(enabled=True, update_interval_seconds=0.5)
    progress_renderer = ProgressRenderer(progress_config)
    progress_stop_event = asyncio.Event()
    
    # 初始化進度
    await progress_state.update_discovered_pages(1)
    await progress_state.update_processed_pages(1)
    await progress_state.update_discovered_links(len(links))
    await progress_state.set_current_page(args.url)
    
    # 啟動進度顯示後台任務
    progress_task = asyncio.create_task(
        display_progress_loop(progress_state, progress_renderer, progress_stop_event)
    )

    try:
        results = await collect_link_statuses(
            links, 
            cfg, 
            source_page_url=args.url,
            progress_state=progress_state,
        )
    finally:
        # 停止進度顯示
        progress_stop_event.set()
        await progress_task
        
        # 顯示最終摘要
        final_snapshot = await progress_state.snapshot()
        summary = progress_renderer.render_final_summary(final_snapshot)
        print(summary)

    # 針對成功連結抓取目標頁 metadata
    successful_urls: List[str] = []
    for row in results:
        status = row.get('status_code')
        try:
            if status is not None and 200 <= int(status) <= 299:
                successful_urls.append(str(row.get('url') or ''))
        except (TypeError, ValueError):
            continue

    # 使用 Playwright 獲取目標頁面 metadata（支援動態內容的中文麵包屑）
    target_page_meta_by_url = await _fetch_target_page_metadata_with_playwright(
        successful_urls,
        timeout=cfg.timeout_seconds,
        concurrency=cfg.concurrency,
    )

    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    page_title = str(static_page_data.get('page_title') or '')
    breadcrumb = str(static_page_data.get('breadcrumb') or '')
    source_label = page_title or args.url

    for row in results:
        link_url = str(row.get('url') or '')
        status = row.get('status_code')
        try:
            is_valid = status is not None and 200 <= int(status) <= 299
        except (TypeError, ValueError):
            is_valid = False

        target_meta = target_page_meta_by_url.get(link_url, {})
        target_page_url = str(target_meta.get('page_url') or link_url)
        target_page_title = str(target_meta.get('page_title') or page_title)
        target_breadcrumb = str(
            target_meta.get('breadcrumb')
            or _build_breadcrumb_from_url(target_page_url)
            or breadcrumb
        )

        breadcrumb_depth = 0
        if target_breadcrumb:
            breadcrumb_depth = len([segment for segment in target_breadcrumb.split('>') if segment.strip()])
        depth = breadcrumb_depth if breadcrumb_depth > 0 else _compute_depth(target_page_url)

        row.update(
            {
                'scan_time': scan_time,
                'page_title': target_page_title,
                'breadcrumb': target_breadcrumb,
                'page_url': target_page_url,
                'link_text': link_text_by_url.get(link_url, ''),
                'link_url': link_url,
                'http_status': row.get('status_code'),
                'result': 'OK' if is_valid else 'Broken',
                'response_time': row.get('elapsed_ms'),
                'source': source_label,
                'depth': depth,
            }
        )

    report_rows = results
    if cfg.report_type == 'failures':
        report_rows = [r for r in report_rows if r.get('result') != 'OK']

    actual_output = write_excel(Path(args.output), report_rows)
    logger.info('輸出報表：%s', actual_output)
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
