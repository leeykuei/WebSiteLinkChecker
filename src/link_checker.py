#!/usr/bin/env python3
"""主程式：連結檢查工具

使用方式示例：
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home --output report.csv --use-playwright false

所有註解與說明皆為繁體中文。
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime
import logging
import sys
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from lib.config import Config
from lib.parser import (
    extract_link_items_from_html,
    extract_links_from_html,
    extract_page_metadata_from_html,
)
from lib.fetcher import collect_link_statuses
from lib.reporter import write_excel
from lib.playwright_adapter import (
    PlaywrightFetchError,
    fetch_link_items_with_playwright,
)
from lib.progress import (
    ProgressDisplayConfig,
    ProgressRenderer,
    ProgressState,
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
    parser.add_argument('--output', default='report.csv', help='CSV 輸出檔案路徑')
    parser.add_argument('--logfile', default=None, help='日誌檔案路徑 (可選)')
    parser.add_argument('--progress', action=argparse.BooleanOptionalAction, default=True, help='是否啟用進度顯示')
    parser.add_argument('--progress-interval', type=float, default=1.0, help='進度更新間隔（秒）')
    parser.add_argument('--progress-bar-width', type=int, default=20, help='進度條寬度（10-50）')
    parser.add_argument('--max-failures-display', type=int, default=50, help='失效連結即時顯示上限（0-1000）')
    parser.add_argument('--max-links', type=int, default=None, help='限制檢查連結數（用於測試）')
    parser.add_argument('--no-ansi', action='store_true', help='禁用 ANSI 覆寫模式')
    parser.add_argument(
        '--show-current-url',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='是否顯示目前頁面/連結 URL',
    )
    parser.add_argument(
        '--show-eta',
        action=argparse.BooleanOptionalAction,
        default=True,
        help='是否顯示預估剩餘時間',
    )
    return parser


async def _fetch_static_links(url: str, timeout: int) -> List[str]:
    import aiohttp

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
            html = await resp.text()
    return extract_links_from_html(html, base_url=url)


async def _fetch_static_page_data(url: str, timeout: int) -> Dict[str, object]:
    """抓取靜態 HTML 並提取頁面與連結報表所需資訊。"""
    import aiohttp

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36'
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


def _build_breadcrumb_from_url(url: str) -> str:
    parsed = urlparse(url)
    segments = [segment for segment in parsed.path.split('/') if segment]
    if not segments:
        return ''
    return ' > '.join(segments)


async def _fetch_target_page_metadata_map(
    urls: list[str],
    timeout: int,
    concurrency: int,
) -> Dict[str, Dict[str, str]]:
    """抓取每個目標連結頁面的 title/breadcrumb，供報表填寫。"""
    import aiohttp

    unique_urls = []
    seen = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        unique_urls.append(url)

    if not unique_urls:
        return {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36'
    }
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 5)))
    metadata: Dict[str, Dict[str, str]] = {}

    async with aiohttp.ClientSession(headers=headers) as session:

        async def worker(url: str) -> None:
            async with semaphore:
                try:
                    async with session.get(
                        url,
                        timeout=timeout,
                        allow_redirects=True,
                    ) as resp:
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
                        page_title, breadcrumb = extract_page_metadata_from_html(
                            html,
                            page_url=final_url,
                        )
                        metadata[url] = {
                            'page_url': final_url,
                            'page_title': page_title,
                            'breadcrumb': breadcrumb,
                        }
                except Exception:
                    # 保持主流程穩定，個別頁面 metadata 失敗時略過
                    return

        await asyncio.gather(*(worker(url) for url in unique_urls))

    return metadata


def _compute_depth(url: str) -> int:
    parsed = urlparse(url)
    return len([segment for segment in parsed.path.split('/') if segment])


def _dedup_keep_order(links: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for link in links:
        if link in seen:
            continue
        seen.add(link)
        output.append(link)
    return output


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
        progress=args.progress,
        progress_interval_seconds=args.progress_interval,
        progress_bar_width=args.progress_bar_width,
        max_failures_display=args.max_failures_display,
        no_ansi=args.no_ansi,
        show_current_url=args.show_current_url,
        show_eta=args.show_eta,
        max_links=args.max_links,
    )

    try:
        cfg.validate()
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    progress_state = ProgressState()
    await progress_state.update_discovered_pages(1)
    await progress_state.set_current_page(args.url)

    progress_config = ProgressDisplayConfig(
        enabled=cfg.progress,
        update_interval_seconds=cfg.progress_interval_seconds,
        progress_bar_width=cfg.progress_bar_width,
        max_failures_display=cfg.max_failures_display,
        fallback_to_newline_mode=cfg.no_ansi,
        show_current_url=cfg.show_current_url,
        show_eta=cfg.show_eta,
    )
    renderer = ProgressRenderer(progress_config)

    progress_enabled = cfg.progress
    if progress_enabled and not sys.stdout.isatty():
        logger.info('偵測到非互動式輸出，已自動停用進度顯示。')
        progress_enabled = False

    stop_event = asyncio.Event()
    progress_task: asyncio.Task[None] | None = None
    shown_failures = 0
    hidden_failures = 0
    overflow_notice_sent = False

    async def on_failed_link(detail) -> None:
        nonlocal shown_failures, hidden_failures, overflow_notice_sent
        if shown_failures < cfg.max_failures_display:
            if progress_enabled and renderer.supports_overwrite:
                sys.stdout.write('\r\033[K')
                sys.stdout.flush()
            print(renderer.render_failed_link_notification(detail))
            shown_failures += 1
            return

        hidden_failures += 1
        if not overflow_notice_sent:
            print(renderer.render_failure_overflow_notice(hidden_failures))
            overflow_notice_sent = True

    if progress_enabled:
        progress_task = asyncio.create_task(display_progress_loop(progress_state, renderer, stop_event))

    logger.info('開始擷取連結', extra={'page': args.url})

    links: List[str] = []
    results: list[dict] = []
    exit_code = 0

    try:
        dynamic_link_items: List[Dict[str, str]] = []
        dynamic_links: List[str] = []
        fallback_to_static = False

        if cfg.use_playwright:
            await progress_state.set_current_page(args.url)
            try:
                dynamic_link_items = await fetch_link_items_with_playwright(args.url)
                dynamic_links = [
                    item.get('url', '') for item in dynamic_link_items if item.get('url')
                ]
            except PlaywrightFetchError as exc:
                fallback_to_static = True
                logger.error('Playwright 擷取失敗，將退回至靜態 HTML 擷取: %s', exc)

        if fallback_to_static:
            await progress_state.set_current_page(args.url)

        static_page_data = await _fetch_static_page_data(args.url, cfg.timeout_seconds)
        static_link_items = static_page_data.get('link_items', [])
        static_links = [item.get('url', '') for item in static_link_items if item.get('url')]

        # 建立 URL -> 連結文字對照（優先使用可取得非空文字的來源）
        link_text_by_url: Dict[str, str] = {}
        for item in static_link_items:
            link_url = item.get('url', '')
            link_text = str(item.get('text', '') or '').strip()
            if link_url and link_text:
                link_text_by_url[link_url] = link_text

        for item in dynamic_link_items:
            link_url = item.get('url', '')
            link_text = str(item.get('text', '') or '').strip()
            if link_url and link_text and not link_text_by_url.get(link_url):
                link_text_by_url[link_url] = link_text

        links = _dedup_keep_order(dynamic_links + static_links)
        await progress_state.update_processed_pages(1)

        logger.info('共擷取到 %s 個連結', len(links))

        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        page_title = str(static_page_data.get('page_title', '') or '')
        breadcrumb = str(static_page_data.get('breadcrumb', '') or '')

        results = await collect_link_statuses(
            links,
            cfg,
            progress_state=progress_state,
            on_failure=on_failed_link,
            source_page_url=args.url,
        )

        # 針對每個成功連結抓取目標頁 metadata，避免所有列都套用同一頁資訊
        successful_urls: list[str] = []
        for row in results:
            status = row.get('status_code')
            try:
                if status is not None and 200 <= int(status) <= 299:
                    successful_urls.append(str(row.get('url', '') or ''))
            except (TypeError, ValueError):
                continue

        target_page_meta_by_url = await _fetch_target_page_metadata_map(
            successful_urls,
            timeout=cfg.timeout_seconds,
            concurrency=cfg.concurrency,
        )

        # 補齊報表欄位資料
        source_label = page_title or args.url
        for row in results:
            link_url = str(row.get('url', '') or '')
            status = row.get('status_code')
            try:
                is_valid = status is not None and 200 <= int(status) <= 299
            except (TypeError, ValueError):
                is_valid = False

            target_meta = target_page_meta_by_url.get(link_url, {})
            target_page_url = str(target_meta.get('page_url', '') or link_url)
            target_page_title = str(target_meta.get('page_title', '') or page_title)
            target_breadcrumb = str(
                target_meta.get('breadcrumb', '')
                or _build_breadcrumb_from_url(target_page_url)
                or breadcrumb
            )

            breadcrumb_depth = 0
            if target_breadcrumb:
                breadcrumb_depth = len([
                    segment for segment in target_breadcrumb.split('>') if segment.strip()
                ])

            row.update({
                'scan_time': scan_time,
                'page_title': target_page_title,
                'breadcrumb': target_breadcrumb,
                'page_url': target_page_url,
                'link_text': link_text_by_url.get(link_url, ''),
                'link_url': link_url,
                'http_status': status,
                'result': 'OK' if is_valid else 'Broken',
                'response_time': row.get('elapsed_ms'),
                'source': source_label,
                'depth': breadcrumb_depth or _compute_depth(target_page_url),
            })
    except KeyboardInterrupt:
        logger.warning('檢查被用戶中斷，將輸出部分結果。')
        exit_code = 130
    except Exception as exc:
        logger.exception('執行失敗: %s', exc)
        exit_code = 1
    finally:
        if progress_task is not None:
            stop_event.set()
            await progress_task

    final_snapshot = await progress_state.snapshot()
    print(renderer.render_final_summary(final_snapshot))

    report_rows = results
    if cfg.report_type == 'failures':
        report_rows = [
            r for r in results if not (r.get('status_code') is not None and 200 <= int(r.get('status_code')) <= 299)
        ]
        if report_rows and exit_code == 0:
            exit_code = 2

    logger.info(
        '檢查摘要',
        extra={
            'total_links': final_snapshot.discovered_links,
            'checked_links': final_snapshot.checked_links,
            'failed_links': final_snapshot.failed_links,
            'elapsed_seconds': round(final_snapshot.elapsed_seconds, 3),
            'report_type': cfg.report_type,
        },
    )

    outpath = Path(args.output)
    write_excel(outpath, report_rows)
    logger.info('輸出報表：%s', outpath)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
