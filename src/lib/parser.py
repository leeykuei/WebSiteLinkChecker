"""HTML 解析與連結抽取（繁體中文註解）"""
from __future__ import annotations

import base64
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup


def _extract_breadcrumb_text(soup: BeautifulSoup) -> str:
    """嘗試從常見麵包屑容器提取文字。"""
    selectors = [
        'nav.breadcrumb',
        '.breadcrumb',
        '[aria-label="breadcrumb"]',
        '[data-testid="breadcrumb"]',
        '.breadCrumbs',
        '.breadcrumbWrap',
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue
        parts = [text.strip() for text in node.stripped_strings if text.strip()]
        if parts:
            return ' > '.join(parts)
    return ''


def _decode_window_json_blob(html: str, variable_name: str) -> Optional[Any]:
    """解碼 window.<var> = "..." 中的 base64 + URL 編碼 JSON。"""
    pattern = rf'window\.{re.escape(variable_name)}\s*=\s*"([^"]+)"'
    matched = re.search(pattern, html)
    if not matched:
        return None

    try:
        raw = matched.group(1)
        json_text = unquote(base64.b64decode(raw).decode('ascii', errors='ignore'))
        return json.loads(json_text)
    except Exception:
        return None


def _find_sitemap_crumbs(node: Any, target_path: str, crumbs: List[str]) -> Optional[List[str]]:
    """在 siteMap 樹中尋找目標路徑並回傳完整麵包屑。"""
    if isinstance(node, dict):
        text = node.get('siteMapText')
        node_url = node.get('url')
        next_crumbs = crumbs
        if isinstance(text, str) and text.strip():
            next_crumbs = crumbs + [text.strip()]

        if isinstance(node_url, str) and node_url.strip() == target_path:
            return next_crumbs

        for value in node.values():
            result = _find_sitemap_crumbs(value, target_path, next_crumbs)
            if result:
                return result
        return None

    if isinstance(node, list):
        for value in node:
            result = _find_sitemap_crumbs(value, target_path, crumbs)
            if result:
                return result
        return None

    return None


def _is_generic_title(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized in {'entie-web', 'entie web', 'entie'}


def extract_page_metadata_from_html(
    html: str,
    page_url: str | None = None,
) -> Tuple[str, str]:
    """提取頁面名稱與麵包屑文字。"""
    soup = BeautifulSoup(html, 'html.parser')

    title_node = soup.find('title')
    h1_node = soup.find('h1')
    page_title = ''
    # 優先使用 H1，可避免 title 只有站名而缺乏頁面語意
    if h1_node and h1_node.get_text(strip=True):
        page_title = h1_node.get_text(strip=True)
    elif title_node and title_node.get_text(strip=True):
        page_title = title_node.get_text(strip=True)

    breadcrumb = _extract_breadcrumb_text(soup)

    # 針對 Entie 站點：優先從 window.siteMap/pageData 還原可讀中文麵包屑
    page_data = _decode_window_json_blob(html, 'pageData')
    site_map = _decode_window_json_blob(html, 'siteMap')

    target_path = ''
    if page_url:
        target_path = urlparse(page_url).path

    sitemap_crumbs: Optional[List[str]] = None
    if site_map is not None and target_path:
        sitemap_crumbs = _find_sitemap_crumbs(site_map, target_path, [])

    if sitemap_crumbs:
        breadcrumb = ' > '.join(sitemap_crumbs)
        # 若目前 title 為站名，改用麵包屑最後一節作為頁面名稱
        if not page_title or _is_generic_title(page_title):
            page_title = sitemap_crumbs[-1]

    if isinstance(page_data, dict):
        site_map_text = str(page_data.get('siteMapText', '') or '').strip()
        if site_map_text:
            if not breadcrumb:
                breadcrumb = site_map_text
            if not page_title or _is_generic_title(page_title):
                page_title = site_map_text

    return page_title, breadcrumb


def extract_link_items_from_html(html: str, base_url: str) -> List[Dict[str, str]]:
    """從 HTML 中提取連結明細（URL + 文字），並保持去重後順序。"""
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find_all('a')

    items: List[Dict[str, str]] = []
    for anchor in anchors:
        href = anchor.get('href')
        if not href:
            continue
        if href.startswith('javascript:') or href.startswith('mailto:'):
            continue

        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ('http', 'https'):
            continue

        text = anchor.get_text(' ', strip=True)
        items.append({'url': abs_url, 'text': text})

    # 以 URL 去重，保留第一個文字
    seen = set()
    ordered: List[Dict[str, str]] = []
    for item in items:
        url = item['url']
        if url in seen:
            continue
        seen.add(url)
        ordered.append(item)
    return ordered


def extract_links_from_html(html: str, base_url: str) -> List[str]:
    """從 HTML 中抽取所有 `<a>` 的 href，並解析為絕對 URL。"""
    return [item['url'] for item in extract_link_items_from_html(html, base_url)]
