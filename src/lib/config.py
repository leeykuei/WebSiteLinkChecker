"""配置模型與預設值（繁體中文註解）"""
from dataclasses import dataclass

@dataclass
class Config:
    timeout_seconds: int = 10
    concurrency: int = 10
    max_retries: int = 3
    retry_backoff_initial: float = 0.5
    use_playwright: bool = False
    report_type: str = 'all'  # 'all' | 'failures'
