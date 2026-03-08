"""HTML 解析與連結抽取（繁體中文註解）"""
from __future__ import annotations

import base64
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup


def _canonical_path(url_or_path: str) -> str:
    path = urlparse(url_or_path).path if '://' in url_or_path else url_or_path
    normalized = (path or '/').strip() or '/'
    normalized = normalized.rstrip('/')
    return normalized or '/'


def _decode_window_json_blob(html: str, var_name: str) -> Optional[Any]:
    """解碼 window.<var> = 'base64(urlencoded(json))' 內容。"""
    pattern = rf"window\.{re.escape(var_name)}\s*=\s*['\"]([^'\"]+)['\"]"
    match = re.search(pattern, html)
    if not match:
        return None

    blob = (match.group(1) or '').strip()
    if not blob:
        return None

    # base64 padding 修復
    blob += '=' * (-len(blob) % 4)
    try:
        raw = base64.b64decode(blob)
        text = raw.decode('utf-8', errors='ignore')
        decoded = unquote(text)
        return json.loads(decoded)
    except Exception:
        return None


def _extract_text(node: Dict[str, Any]) -> str:
    for key in ('siteMapText', 'text', 'name', 'title'):
        val = node.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ''


def _iter_children(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    children: List[Dict[str, Any]] = []
    for key in ('children', 'siteMapList', 'subSiteMap'):
        raw = node.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    children.append(item)
    return children


def _find_sitemap_crumbs(data: Any, page_url: str) -> List[str]:
    """在 siteMap 樹中找對應頁面的 breadcrumb。"""
    target_path = _canonical_path(page_url)

    def walk(node: Dict[str, Any], trail: List[str]) -> Optional[List[str]]:
        url = str(node.get('url') or '')
        text = _extract_text(node)
        next_trail = trail + ([text] if text else [])

        if url and _canonical_path(url) == target_path:
            return next_trail

        for child in _iter_children(node):
            found = walk(child, next_trail)
            if found:
                return found
        return None

    if isinstance(data, dict):
        result = walk(data, [])
        return result or []
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            result = walk(item, [])
            if result:
                return result
    return []


def _is_generic_title(title: str) -> bool:
    t = (title or '').strip().lower()
    if not t:
        return True
    generic = {
        'entie-web',
        '安泰銀行',
        'entiebank',
        'home',
        '首頁',
    }
    return t in generic


def extract_page_metadata_from_html(html: str, page_url: str = '') -> Tuple[str, str]:
    """提取頁面標題與 breadcrumb（盡量使用人類可讀資訊）。"""
    soup = BeautifulSoup(html, 'html.parser')

    title = ''
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text(strip=True):
        title = title_tag.get_text(strip=True)
    elif soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)

    breadcrumb = ''
    # 優先使用動態渲染的麵包屑（支援 moduleBreadcrumbList）
    breadcrumb_selectors = [
        '[aria-label="breadcrumb"]',
        '.moduleBreadcrumbList', 
        'nav.breadcrumb',
        '.breadcrumb',
    ]
    
    for selector in breadcrumb_selectors:
        breadcrumb_node = soup.select_one(selector)
        if breadcrumb_node:
            # 嘗試從 <a> 和 text nodes 提取麵包屑項目
            items = []
            for link in breadcrumb_node.find_all('a'):
                text = link.get_text(strip=True)
                if text:
                    items.append(text)
            
            # 如果沒找到 <a> 標籤，嘗試從 <li> 提取
            if not items:
                for li in breadcrumb_node.find_all('li'):
                    text = li.get_text(strip=True)
                    # 移除 ">" 符號
                    text = text.replace('>', '').strip()
                    if text:
                        items.append(text)
            
            # 如果還是沒有，使用原始方法
            if not items:
                full_text = breadcrumb_node.get_text(' ', strip=True)
                # 嘗試用 ">" 分割
                if '>' in full_text:
                    items = [x.strip() for x in full_text.split('>') if x.strip()]
                else:
                    items = [x.strip() for x in full_text.split() if x.strip()]
            
            if items:
                breadcrumb = ' > '.join(items)
                break

    site_map = _decode_window_json_blob(html, 'siteMap')
    if site_map is None:
        site_map = _decode_window_json_blob(html, 'moduleListData')
    page_data = _decode_window_json_blob(html, 'pageData')

    # 只有在沒找到好的麵包屑時，才使用 siteMap fallback
    if not breadcrumb and page_url and site_map is not None:
        crumbs = _find_sitemap_crumbs(site_map, page_url)
        if crumbs:
            breadcrumb = ' > '.join(crumbs)
            if _is_generic_title(title):
                title = crumbs[-1]

    if isinstance(page_data, dict):
        page_text = str(page_data.get('siteMapText') or '').strip()
        if page_text and _is_generic_title(title):
            title = page_text
        if not breadcrumb:
            raw_path = page_data.get('breadcrumb') or page_data.get('siteMapPath') or []
            if isinstance(raw_path, list):
                parts = [str(x).strip() for x in raw_path if str(x).strip()]
                if parts:
                    breadcrumb = ' > '.join(parts)

    if not breadcrumb and page_url:
        segments = [seg for seg in urlparse(page_url).path.split('/') if seg]
        if segments:
            breadcrumb = ' > '.join(segments)

    if _is_generic_title(title) and breadcrumb:
        title = breadcrumb.split('>')[-1].strip()
    if not title and breadcrumb:
        title = breadcrumb.split('>')[-1].strip()

    return title.strip(), breadcrumb.strip()


def extract_link_items_from_html(html: str, base_url: str) -> List[Dict[str, str]]:
    """抽取連結與連結文字，並回傳去重後的列表。"""
    soup = BeautifulSoup(html, 'html.parser')
    output: List[Dict[str, str]] = []
    seen: set[str] = set()

    for a in soup.find_all('a'):
        href = (a.get('href') or '').strip()
        if not href or href.startswith('javascript:') or href.startswith('mailto:'):
            continue

        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ('http', 'https'):
            continue

        text = a.get_text(' ', strip=True)
        if abs_url in seen:
            continue
        seen.add(abs_url)
        output.append({'url': abs_url, 'text': text})

    return output


def extract_links_from_html(html: str, base_url: str) -> List[str]:
    """從 HTML 中抽取所有 `<a>` 的 href，並解析為絕對 URL。"""
    return [item['url'] for item in extract_link_items_from_html(html, base_url)]
