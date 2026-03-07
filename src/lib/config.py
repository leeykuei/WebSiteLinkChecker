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
    progress: bool = True
    progress_interval_seconds: float = 1.0
    progress_bar_width: int = 20
    max_failures_display: int = 50
    no_ansi: bool = False
    show_current_url: bool = True
    show_eta: bool = True
    max_links: int | None = None  # 限制檢查連結數（None=無限制）

    def validate(self) -> None:
        """驗證主要參數範圍，避免執行期間才拋錯。"""
        if not 1 <= self.concurrency <= 50:
            raise ValueError(f'--concurrency 必須在 1-50 範圍內，收到: {self.concurrency}')
        if not 3 <= self.timeout_seconds <= 60:
            raise ValueError(f'--timeout 必須在 3-60 範圍內，收到: {self.timeout_seconds}')
        if self.max_retries < 0:
            raise ValueError(f'--max-retries 不可小於 0，收到: {self.max_retries}')
        if not 0.1 <= self.progress_interval_seconds <= 10:
            raise ValueError(
                f'--progress-interval 必須在 0.1-10 範圍內，收到: {self.progress_interval_seconds}'
            )
        if not 10 <= self.progress_bar_width <= 50:
            raise ValueError(
                f'--progress-bar-width 必須在 10-50 範圍內，收到: {self.progress_bar_width}'
            )
        if not 0 <= self.max_failures_display <= 1000:
            raise ValueError(
                f'--max-failures-display 必須在 0-1000 範圍內，收到: {self.max_failures_display}'
            )
        if self.report_type not in ('all', 'failures'):
            raise ValueError(f"--report-type 只接受 all 或 failures，收到: {self.report_type}")
        if self.max_links is not None and self.max_links < 1:
            raise ValueError(f'--max-links 必須 >= 1 或為空，收到: {self.max_links}')
