# Quickstart: 即時檢查進度可視化實作指南

**Feature**: 002-realtime-progress  
**Date**: 2026-03-07  
**Audience**: 實作工程師  
**Prerequisites**: 熟悉 Python 3.9+、asyncio、命令列工具開發

## 快速概覽

本指南針對即時進度可視化功能提供簡明的實作路徑，幫助開發者快速上手。完整技術決策請參閱 [research.md](research.md)，資料模型定義請參閱 [data-model.md](data-model.md)，CLI 規格請參閱 [contracts/cli.md](contracts/cli.md)。

---

## 實作檢查清單

### Phase 1: 核心進度追蹤（2-3 小時）

- [ ] 創建 `src/lib/progress.py` 模組
- [ ] 實作 `ProgressState` 類別（狀態追蹤）
- [ ] 實作 `ProgressSnapshot` 類別（不可變快照）
- [ ] 實作基本進度計算邏輯（百分比、預估時間）
- [ ] 撰寫單元測試（`tests/test_progress.py`）

**驗收標準**：
```python
state = ProgressState()
state.discovered_links = 100
await state.update_checked_link("https://example.com", 200, None)
assert state.get_progress_percentage() == 1.0
```

---

### Phase 2: 進度渲染與顯示（2-3 小時）

- [ ] 實作 `ProgressRenderer` 類別（渲染邏輯）
- [ ] 實作 ANSI 跳脫序列的進度條渲染
- [ ] 實作失效連結通知格式化
- [ ] 實作最終摘要格式化
- [ ] 實作終端機能力檢測（ANSI 支援檢查）

**驗收標準**：
```python
renderer = ProgressRenderer(config)
line = renderer.render_progress_line(snapshot)
# 輸出: [=========>          ] 45% | 已檢查: 450/1000 | 失效: 12 | ...
```

---

### Phase 3: 整合至主程式（1-2 小時）

- [ ] 修改 `src/link_checker.py`：新增進度相關 CLI 參數
- [ ] 修改 `src/lib/fetcher.py`：注入進度回調函式
- [ ] 實作定時進度顯示任務（asyncio task）
- [ ] 實作失效連結即時通知
- [ ] 整合優雅關閉（Ctrl+C 處理）

**驗收標準**：
執行 `python src/link_checker.py --url https://example.com`，能看到即時進度更新。

---

### Phase 4: 配置與優化（1 小時）

- [ ] 實作 `ProgressDisplayConfig` 類別
- [ ] 新增配置參數解析（`--progress-interval` 等）
- [ ] 實作降級策略（不支援 ANSI 時）
- [ ] 效能測試：確保進度顯示開銷 ≤ 5%

**驗收標準**：
使用 `--no-ansi` 參數能正常顯示進度（追加新行模式）。

---

### Phase 5: 測試與文檔（2 小時）

- [ ] 撰寫集成測試
- [ ] 更新 `README.md`（新增進度顯示說明）
- [ ] 手動測試各種場景（大量連結、失效連結、中途取消）
- [ ] 驗證所有成功準則（SC-001 到 SC-013）

---

## 核心程式碼框架

### 1. `src/lib/progress.py`

```python
"""進度追蹤與顯示模組"""
from __future__ import annotations
import asyncio
import sys
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class FailedLinkDetail:
    url: str
    status_code: Optional[int]
    error_message: Optional[str]
    source_page: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class ProgressState:
    discovered_pages: int = 0
    processed_pages: int = 0
    discovered_links: int = 0
    checked_links: int = 0
    failed_links: int = 0
    current_page_url: str = ""
    current_link_url: str = ""
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    failed_link_details: List[FailedLinkDetail] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def update_checked_link(
        self, url: str, status_code: Optional[int], error: Optional[str]
    ) -> Optional[FailedLinkDetail]:
        """更新已檢查連結，返回失效連結詳情（若失效）"""
        async with self._lock:
            self.checked_links += 1
            failed_detail = None
            if status_code is None or not (200 <= status_code <= 299):
                self.failed_links += 1
                failed_detail = FailedLinkDetail(url, status_code, error)
                self.failed_link_details.append(failed_detail)
            self.last_update_time = time.time()
            return failed_detail

    def get_progress_percentage(self) -> float:
        if self.discovered_links == 0:
            return 0.0
        return (self.checked_links / self.discovered_links) * 100

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time

    def get_estimated_remaining_time(self) -> Optional[float]:
        if self.checked_links == 0:
            return None
        avg_time_per_link = self.get_elapsed_time() / self.checked_links
        remaining_links = self.discovered_links - self.checked_links
        if remaining_links <= 0:
            return 0.0
        return remaining_links * avg_time_per_link

    def to_snapshot(self) -> ProgressSnapshot:
        return ProgressSnapshot(
            discovered_pages=self.discovered_pages,
            processed_pages=self.processed_pages,
            discovered_links=self.discovered_links,
            checked_links=self.checked_links,
            failed_links=self.failed_links,
            current_page_url=self.current_page_url,
            current_link_url=self.current_link_url,
            progress_percentage=self.get_progress_percentage(),
            elapsed_seconds=self.get_elapsed_time(),
            estimated_remaining_seconds=self.get_estimated_remaining_time(),
            timestamp=time.time()
        )

@dataclass(frozen=True)
class ProgressSnapshot:
    discovered_pages: int
    processed_pages: int
    discovered_links: int
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
    update_interval_seconds: float = 1.0
    progress_bar_width: int = 20
    max_url_display_length: int = 80
    max_failures_display: int = 50
    enable_ansi_colors: bool = True
    fallback_to_newline_mode: bool = False
    show_current_url: bool = True
    show_eta: bool = True

class ProgressRenderer:
    """進度渲染器"""
    
    def __init__(self, config: ProgressDisplayConfig):
        self.config = config
        self.supports_ansi = self._detect_ansi_support()
    
    def _detect_ansi_support(self) -> bool:
        """檢測終端機是否支援 ANSI 跳脫序列"""
        if self.config.fallback_to_newline_mode:
            return False
        if not sys.stdout.isatty():
            return False
        if os.getenv('TERM') == 'dumb':
            return False
        if sys.platform == 'win32':
            import platform
            version = platform.version().split('.')
            build = int(version[2]) if len(version) > 2 else 0
            return build >= 10586  # Windows 10 build 10586+
        return True
    
    def render_progress_line(self, snapshot: ProgressSnapshot) -> str:
        """渲染單行進度資訊"""
        bar = self._format_progress_bar(
            snapshot.progress_percentage, 
            self.config.progress_bar_width
        )
        
        parts = [
            f"{bar} {snapshot.progress_percentage:.0f}%",
            f"已檢查: {snapshot.checked_links}/{snapshot.discovered_links}",
            f"失效: {snapshot.failed_links}",
            f"用時: {self._format_time(snapshot.elapsed_seconds)}"
        ]
        
        if self.config.show_eta and snapshot.estimated_remaining_seconds is not None:
            parts.append(f"剩餘: ~{self._format_time(snapshot.estimated_remaining_seconds)}")
        
        line = " | ".join(parts)
        
        if self.config.show_current_url and snapshot.current_link_url:
            url = self._truncate_url(snapshot.current_link_url, self.config.max_url_display_length)
            line = f"正在檢查: {url}\n{line}"
        
        return line
    
    def _format_progress_bar(self, percentage: float, width: int) -> str:
        """生成進度條字符串"""
        filled = int(width * percentage / 100)
        bar = '=' * filled + '>' + ' ' * (width - filled - 1)
        return f"[{bar}]"
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間顯示（MM:SS）"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _truncate_url(self, url: str, max_length: int) -> str:
        """截斷過長 URL"""
        if len(url) <= max_length:
            return url
        return url[:max_length-3] + "..."
    
    def render_failed_link_notification(self, detail: FailedLinkDetail) -> str:
        """渲染失效連結通知"""
        if detail.status_code:
            return f"❌ 失效連結: {detail.url} (HTTP {detail.status_code})"
        else:
            return f"⏱ 失效連結: {detail.url} ({detail.error_message})"
    
    def render_final_summary(self, snapshot: ProgressSnapshot) -> str:
        """渲染最終摘要"""
        return f"""
檢查完成！
----------
總耗時: {self._format_time(snapshot.elapsed_seconds)}
總連結數: {snapshot.discovered_links}
有效連結: {snapshot.checked_links - snapshot.failed_links}
失效連結: {snapshot.failed_links}
----------
"""

async def display_progress_loop(
    state: ProgressState, 
    renderer: ProgressRenderer, 
    config: ProgressDisplayConfig
) -> None:
    """定時進度顯示循環"""
    while True:
        await asyncio.sleep(config.update_interval_seconds)
        snapshot = state.to_snapshot()
        line = renderer.render_progress_line(snapshot)
        
        if renderer.supports_ansi:
            # 使用 ANSI 跳脫序列覆寫當前行
            sys.stdout.write(f"\r\033[K{line}")
            sys.stdout.flush()
        else:
            # 降級為追加新行模式
            print(line)
```

---

### 2. 修改 `src/link_checker.py`

```python
async def main() -> None:
    parser = argparse.ArgumentParser(description='連結檢查工具 (繁體中文)')
    # ... 現有參數 ...
    
    # 新增進度相關參數
    parser.add_argument('--progress', type=lambda s: s.lower() in ('true','1','yes'), default=True, help='是否啟用進度顯示')
    parser.add_argument('--progress-interval', type=float, default=1.0, help='進度更新間隔（秒）')
    parser.add_argument('--no-ansi', action='store_true', help='禁用 ANSI 跳脫序列')
    
    args = parser.parse_args()
    
    # 初始化進度追蹤
    from lib.progress import ProgressState, ProgressRenderer, ProgressDisplayConfig, display_progress_loop
    
    progress_config = ProgressDisplayConfig(
        update_interval_seconds=args.progress_interval,
        fallback_to_newline_mode=args.no_ansi
    )
    progress_state = ProgressState()
    progress_renderer = ProgressRenderer(progress_config)
    
    # 啟動進度顯示任務
    if args.progress:
        progress_task = asyncio.create_task(
            display_progress_loop(progress_state, progress_renderer, progress_config)
        )
    
    # ... 執行連結檢查 ...
    
    # 顯示最終摘要
    final_snapshot = progress_state.to_snapshot()
    print(progress_renderer.render_final_summary(final_snapshot))
```

---

### 3. 修改 `src/lib/fetcher.py`

```python
async def collect_link_statuses(
    links: List[str], 
    cfg: Config,
    progress_state: Optional[ProgressState] = None  # 新增進度回調
) -> List[dict]:
    """並發檢查連結狀態"""
    results = []
    
    # 更新已發現連結數
    if progress_state:
        progress_state.discovered_links = len(links)
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            check_single_link(session, url, cfg, progress_state) 
            for url in links
        ]
        results = await asyncio.gather(*tasks)
    
    return results

async def check_single_link(
    session: aiohttp.ClientSession, 
    url: str, 
    cfg: Config,
    progress_state: Optional[ProgressState] = None
) -> dict:
    """檢查單個連結狀態"""
    # ... 現有檢查邏輯 ...
    
    # 更新進度狀態
    if progress_state:
        failed_detail = await progress_state.update_checked_link(url, status_code, error_msg)
        
        # 若失效，立即顯示通知
        if failed_detail:
            from lib.progress import ProgressRenderer, ProgressDisplayConfig
            renderer = ProgressRenderer(ProgressDisplayConfig())
            notification = renderer.render_failed_link_notification(failed_detail)
            print(f"\n{notification}")
    
    return result
```

---

## 開發流程建議

### 1. TDD（測試驅動開發）

先撰寫測試，再實作功能：

```python
# tests/test_progress.py
@pytest.mark.asyncio
async def test_progress_state_basic():
    state = ProgressState()
    state.discovered_links = 10
    
    await state.update_checked_link("https://example.com/1", 200, None)
    assert state.checked_links == 1
    assert state.failed_links == 0
    assert state.get_progress_percentage() == 10.0

@pytest.mark.asyncio
async def test_progress_state_failed_link():
    state = ProgressState()
    state.discovered_links = 10
    
    failed_detail = await state.update_checked_link("https://example.com/broken", 404, "Not Found")
    assert failed_detail is not None
    assert state.failed_links == 1
    assert len(state.failed_link_details) == 1
```

### 2. 漸進式整合

1. 先完成 `ProgressState` 並測試
2. 再實作 `ProgressRenderer` 並測試
3. 最後整合至主程式

### 3. 手動測試場景

```bash
# 基本功能測試
python src/link_checker.py --url https://www.entiebank.com.tw/entie/home

# 禁用 ANSI 測試
python src/link_checker.py --url https://example.com --no-ansi

# 高頻更新測試
python src/link_checker.py --url https://example.com --progress-interval 0.5

# 中途取消測試（按 Ctrl+C）
python src/link_checker.py --url https://example.com
^C
# 應顯示部分統計並優雅退出
```

---

## 常見問題與解決方案

### Q1: 進度顯示閃爍或錯位？

**原因**：未正確清除行尾字符。  
**解決**：使用 `\033[K` ANSI 跳脫碼清除行尾。

```python
sys.stdout.write(f"\r\033[K{line}")  # \033[K 清除游標右側至行尾
```

---

### Q2: 進度更新影響檢查效能？

**原因**：更新頻率過高或 I/O 阻塞。  
**解決**：限制更新頻率至 1 秒，使用非阻塞寫入。

```python
await asyncio.sleep(1.0)  # 每秒更新一次
sys.stdout.flush()        # 強制刷新緩衝區
```

---

### Q3: Windows 終端機不支援 ANSI？

**原因**：Windows 10 以下版本預設禁用 ANSI。  
**解決**：自動檢測並降級為追加新行模式。

```python
if sys.platform == 'win32':
    version_info = platform.version().split('.')
    build = int(version_info[2])
    if build < 10586:
        config.fallback_to_newline_mode = True
```

---

### Q4: 中途取消後資料遺失？

**原因**：未捕捉 `KeyboardInterrupt`。  
**解決**：在主程式中捕捉異常並保存部分結果。

```python
try:
    await run_link_checks()
except KeyboardInterrupt:
    logger.warning("檢查被用戶中斷")
    write_csv(partial_results)
    print(progress_renderer.render_final_summary(progress_state.to_snapshot()))
    sys.exit(130)
```

---

## 效能優化建議

1. **減少字符串拼接**：使用 f-string 而非多次 `+` 操作
2. **批量輸出**：累積多個更新後一次性輸出
3. **懶惰計算**：僅在顯示時計算百分比和 ETA
4. **異步 I/O**：使用 `sys.stdout.write()` 而非 `print()`，避免額外刷新

---

## 驗收檢查清單

完成實作後，驗證以下項目：

- [x] 進度資訊更新延遲 ≤ 1 秒（SC-008）
- [x] 統計數據準確性 100%（SC-009）
- [x] 進度百分比計算準確（SC-010）
- [x] 用戶能全程看到進度更新（SC-011）
- [x] 預估剩餘時間誤差 ≤ 30%（SC-012）
- [x] 進度顯示開銷 ≤ 5%（SC-013）
- [x] 失效連結即時通知（FR-021）
- [x] 支援優雅關閉（邊界情況）
- [x] ANSI 不支援時正確降級（邊界情況）

### 實作驗證快照（2026-03-07）

- 測試結果：`8 passed`（`pytest -q`）
- 目標站效能比較：進度開銷約 `1.04%`（見 `reports/progress_benchmark.md`）
- 已完成檔案：`src/link_checker.py`、`src/lib/progress.py`、`src/lib/fetcher.py`、`src/lib/config.py`、`src/lib/reporter.py`、`src/lib/playwright_adapter.py`

---

## 後續步驟

完成實作後，建議：

1. 執行完整測試套組：`pytest tests/`
2. 手動測試各種場景（大型網站、失效連結、中途取消）
3. 更新 `README.md`，新增進度顯示使用說明
4. 提交 Pull Request，附上測試結果和執行截圖
5. 執行效能基準測試，驗證進度顯示開銷 ≤ 5%

---

**實作時間預估**：總計 8-11 小時（包含測試與文檔）

**Phase 1 Quickstart 完成**。開發者可依循本指南快速實作即時進度可視化功能。
