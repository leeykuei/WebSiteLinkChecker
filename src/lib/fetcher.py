"""非同步連結檢查與重試邏輯（繁體中文註解）"""
from typing import List, Dict
import asyncio
import logging
import time
from aiohttp import ClientSession, ClientError
from dataclasses import asdict

logger = logging.getLogger('link-checker.fetcher')


async def _fetch_with_retries(session: ClientSession, url: str, timeout: int, max_retries: int, backoff_initial: float) -> Dict:
    """對單一 URL 發送請求，支援重試與指數退避，回傳 dict 包含 status_code, elapsed_ms, error。"""
    attempt = 0
    start = time.time()
    last_exc = None
    while attempt <= max_retries:
        try:
            # 先嘗試 HEAD，若 server 不支援再 fallback to GET
            async with session.head(url, timeout=timeout, allow_redirects=True) as resp:
                status = resp.status
                elapsed = (time.time() - start) * 1000
                return {'url': url, 'status_code': status, 'elapsed_ms': int(elapsed), 'error': None}
        except ClientError as e:
            last_exc = e
            attempt += 1
            if attempt > max_retries:
                elapsed = (time.time() - start) * 1000
                return {'url': url, 'status_code': None, 'elapsed_ms': int(elapsed), 'error': str(e)}
            await asyncio.sleep(backoff_initial * (2 ** (attempt-1)))
        except asyncio.TimeoutError as e:
            last_exc = e
            attempt += 1
            if attempt > max_retries:
                elapsed = (time.time() - start) * 1000
                return {'url': url, 'status_code': None, 'elapsed_ms': int(elapsed), 'error': 'timeout'}
            await asyncio.sleep(backoff_initial * (2 ** (attempt-1)))
        except Exception as e:
            # 其他例外視為最終錯誤
            elapsed = (time.time() - start) * 1000
            return {'url': url, 'status_code': None, 'elapsed_ms': int(elapsed), 'error': str(e)}
    # 若迴圈結束但仍未返回
    elapsed = (time.time() - start) * 1000
    return {'url': url, 'status_code': None, 'elapsed_ms': int(elapsed), 'error': str(last_exc)}


async def collect_link_statuses(links: List[str], cfg) -> List[Dict]:
    """並發收集所有連結的狀態。回傳每個連結的 dict 列表。"""
    results = []
    semaphore = asyncio.Semaphore(cfg.concurrency)
    timeout = cfg.timeout_seconds
    max_retries = cfg.max_retries
    backoff_initial = cfg.retry_backoff_initial

    async def worker(url: str):
        async with semaphore:
            async with ClientSession() as session:
                res = await _fetch_with_retries(session, url, timeout, max_retries, backoff_initial)
                logger.debug('Checked %s -> %s', url, res.get('status_code'))
                results.append(res)

    # 建立 tasks
    tasks = [asyncio.create_task(worker(u)) for u in links]
    await asyncio.gather(*tasks)
    return results
