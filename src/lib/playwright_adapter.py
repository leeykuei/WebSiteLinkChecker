"""Playwright 適配器：啟動 headless 瀏覽器並擷取頁面中所有連結（繁體中文註解）"""
from typing import List
import asyncio

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None


async def fetch_links_with_playwright(url: str, timeout: int = 15000) -> List[str]:
    """使用 Playwright 啟動 headless 瀏覽器，載入頁面並回傳發現的 href 清單。
    若系統未安裝 Playwright 或未下載瀏覽器二進位檔，會拋出 Exception。
    """
    if async_playwright is None:
        raise RuntimeError('Playwright 未安裝，請執行: pip install playwright && playwright install')
    links = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=timeout)
        # 直接在頁面執行 JS 擷取 href
        hrefs = await page.evaluate('''() => Array.from(document.querySelectorAll('a'), a => a.href)''')
        for h in hrefs:
            if h:
                links.append(h)
        await browser.close()
    return links
