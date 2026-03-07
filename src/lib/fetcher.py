"""非同步連結檢查與重試邏輯（繁體中文註解）"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional
import asyncio
import logging
import time
from aiohttp import ClientSession, ClientError

from lib.config import Config

try:
    from lib.progress import FailedLinkDetail, ProgressState
except Exception:  # pragma: no cover - 避免在無進度模組時造成 import 失敗
    FailedLinkDetail = Any  # type: ignore
    ProgressState = Any  # type: ignore

logger = logging.getLogger('link-checker.fetcher')


FailureCallback = Callable[[FailedLinkDetail], Optional[Awaitable[None]]]


async def _fetch_with_retries(
    session: ClientSession,
    url: str,
    timeout: int,
    max_retries: int,
    backoff_initial: float,
) -> Dict[str, Any]:
    """對單一 URL 發送請求，支援重試與指數退避。先嘗試 HEAD，失敗則 fallback 到 GET。"""
    attempt = 0
    start = time.time()
    last_exc = None
    use_get = False

    while attempt <= max_retries:
        try:
            if use_get:
                # 直接使用 GET 進行檢查
                async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                    status = resp.status
                    elapsed = (time.time() - start) * 1000
                    return {
                        'url': url,
                        'status_code': status,
                        'elapsed_ms': int(elapsed),
                        'error': None,
                    }
            else:
                # 先嘗試 HEAD（輕量級）
                async with session.head(
                    url, timeout=timeout, allow_redirects=True
                ) as resp:
                    status = resp.status
                    elapsed = (time.time() - start) * 1000
                    return {
                        'url': url,
                        'status_code': status,
                        'elapsed_ms': int(elapsed),
                        'error': None,
                    }

        except asyncio.TimeoutError as e:
            # HEAD 或 GET timeout
            if not use_get:
                # 第一次超時發生在 HEAD，試著降級為 GET（不計入重試次數）
                logger.debug('HEAD 超時，降級為 GET: %s', url)
                use_get = True
                continue
            
            # GET 也超時了，才計為真正的重試
            last_exc = e
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

        except ClientError as e:
            # HEAD 失敗（如 405），或 GET ClientError
            if not use_get:
                # 第一次失敗發生在 HEAD，試著降級為 GET（不計入重試次數）
                logger.debug('HEAD 失敗 (%s)，降級為 GET: %s', type(e).__name__, url)
                use_get = True
                continue
            
            # GET 也失敗了，才計為真正的重試
            last_exc = e
            attempt += 1
            if attempt > max_retries:
                elapsed = (time.time() - start) * 1000
                return {
                    'url': url,
                    'status_code': None,
                    'elapsed_ms': int(elapsed),
                    'error': str(e),
                }
            await asyncio.sleep(backoff_initial * (2 ** (attempt - 1)))

        except Exception as e:
            # 其他例外視為最終錯誤
            elapsed = (time.time() - start) * 1000
            return {
                'url': url,
                'status_code': None,
                'elapsed_ms': int(elapsed),
                'error': str(e),
            }

    # 若迴圈結束但仍未返回
    elapsed = (time.time() - start) * 1000
    return {
        'url': url,
        'status_code': None,
        'elapsed_ms': int(elapsed),
        'error': str(last_exc),
    }


async def collect_link_statuses(
    links: list[str],
    cfg: Config,
    progress_state: Optional[ProgressState] = None,
    on_failure: Optional[FailureCallback] = None,
    source_page_url: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """並發收集所有連結狀態，並可選地更新進度狀態。"""
    # 應用 max_links 限制（用於測試）
    if cfg.max_links is not None and cfg.max_links > 0:
        links = links[:cfg.max_links]
    
    results: list[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(cfg.concurrency)
    timeout = cfg.timeout_seconds
    max_retries = cfg.max_retries
    backoff_initial = cfg.retry_backoff_initial

    if progress_state is not None:
        await progress_state.update_discovered_links(len(links))

    # 單一 session 對多 worker 共用，避免每個連結重建連線
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36'
    }
    async with ClientSession(headers=headers) as session:

        async def worker(url: str):
            async with semaphore:
                if progress_state is not None:
                    await progress_state.set_current_link(url)
                    await progress_state.start_checking_link()  # 標記開始檢查

                res = await _fetch_with_retries(
                    session, url, timeout, max_retries, backoff_initial
                )

                res['check_timestamp'] = time.time()
                res['source_page_url'] = source_page_url
                logger.debug('Checked %s -> %s', url, res.get('status_code'))
                results.append(res)

                if progress_state is not None:
                    detail = await progress_state.update_checked_link(
                        url=url,
                        status_code=res.get('status_code'),
                        error_message=res.get('error'),
                        source_page=source_page_url,
                    )
                    if detail is not None and on_failure is not None:
                        maybe_awaitable = on_failure(detail)
                        if maybe_awaitable is not None:
                            await maybe_awaitable

        tasks = [asyncio.create_task(worker(u)) for u in links]
        await asyncio.gather(*tasks)

    return results
