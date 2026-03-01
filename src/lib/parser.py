"""HTML 解析與連結抽取（繁體中文註解）"""
from typing import List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def extract_links_from_html(html: str, base_url: str) -> List[str]:
    """從 HTML 中抽取所有 `<a>` 的 href，並解析為絕對 URL。"""
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.find_all('a')
    links = []
    for a in anchors:
        href = a.get('href')
        if not href:
            continue
        # 忽略 javascript: 與 mailto:
        if href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ('http','https'):
            continue
        links.append(abs_url)
    # 去重但保持順序
    seen = set()
    ordered = []
    for u in links:
        if u in seen:
            continue
        seen.add(u)
        ordered.append(u)
    return ordered
