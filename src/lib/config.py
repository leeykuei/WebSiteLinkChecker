"""配置模型與預設值（繁體中文註解）"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    timeout_seconds: int = 10
    concurrency: int = 10
    max_retries: int = 3
    retry_backoff_initial: float = 0.5
    use_playwright: bool = False
    report_type: str = 'all'  # 'all' | 'failures'
    max_links: int | None = None
    progress: bool = True
    progress_interval_seconds: float = 1.0
    progress_bar_width: int = 20
    max_failures_display: int = 50
    no_ansi: bool = False
    show_current_url: bool = True
    show_eta: bool = True
    compact_mode_threshold: int = 50

    def validate(self) -> None:
        if not (3 <= int(self.timeout_seconds) <= 60):
            raise ValueError('timeout_seconds 必須介於 3 到 60 之間')
        if not (1 <= int(self.concurrency) <= 50):
            raise ValueError('concurrency 必須介於 1 到 50 之間')
        if not (0 <= int(self.max_retries) <= 10):
            raise ValueError('max_retries 必須介於 0 到 10 之間')
        if self.report_type not in ('all', 'failures'):
            raise ValueError("report_type 只能是 'all' 或 'failures'")
        if self.max_links is not None and int(self.max_links) <= 0:
            raise ValueError('max_links 必須大於 0')
        if not (0.1 <= float(self.progress_interval_seconds) <= 10.0):
            raise ValueError('progress_interval_seconds 必須介於 0.1 到 10.0 之間')
        if not (10 <= int(self.progress_bar_width) <= 50):
            raise ValueError('progress_bar_width 必須介於 10 到 50 之間')
        if not (0 <= int(self.max_failures_display) <= 1000):
            raise ValueError('max_failures_display 必須介於 0 到 1000 之間')
        if int(self.compact_mode_threshold) <= 0:
            raise ValueError('compact_mode_threshold 必須大於 0')
