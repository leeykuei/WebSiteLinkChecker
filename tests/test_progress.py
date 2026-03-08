from pathlib import Path
import asyncio
import sys

# 將 src 加入 sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from lib.progress import ProgressDisplayConfig, ProgressRenderer, ProgressState


def test_progress_state_successful_link_updates_percentage():
    async def run_case():
        state = ProgressState()
        await state.update_discovered_links(10)

        detail = await state.update_checked_link(
            url='https://example.com/ok',
            status_code=200,
            error_message=None,
        )
        snapshot = await state.snapshot()

        assert detail is None
        assert snapshot.checked_links == 1
        assert snapshot.failed_links == 0
        assert snapshot.progress_percentage == 10.0

    asyncio.run(run_case())


def test_progress_state_failed_link_records_detail():
    async def run_case():
        state = ProgressState()
        await state.update_discovered_links(5)

        detail = await state.update_checked_link(
            url='https://example.com/404',
            status_code=404,
            error_message='Not Found',
            source_page='https://example.com',
        )
        snapshot = await state.snapshot()

        assert detail is not None
        assert snapshot.checked_links == 1
        assert snapshot.failed_links == 1
        assert len(state.failed_link_details) == 1
        assert state.failed_link_details[0].source_page == 'https://example.com'

    asyncio.run(run_case())


def test_progress_renderer_line_contains_key_fields():
    async def run_case():
        state = ProgressState()
        await state.update_discovered_pages(1)
        await state.update_processed_pages(1)
        await state.update_discovered_links(4)
        await state.update_checked_link('https://example.com/1', 200, None)

        config = ProgressDisplayConfig(progress_bar_width=10)
        renderer = ProgressRenderer(config)
        snapshot = await state.snapshot()
        line = renderer.render_progress_line(snapshot)

        assert line.startswith('[')
        assert '%' in line
        assert '連結: 1/4' in line
        assert '失效: 0' in line

    asyncio.run(run_case())


def test_renderer_disables_overwrite_when_not_tty():
    class FakeStream:
        def isatty(self):
            return False

        def write(self, text):
            return len(text)

        def flush(self):
            return None

    renderer = ProgressRenderer(ProgressDisplayConfig(), stream=FakeStream())
    assert renderer.supports_overwrite is False
