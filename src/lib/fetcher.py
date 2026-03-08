"""非同步連結檢查與重試邏輯（繁體中文註解）"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
import logging
import time

from aiohttp import ClientError, ClientSession

from lib.config import Config

if TYPE_CHECKING:
    from lib.progress import ProgressState

logger = logging.getLogger('link-checker.fetcher')


async def _fetch_with_retries(
    session: ClientSession,
    url: str,
    timeout: int,
    max_retries: int,
    backoff_initial: float,
) -> Dict[str, Any]:
    """對單一 URL 發送請求，支援重試與指數退避。先 HEAD，失敗時降級 GET。"""
    attempt = 0
    start = time.time()
    last_exc: Optional[Exception] = None
    use_get = False

    while attempt <= max_retries:
        try:
            if use_get:
                async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                    status = resp.status
                    elapsed = (time.time() - start) * 1000
                    return {
                        'url': url,
                        'status_code': status,
                        'elapsed_ms': int(elapsed),
                        'error': None,
                    }

            async with session.head(url, timeout=timeout, allow_redirects=True) as resp:
                status = resp.status
                elapsed = (time.time() - start) * 1000
                return {
                    'url': url,
                    'status_code': status,
                    'elapsed_ms': int(elapsed),
                    'error': None,
                }

        except asyncio.TimeoutError as exc:
            if not use_get:
                use_get = True
                continue

            last_exc = exc
            attempt += 1
            if attempt > max_retries:
                elapsed = (time.time() - start) * 1000
                return {
                    'url': url,
                    'status_code': None,
                    'elapsed_ms': int(elapsed),
                    'error': 'timeout',
                }
            await asyncio.sleep(backoff_initial * (2 ** (attempt - 1)))

        except ClientError as exc:
            if not use_get:
                use_get = True
                continue

            last_exc = exc
            attempt += 1
            if attempt > max_retries:
                elapsed = (time.time() - start) * 1000
                return {
                    'url': url,
                    'status_code': None,
                    'elapsed_ms': int(elapsed),
                    'error': str(exc),
                }
            await asyncio.sleep(backoff_initial * (2 ** (attempt - 1)))

        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return {
                'url': url,
                'status_code': None,
                'elapsed_ms': int(elapsed),
                'error': str(exc),
            }

    elapsed = (time.time() - start) * 1000
    return {
        'url': url,
        'status_code': None,
        'elapsed_ms': int(elapsed),
        'error': str(last_exc) if last_exc else 'unknown error',
    }


async def collect_link_statuses(
    links: List[str],
    cfg: Config,
    source_page_url: Optional[str] = None,
    progress_state: Optional['ProgressState'] = None,
) -> List[Dict[str, Any]]:
    """並發收集所有連結狀態。"""
    if cfg.max_links is not None and cfg.max_links > 0:
        links = links[: cfg.max_links]

    if not links:
        return []

    results: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(cfg.concurrency)

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36'
        )
    }

    async with ClientSession(headers=headers) as session:

        async def worker(url: str) -> None:
            async with semaphore:
                # 標記開始檢查
                if progress_state:
                    await progress_state.start_checking_link()
                    await progress_state.set_current_link(url)
                
                res = await _fetch_with_retries(
                    session,
                    url,
                    cfg.timeout_seconds,
                    cfg.max_retries,
                    cfg.retry_backoff_initial,
                )
                res['check_timestamp'] = time.time()
                res['source_page_url'] = source_page_url
                results.append(res)
                
                # 更新檢查結果
                if progress_state:
                    await progress_state.update_checked_link(
                        url=url,
                        status_code=res.get('status_code'),
                        error_message=res.get('error'),
                        source_page=source_page_url,
                    )
                
                logger.debug('Checked %s -> %s', url, res.get('status_code'))

        tasks = [asyncio.create_task(worker(url)) for url in links]
        await asyncio.gather(*tasks)

    return results
