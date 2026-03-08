"""Playwright 適配器：啟動 headless 瀏覽器並擷取頁面中所有連結（繁體中文註解）"""
from __future__ import annotations

from typing import Any, Dict, List

try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover
    async_playwright = None


class PlaywrightFetchError(RuntimeError):
    """Playwright 擷取失敗。"""


def _normalize_link_items(raw_items: Any) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    seen: set[str] = set()

    if not isinstance(raw_items, list):
        return output

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        url = str(item.get('url') or '').strip()
        text = str(item.get('text') or '').strip()
        if not url:
            continue
        if url.startswith('javascript:') or url.startswith('mailto:'):
            continue
        if not (url.startswith('http://') or url.startswith('https://')):
            continue
        if url in seen:
            continue

        seen.add(url)
        output.append({'url': url, 'text': text})

    return output


async def fetch_link_items_with_playwright(url: str, timeout: int = 30000) -> List[Dict[str, str]]:
    """使用 Playwright 回傳 [{'url', 'text'}]。"""
    if async_playwright is None:
        raise PlaywrightFetchError('Playwright 未安裝，請執行: pip install playwright && playwright install')

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 改用 domcontentloaded 而非 networkidle，避免等待過久
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            # 等待連結生成（最多等待 5 秒）
            try:
                await page.wait_for_selector('a', timeout=5000)
            except Exception:
                pass  # 如果沒有連結也不報錯
            
            # 額外等待 JavaScript 執行
            await page.wait_for_timeout(2000)

            raw_items = await page.evaluate(
                """() => Array.from(document.querySelectorAll('a')).map((a) => ({
                    url: a.href,
                    text: (a.innerText || a.textContent || '').trim(),
                }))"""
            )

            await browser.close()
            return _normalize_link_items(raw_items)
    except Exception as exc:
        raise PlaywrightFetchError(str(exc)) from exc


async def fetch_links_with_playwright(url: str, timeout: int = 30000) -> List[str]:
    """向後相容：只回傳 URL 陣列。"""
    items = await fetch_link_items_with_playwright(url=url, timeout=timeout)
    return [item['url'] for item in items]
