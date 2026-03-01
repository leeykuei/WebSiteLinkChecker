from pathlib import Path
import sys
import pytest

# 將 src 加入 sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    from lib.parser import extract_links_from_html
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False


@pytest.mark.skipif(not BS4_AVAILABLE, reason='beautifulsoup4 未安裝，跳過 HTML 解析測試')
def test_extract_links_basic():
    html = '<a href="/a">A</a><a href="http://example.com/b">B</a><a href="mailto:me@example.com">Mail</a><a>nohref</a>'
    links = extract_links_from_html(html, base_url='https://www.example.com/')
    assert 'https://www.example.com/a' in links
    assert 'http://example.com/b' in links
    # mailto 不應包含
    assert not any(l.startswith('mailto:') for l in links)
    # 無 href 不應包含
    assert len(links) == 2
