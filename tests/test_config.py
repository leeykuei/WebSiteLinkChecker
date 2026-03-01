from pathlib import Path
import sys
import pytest

# 將 src 加入 sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from lib.config import Config


def test_config_defaults():
    c = Config()
    assert c.timeout_seconds == 10
    assert c.concurrency == 10
    assert c.max_retries == 3
    assert c.retry_backoff_initial == 0.5
    assert c.use_playwright is False
    assert c.report_type == 'all'
