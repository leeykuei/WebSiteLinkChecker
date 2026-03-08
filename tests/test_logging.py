from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import sys

# 將 src 加入 sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from link_checker import setup_logging


def _flush_handlers() -> None:
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'flush'):
            handler.flush()


def test_setup_logging_uses_rotating_file_handler(tmp_path):
    log_path = tmp_path / 'logs' / 'checker.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    setup_logging(
        level=logging.INFO,
        logfile=str(log_path),
        log_max_bytes=1024,
        log_backup_count=2,
    )

    handlers = logging.getLogger().handlers
    rotating_handlers = [
        h for h in handlers
        if isinstance(h, RotatingFileHandler)
    ]

    assert len(rotating_handlers) == 1
    assert rotating_handlers[0].maxBytes == 1024
    assert rotating_handlers[0].backupCount == 2


def test_structured_log_contains_context_fields(tmp_path):
    log_path = tmp_path / 'logs' / 'checker.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    setup_logging(
        level=logging.INFO,
        logfile=str(log_path),
        log_max_bytes=4096,
        log_backup_count=1,
    )

    logger = logging.getLogger('link-checker.fetcher')
    logger.info(
        '連結檢查完成',
        extra={
            'event': 'link_checked',
            'page_url': 'https://example.com',
            'link_index': 1,
            'link_total': 3,
            'link_url': 'https://example.com/a',
            'status_code': 200,
            'elapsed_ms': 123,
            'error': None,
        },
    )
    _flush_handlers()

    assert log_path.exists()
    line = log_path.read_text(encoding='utf-8').strip().splitlines()[-1]
    assert 'page_url' in line
    assert 'link_index' in line
    assert 'link_total' in line
    assert 'link_url' in line


def test_setup_logging_creates_log_directory(tmp_path):
    log_path = tmp_path / 'nested' / 'logs' / 'checker.log'
    assert not log_path.parent.exists()

    setup_logging(
        level=logging.INFO,
        logfile=str(log_path),
        log_max_bytes=4096,
        log_backup_count=1,
    )

    logging.getLogger('link-checker').info('log-path-create-test')
    _flush_handlers()

    assert log_path.parent.exists()
    assert log_path.exists()
