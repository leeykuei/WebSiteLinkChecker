"""Playwright 適配器：啟動 headless 瀏覽器並擷取頁面中所有連結（繁體中文註解）"""
from __future__ import annotations

from typing import Dict, List
import asyncio

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None


class PlaywrightFetchError(RuntimeError):
    """Playwright 擷取流程的標準化例外。"""

    def __init__(self, message: str, error_type: str = 'runtime'):
        super().__init__(message)
        self.error_type = error_type


def _normalize_link_items(raw_items: list[dict]) -> List[Dict[str, str]]:
    """整理 Playwright 回傳的連結項目並去重。"""
    items: List[Dict[str, str]] = []
    for raw in raw_items:
        href = str(raw.get('href', '') or '').strip()
        text = str(raw.get('text', '') or '').strip()
        if not href:
            continue
        if href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        if not (href.startswith('http://') or href.startswith('https://')):
            continue
        items.append({'url': href, 'text': text})

    seen = set()
    ordered: List[Dict[str, str]] = []
    for item in items:
        url = item['url']
        if url in seen:
            continue
        seen.add(url)
        ordered.append(item)
    return ordered


async def fetch_link_items_with_playwright(
    url: str,
    timeout: int = 15000,
) -> List[Dict[str, str]]:
    """使用 Playwright 載入頁面並回傳連結明細（url + text）。"""
    if async_playwright is None:
        raise PlaywrightFetchError(
            'Playwright 未安裝，請執行: pip install playwright && playwright install',
            error_type='dependency',
        )

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=timeout)
            raw_items = await page.evaluate(
                """() => Array.from(document.querySelectorAll('a')).map((a) => ({
                    href: a.href || '',
                    text: (a.innerText || a.textContent || '').trim()
                }))"""
            )
            if not isinstance(raw_items, list):
                return []
            return _normalize_link_items(raw_items)
    except asyncio.TimeoutError as exc:
        raise PlaywrightFetchError(f'Playwright 載入逾時: {url}', error_type='timeout') from exc
    except Exception as exc:
        raise PlaywrightFetchError(f'Playwright 執行失敗: {exc}', error_type='runtime') from exc
    finally:
        if browser is not None:
            await browser.close()


async def fetch_links_with_playwright(url: str, timeout: int = 15000) -> List[str]:
    """使用 Playwright 啟動 headless 瀏覽器，載入頁面並回傳發現的 href 清單。
    若系統未安裝 Playwright 或未下載瀏覽器二進位檔，會拋出 Exception。
    """
    items = await fetch_link_items_with_playwright(url, timeout=timeout)
    return [item['url'] for item in items]
