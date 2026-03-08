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
