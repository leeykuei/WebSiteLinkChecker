"""進度追蹤與顯示模組。"""
from __future__ import annotations

import asyncio
import os
import platform
import sys
import time
from dataclasses import dataclass, field
from typing import IO, Optional


@dataclass
class FailedLinkDetail:
    """失效連結詳細資訊。"""

    url: str
    status_code: Optional[int]
    error_message: Optional[str]
    source_page: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class ProgressSnapshot:
    """不可變進度快照，避免渲染時讀到中途變動資料。"""

    discovered_pages: int
    processed_pages: int
    discovered_links: int
    checking_links: int  # 正在檢查中的連結數
    checked_links: int
    failed_links: int
    current_page_url: str
    current_link_url: str
    progress_percentage: float
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float]
    timestamp: float


@dataclass
class ProgressDisplayConfig:
    """進度顯示設定。"""

    enabled: bool = True
    update_interval_seconds: float = 1.0
    progress_bar_width: int = 20
    max_url_display_length: int = 80
    max_failures_display: int = 50
    fallback_to_newline_mode: bool = False
    show_current_url: bool = True
    show_eta: bool = True


@dataclass
class ProgressState:
    """整體進度狀態。"""

    discovered_pages: int = 0
    processed_pages: int = 0
    discovered_links: int = 0
    checking_links: int = 0  # 正在檢查中的連結數
    checked_links: int = 0
    failed_links: int = 0
    current_page_url: str = ""
    current_link_url: str = ""
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    failed_link_details: list[FailedLinkDetail] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def update_discovered_pages(self, count: int = 1) -> None:
        async with self._lock:
            self.discovered_pages += max(0, count)
            self.last_update_time = time.time()

    async def update_processed_pages(self, count: int = 1) -> None:
        async with self._lock:
            self.processed_pages += max(0, count)
            self.last_update_time = time.time()

    async def update_discovered_links(self, count: int) -> None:
        async with self._lock:
            self.discovered_links += max(0, count)
            self.last_update_time = time.time()

    async def set_current_page(self, url: str) -> None:
        async with self._lock:
            self.current_page_url = url
            self.last_update_time = time.time()

    async def set_current_link(self, url: str) -> None:
        async with self._lock:
            self.current_link_url = url
            self.last_update_time = time.time()

    async def start_checking_link(self) -> None:
        """標記開始檢查一個連結（進入檢查中狀態）。"""
        async with self._lock:
            self.checking_links += 1
            self.last_update_time = time.time()

    async def update_checked_link(
        self,
        url: str,
        status_code: Optional[int],
        error_message: Optional[str],
        source_page: Optional[str] = None,
    ) -> Optional[FailedLinkDetail]:
        """更新連結檢查結果，若失效則回傳失效明細。"""
        async with self._lock:
            self.checking_links = max(0, self.checking_links - 1)  # 離開檢查中狀態
            self.checked_links += 1
            self.current_link_url = url
            self.last_update_time = time.time()

            if status_code is not None and 200 <= status_code <= 299:
                return None

            self.failed_links += 1
            detail = FailedLinkDetail(
                url=url,
                status_code=status_code,
                error_message=error_message,
                source_page=source_page,
            )
            self.failed_link_details.append(detail)
            return detail

    async def snapshot(self) -> ProgressSnapshot:
        async with self._lock:
            now = time.time()
            elapsed = max(0.0, now - self.start_time)
            percentage = self._progress_percentage()
            eta = self._estimated_remaining(elapsed)
            return ProgressSnapshot(
                discovered_pages=self.discovered_pages,
                processed_pages=self.processed_pages,
                discovered_links=self.discovered_links,
                checking_links=self.checking_links,
                checked_links=self.checked_links,
                failed_links=self.failed_links,
                current_page_url=self.current_page_url,
                current_link_url=self.current_link_url,
                progress_percentage=percentage,
                elapsed_seconds=elapsed,
                estimated_remaining_seconds=eta,
                timestamp=now,
            )

    def _progress_percentage(self) -> float:
        if self.discovered_links <= 0:
            return 0.0
        # 只基於已完成的連結計算進度，不包含檢查中的
        return min(100.0, (self.checked_links / self.discovered_links) * 100.0)

    def _estimated_remaining(self, elapsed_seconds: float) -> Optional[float]:
        # 使用已完成的連結計算平均時間，不包含正在檢查中的
        if self.checked_links <= 0:
            return None
        avg = elapsed_seconds / self.checked_links
        # 剩餘連結 = 總數 - 已完成 - 檢查中
        remain = self.discovered_links - self.checked_links - self.checking_links
        if remain <= 0:
            return 0.0
        return max(0.0, avg * remain)


class ProgressRenderer:
    """將進度快照渲染為終端輸出字串。"""

    def __init__(self, config: ProgressDisplayConfig, stream: IO[str] = sys.stdout):
        self.config = config
        self.stream = stream
        self.supports_overwrite = self._detect_overwrite_support()

    def _detect_overwrite_support(self) -> bool:
        if self.config.fallback_to_newline_mode:
            return False

        if not hasattr(self.stream, "isatty") or not self.stream.isatty():
            return False

        term = os.getenv("TERM", "")
        if term.lower() == "dumb":
            return False

        if sys.platform == "win32":
            try:
                version_parts = platform.version().split(".")
                build = int(version_parts[2]) if len(version_parts) >= 3 else 0
                if build < 10586:
                    return False
            except Exception:
                return False

        return True

    def render_progress_line(self, snapshot: ProgressSnapshot) -> str:
        bar = self._format_progress_bar(snapshot.progress_percentage)
        
        # 連結狀態顯示：如果有檢查中的連結，顯示在括號內
        links_status = f"連結: {snapshot.checked_links}/{snapshot.discovered_links}"
        if snapshot.checking_links > 0:
            links_status += f" (檢查中: {snapshot.checking_links})"
        
        parts: list[str] = [
            f"{bar} {snapshot.progress_percentage:>3.0f}%",
            f"頁面: {snapshot.processed_pages}/{snapshot.discovered_pages}",
            links_status,
            f"失效: {snapshot.failed_links}",
            f"用時: {self._format_time(snapshot.elapsed_seconds)}",
        ]
        if self.config.show_eta and snapshot.estimated_remaining_seconds is not None:
            parts.append(f"剩餘: ~{self._format_time(snapshot.estimated_remaining_seconds)}")

        if self.config.show_current_url:
            if snapshot.current_page_url:
                parts.append(f"頁面URL: {self._truncate(snapshot.current_page_url)}")
            if snapshot.current_link_url:
                parts.append(f"連結URL: {self._truncate(snapshot.current_link_url)}")

        return " | ".join(parts)

    def render_failed_link_notification(self, detail: FailedLinkDetail) -> str:
        if detail.status_code is None:
            err = detail.error_message or "未知錯誤"
            return f"[FAIL] 失效連結: {detail.url} ({err})"
        return f"[FAIL] 失效連結: {detail.url} (HTTP {detail.status_code})"

    def render_failure_overflow_notice(self, remaining_count: int) -> str:
        return f"[INFO] 還有 {remaining_count} 個失效連結未即時顯示，詳見 CSV 報表。"

    def render_final_summary(self, snapshot: ProgressSnapshot) -> str:
        ok_count = max(0, snapshot.checked_links - snapshot.failed_links)
        lines = [
            "\n檢查完成！",
            "----------",
            f"總耗時: {self._format_time(snapshot.elapsed_seconds)}",
            f"總頁面數: {snapshot.discovered_pages}",
            f"總連結數: {snapshot.discovered_links}",
            f"有效連結: {ok_count}",
            f"失效連結: {snapshot.failed_links}",
            "----------",
        ]
        return "\n".join(lines)

    def _format_progress_bar(self, percentage: float) -> str:
        width = max(10, self.config.progress_bar_width)
        ratio = max(0.0, min(100.0, percentage)) / 100.0
        filled = int(width * ratio)
        if filled <= 0:
            body = ">" + " " * (width - 1)
        elif filled >= width:
            body = "=" * width
        else:
            body = "=" * (filled - 1) + ">" + " " * (width - filled)
        return f"[{body}]"

    def _format_time(self, seconds: float) -> str:
        sec = max(0, int(seconds))
        mins, sec = divmod(sec, 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{sec:02d}"
        return f"{mins:02d}:{sec:02d}"

    def _truncate(self, text: str) -> str:
        max_len = max(20, self.config.max_url_display_length)
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


async def display_progress_loop(
    state: ProgressState,
    renderer: ProgressRenderer,
    stop_event: asyncio.Event,
) -> None:
    """定時輸出進度。

    - 支援 ANSI 單行覆寫模式
    - 不支援時降級為追加新行模式
    """
    last_line = ""
    while not stop_event.is_set():
        snapshot = await state.snapshot()
        line = renderer.render_progress_line(snapshot)

        if renderer.supports_overwrite:
            renderer.stream.write(f"\r\033[K{line}")
            renderer.stream.flush()
        else:
            if line != last_line:
                print(line)
                last_line = line

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=renderer.config.update_interval_seconds)
        except asyncio.TimeoutError:
            continue

    if renderer.supports_overwrite:
        renderer.stream.write("\r\033[K")
        renderer.stream.flush()
