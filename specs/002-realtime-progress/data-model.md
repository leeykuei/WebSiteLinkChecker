# Data Model: 即時檢查進度可視化

**Feature**: 002-realtime-progress  
**Date**: 2026-03-07  
**Status**: Phase 1 Complete

## 概述

本文件定義即時進度可視化功能所需的核心資料結構，包括進度狀態追蹤、統計資訊計算、顯示格式化等實體。所有實體設計遵循 Python dataclass 規範，支援類型提示，確保程式碼可讀性與類型安全。

---

## 1. ProgressState（進度狀態追蹤器）

**用途**：中央狀態物件，追蹤整個連結檢查過程的即時進度資訊。

**屬性**：

| 欄位名稱 | 類型 | 必填 | 預設值 | 說明 |
|---------|------|-----|-------|------|
| `discovered_pages` | `int` | ✅ | `0` | 已發現的頁面總數 |
| `processed_pages` | `int` | ✅ | `0` | 已處理完成的頁面數量 |
| `discovered_links` | `int` | ✅ | `0` | 已發現的連結總數 |
| `checked_links` | `int` | ✅ | `0` | 已檢查完成的連結數量 |
| `failed_links` | `int` | ✅ | `0` | 失效連結數量（HTTP非2xx） |
| `current_page_url` | `str` | ✅ | `""` | 目前正在掃描的頁面 URL |
| `current_link_url` | `str` | ✅ | `""` | 目前正在檢查的連結 URL |
| `start_time` | `float` | ✅ | `time.time()` | 檢查開始時間（Unix timestamp） |
| `last_update_time` | `float` | ✅ | `time.time()` | 最後一次更新時間 |
| `failed_link_details` | `List[FailedLinkDetail]` | ✅ | `[]` | 失效連結詳細資訊列表 |
| `_lock` | `asyncio.Lock` | ✅ | `asyncio.Lock()` | 確保多協程安全的鎖 |

**方法**：

```python
async def update_discovered_pages(count: int = 1) -> None:
    """增加已發現頁面計數"""

async def update_processed_pages(count: int = 1) -> None:
    """增加已處理頁面計數"""

async def update_discovered_links(count: int) -> None:
    """增加已發現連結計數"""

async def update_checked_link(url: str, status_code: int | None, error: str | None) -> None:
    """更新已檢查連結，記錄失效連結"""

async def set_current_page(url: str) -> None:
    """設定目前正在掃描的頁面"""

async def set_current_link(url: str) -> None:
    """設定目前正在檢查的連結"""

def get_progress_percentage() -> float:
    """計算進度百分比（已檢查/已發現）"""

def get_elapsed_time() -> float:
    """計算已執行時間（秒）"""

def get_estimated_remaining_time() -> float | None:
    """預估剩餘時間（秒），若無法預估返回 None"""

def to_snapshot() -> ProgressSnapshot:
    """生成當前狀態的快照（用於顯示）"""
```

**設計考量**：
- 使用 `asyncio.Lock` 確保多協程並發更新時的數據一致性
- 所有更新操作都是 `async` 方法，避免阻塞 event loop
- 統計資訊（百分比、剩餘時間）採用計算屬性，不預先儲存

**範例**：
```python
state = ProgressState()
await state.update_discovered_links(100)
await state.update_checked_link("https://example.com", 200, None)
percentage = state.get_progress_percentage()  # 1.0%
```

---

## 2. FailedLinkDetail（失效連結詳情）

**用途**：記錄每個失效連結的詳細資訊，用於即時通知和最終報表。

**屬性**：

| 欄位名稱 | 類型 | 必填 | 說明 |
|---------|------|-----|------|
| `url` | `str` | ✅ | 失效連結的 URL |
| `status_code` | `int \| None` | ✅ | HTTP 狀態碼（若失敗則為 None） |
| `error_message` | `str \| None` | ✅ | 錯誤訊息（如 timeout、DNS 失敗） |
| `source_page` | `str \| None` | ❌ | 發現此連結的來源頁面 URL |
| `timestamp` | `float` | ✅ | 檢查時間（Unix timestamp） |

**設計考量**：
- `status_code` 和 `error_message` 至少有一個非 None
- `source_page` 為可選，若追蹤來源頁面可填寫
- 支援序列化至 JSON 或 CSV 格式

**範例**：
```python
detail = FailedLinkDetail(
    url="https://example.com/broken",
    status_code=404,
    error_message="Not Found",
    source_page="https://example.com/home",
    timestamp=time.time()
)
```

---

## 3. ProgressSnapshot（進度快照）

**用途**：不可變的進度狀態快照，用於渲染顯示。避免在渲染過程中狀態被修改。

**屬性**：

| 欄位名稱 | 類型 | 必填 | 說明 |
|---------|------|-----|------|
| `discovered_pages` | `int` | ✅ | 已發現頁面數 |
| `processed_pages` | `int` | ✅ | 已處理頁面數 |
| `discovered_links` | `int` | ✅ | 已發現連結數 |
| `checked_links` | `int` | ✅ | 已檢查連結數 |
| `failed_links` | `int` | ✅ | 失效連結數 |
| `current_page_url` | `str` | ✅ | 目前掃描頁面 |
| `current_link_url` | `str` | ✅ | 目前檢查連結 |
| `progress_percentage` | `float` | ✅ | 進度百分比（0-100） |
| `elapsed_seconds` | `float` | ✅ | 已執行時間（秒） |
| `estimated_remaining_seconds` | `float \| None` | ✅ | 預估剩餘時間（秒），None 表示無法預估 |
| `timestamp` | `float` | ✅ | 快照時間戳 |

**設計考量**：
- 不可變（使用 `@dataclass(frozen=True)`）
- 包含所有顯示所需的已計算欄位，避免渲染時重複計算
- 輕量級，可頻繁創建

**範例**：
```python
snapshot = state.to_snapshot()
# snapshot 是不可變的，可安全傳遞給渲染函式
```

---

## 4. ProgressDisplayConfig（進度顯示配置）

**用途**：配置進度顯示的行為參數，如更新頻率、進度條寬度、降級模式等。

**屬性**：

| 欄位名稱 | 類型 | 必填 | 預設值 | 說明 |
|---------|------|-----|-------|------|
| `update_interval_seconds` | `float` | ✅ | `1.0` | 進度更新間隔（秒） |
| `progress_bar_width` | `int` | ✅ | `20` | 進度條字符寬度 |
| `max_url_display_length` | `int` | ✅ | `80` | URL 顯示最大長度（超過截斷） |
| `max_failures_display` | `int` | ✅ | `50` | 即時顯示失效連結的最大數量 |
| `enable_ansi_colors` | `bool` | ✅ | `True` | 是否啟用 ANSI 彩色輸出 |
| `fallback_to_newline_mode` | `bool` | ✅ | `False` | 是否降級為追加新行模式 |
| `show_current_url` | `bool` | ✅ | `True` | 是否顯示目前檢查的 URL |
| `show_eta` | `bool` | ✅ | `True` | 是否顯示預估剩餘時間 |

**設計考量**：
- 所有參數可透過命令列參數或配置檔案調整
- 支援自動降級（如檢測到不支援 ANSI 時設定 `fallback_to_newline_mode=True`）
- 提供合理預設值，符合多數使用場景

**範例**：
```python
config = ProgressDisplayConfig(
    update_interval_seconds=0.5,  # 更頻繁更新
    max_failures_display=20,       # 限制失效連結顯示數量
    enable_ansi_colors=False       # 禁用彩色輸出
)
```

---

## 5. ProgressRenderer（進度渲染器）

**用途**：負責將 `ProgressSnapshot` 渲染為終端機顯示字符串。

**方法**：

```python
def render_progress_line(snapshot: ProgressSnapshot, config: ProgressDisplayConfig) -> str:
    """渲染單行進度資訊（用於覆寫更新）"""

def render_failed_link_notification(detail: FailedLinkDetail) -> str:
    """渲染失效連結通知（追加新行）"""

def render_final_summary(snapshot: ProgressSnapshot) -> str:
    """渲染最終摘要資訊"""

def format_progress_bar(percentage: float, width: int) -> str:
    """生成進度條字符串，如 [=====>     ]"""

def format_time(seconds: float) -> str:
    """格式化時間顯示，如 01:23（MM:SS）"""

def truncate_url(url: str, max_length: int) -> str:
    """截斷過長 URL，保留前後部分"""
```

**設計考量**：
- 純函式設計，無副作用，易於測試
- 支援 ANSI 跳脫序列和純文字兩種模式
- 所有字符串使用繁體中文

**範例輸出**：
```
正在檢查: https://example.com/page1
[=========>          ] 45% | 已檢查: 450/1000 | 失效: 12 | 用時: 01:23 | 剩餘: ~01:50
```

---

## 6. LinkCheckResult（連結檢查結果）擴充

**用途**：現有的連結檢查結果實體，需擴充以支援進度追蹤。

**現有屬性**（保留）：
- `url`: `str` - 連結 URL
- `status_code`: `int | None` - HTTP 狀態碼
- `elapsed_ms`: `float` - 檢查耗時（毫秒）
- `error_message`: `str | None` - 錯誤訊息

**新增屬性**：
- `check_timestamp`: `float` - 檢查完成時間（Unix timestamp）
- `source_page_url`: `str | None` - 來源頁面 URL（可選）

**設計考量**：
- 保持向後相容，不破壞現有結構
- 新增欄位用於進度追蹤和報表增強

---

## 實體關係圖

```
┌─────────────────────────────────────────┐
│         ProgressState                   │
│  中央狀態管理器                          │
│                                         │
│  + discovered_pages: int                │
│  + checked_links: int                   │
│  + failed_link_details: List            │
│  + _lock: asyncio.Lock                  │
│                                         │
│  + update_checked_link()                │
│  + get_progress_percentage()            │
│  + to_snapshot()                        │
└───────────┬─────────────────────────────┘
            │
            │ 生成快照
            ▼
      ┌─────────────────┐
      │ ProgressSnapshot │
      │  不可變快照      │
      │                 │
      │  + checked_links│
      │  + percentage   │
      │  + elapsed_time │
      └────────┬────────┘
               │
               │ 傳遞給渲染器
               ▼
         ┌────────────────┐
         │ProgressRenderer│
         │   渲染器        │
         │                │
         │  + render()    │
         │  + format_bar()│
         └────────────────┘

┌─────────────────┐
│FailedLinkDetail │  ◄──┬── 儲存於 ProgressState.failed_link_details
│  失效連結詳情    │     │
│                 │     │
│  + url          │     │
│  + status_code  │     │
│  + error_message│     │
└─────────────────┘     │
                        │
                  用於即時通知與報表
```

---

## 資料流程

### 1. 連結檢查完成時

```
連結檢查完成
    ↓
fetcher.py 回調
    ↓
ProgressState.update_checked_link()
    ├─→ checked_links += 1
    ├─→ 若失效：failed_links += 1
    └─→ 若失效：failed_link_details.append(...)
    ↓
若失效：立即渲染並輸出失效通知
```

### 2. 定時進度顯示

```
每 1 秒定時任務
    ↓
ProgressState.to_snapshot()
    ↓
ProgressSnapshot（不可變）
    ↓
ProgressRenderer.render_progress_line()
    ↓
輸出至 stdout（覆寫前一行）
```

### 3. 檢查完成時

```
檢查完成
    ↓
ProgressState.to_snapshot()
    ↓
ProgressRenderer.render_final_summary()
    ↓
輸出最終摘要（追加新行）
```

---

## 類型定義（Python 類型提示）

```python
from dataclasses import dataclass, field
from typing import List, Optional
import asyncio
import time

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
    ) -> None:
        async with self._lock:
            self.checked_links += 1
            if status_code is None or not (200 <= status_code <= 299):
                self.failed_links += 1
                self.failed_link_details.append(
                    FailedLinkDetail(url, status_code, error)
                )
            self.last_update_time = time.time()

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

    def to_snapshot(self) -> 'ProgressSnapshot':
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
```

---

## 驗證與測試

### 單元測試

```python
@pytest.mark.asyncio
async def test_progress_state_update():
    state = ProgressState()
    state.discovered_links = 100
    await state.update_checked_link("https://example.com", 200, None)
    assert state.checked_links == 1
    assert state.failed_links == 0
    assert state.get_progress_percentage() == 1.0

@pytest.mark.asyncio
async def test_progress_state_failed_link():
    state = ProgressState()
    state.discovered_links = 100
    await state.update_checked_link("https://example.com/broken", 404, "Not Found")
    assert state.failed_links == 1
    assert len(state.failed_link_details) == 1
    assert state.failed_link_details[0].status_code == 404
```

### 集成測試

```python
@pytest.mark.asyncio
async def test_progress_display_integration():
    state = ProgressState()
    config = ProgressDisplayConfig()
    renderer = ProgressRenderer(config)
    
    # 模擬檢查過程
    state.discovered_links = 10
    for i in range(5):
        await state.update_checked_link(f"https://example.com/{i}", 200, None)
    
    snapshot = state.to_snapshot()
    progress_line = renderer.render_progress_line(snapshot)
    assert "50%" in progress_line
    assert "5/10" in progress_line
```

---

**Phase 1 Data Model 完成**。所有資料結構已明確定義，支援完整的進度追蹤與顯示功能。
