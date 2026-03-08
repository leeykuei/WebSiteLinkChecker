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
    assert c.progress is True
    assert c.progress_interval_seconds == 1.0
    assert c.progress_bar_width == 20
    assert c.max_failures_display == 50
    assert c.no_ansi is False
    assert c.show_current_url is True
    assert c.show_eta is True


def test_config_validate_ok():
    c = Config()
    c.validate()


def test_config_validate_bad_progress_interval():
    c = Config(progress_interval_seconds=0.05)
    with pytest.raises(ValueError):
        c.validate()
