# Tasks: ?單?瑼Ｘ?脣漲?航???撘瑞?

**Input**: Design documents from `/specs/002-realtime-progress/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`

**Tests**: ?祈??潭?Ⅱ閬????啣神?芸??葫閰佗?TDD嚗??砌遙???桐誑?撖虫??蝡??嗥銝颯? 
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Every task includes an exact file path

## Path Conventions

- Single project layout: `src/`, `tests/` at repository root
- Feature docs: `specs/002-realtime-progress/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 撱箇??脣漲?航????賜??梁撉冽???詨???

- [x] T001 Create progress module scaffold with public class stubs in src/lib/progress.py
- [x] T002 Extend configuration dataclass with progress display options in src/lib/config.py
- [x] T003 [P] Add progress-related argparse option declarations and help text skeleton in src/link_checker.py
- [x] T004 [P] Add progress feature section placeholder for CLI usage in README.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 撱箇????user stories ?勗?靘陷??撅方?? 
**?? CRITICAL**: ?祇?畾萄???嚗???憪遙雿?user story 隞餃???

- [x] T005 Refactor result collection entrypoint to accept progress context/callback arguments in src/lib/fetcher.py
- [x] T006 [P] Consolidate aiohttp session lifecycle to shared ClientSession per run in src/lib/fetcher.py
- [x] T007 [P] Implement terminal capability detection and output mode switch (ANSI/newline) in src/lib/progress.py
- [x] T008 Implement centralized CLI parameter range validation for progress options in src/link_checker.py
- [x] T009 Wire ProgressDisplayConfig creation and lifecycle bootstrap in src/link_checker.py

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - ?箸?????撽? (Priority: P1) ? MVP Base

**Goal**: ?冽?????瑼Ｘ瘚?銝剜?靘鋡恍脣漲蝟餌絞瘨祥??蝣箇????? 
**Independent Test**: 隞?`--use-playwright false` 瑼Ｘ???嚗Ⅱ隤????仃???詻SV 頛詨?迤蝣綽?銝?脣漲????箔??飛??

### Implementation for User Story 1

- [x] T010 [US1] Set current page URL before static HTML parse flow in src/link_checker.py
- [x] T011 [P] [US1] Add discovered_links and checked_links update hooks during static link checking in src/lib/fetcher.py
- [x] T012 [P] [US1] Implement ProgressState counter update methods and snapshot conversion in src/lib/progress.py
- [x] T013 [US1] Extend link result payload with check timestamp and source page metadata in src/lib/fetcher.py
- [x] T014 [US1] Normalize extended result rows while preserving legacy CSV schema in src/lib/reporter.py
- [x] T015 [US1] Pass progress state through static collection pipeline orchestration in src/link_checker.py

**Checkpoint**: User Story 1 is independently functional and preserves existing static-check behavior.

---

## Phase 4: User Story 2 - ?單??脣漲?航???(Priority: P1)

**Goal**: ?函?蝡舀????單??脣漲璇絞閮?閮??URL ?仃????單???? 
**Independent Test**: ?瑁? `python src/link_checker.py --url <URL>`嚗Ⅱ隤?蝘?啜銵?撖怒仃???餈賢??啗???蝯?閬?銝剜??蝚血?閬??

### Implementation for User Story 2

- [x] T016 [US2] Implement ProgressSnapshot with dynamic percentage and ETA calculations in src/lib/progress.py
- [x] T017 [US2] Implement ProgressRenderer progress line formatting (bar, stats, URL truncation) in src/lib/progress.py
- [x] T018 [P] [US2] Implement failed-link notification and final summary rendering in src/lib/progress.py
- [x] T019 [US2] Add CLI flags (`--progress`, `--progress-interval`, `--progress-bar-width`, `--max-failures-display`, `--no-ansi`, `--show-current-url`, `--show-eta`) in src/link_checker.py
- [x] T020 [US2] Add async display loop for periodic single-line progress overwrite in src/link_checker.py
- [x] T021 [US2] Trigger immediate newline notifications for failed links via callback plumbing in src/lib/fetcher.py
- [x] T022 [US2] Implement graceful Ctrl+C handling with partial summary and exit code 130 in src/link_checker.py

**Checkpoint**: User Story 2 provides full real-time progress visualization without breaking link checking throughput.

---

## Phase 5: User Story 3 - ??????瑼Ｘ葫 (Priority: P2)

**Goal**: ??Playwright ??璅∪?銝雁?脣漲?航????湔扯??航炊?瘚??? 
**Independent Test**: ?瑁? `--use-playwright true` 撠????Ｘ炎?伐?蝣箄??舫＊蝷粹脣漲銝血 Playwright 憭望??迤蝣箏????璅∪???

### Implementation for User Story 3

- [x] T023 [US3] Update Playwright branch to feed current page and discovered link counts into progress state in src/link_checker.py
- [x] T024 [P] [US3] Normalize Playwright timeout/runtime errors for consistent progress and logging output in src/lib/playwright_adapter.py
- [x] T025 [US3] Implement progress state transitions for Playwright-to-static fallback path in src/link_checker.py
- [x] T026 [US3] Ensure dynamic link merge is deduplicated before progress percentage recalculation in src/link_checker.py

**Checkpoint**: User Story 3 works independently in dynamic mode and degrades gracefully.

---

## Phase 6: User Story 4 - CSV ?梯”?? (Priority: P2)

**Goal**: 蝣箔??脣漲????CSV 頛詨隞雁??UTF-8??雿??渲? failures ?蕪甇?Ⅱ?? 
**Independent Test**: ?隞?`--report-type all` ??`--report-type failures` ?瑁?嚗炎??CSV ?批捆摰?楊蝣潭迤蝣箔???蝡舫脣漲頛詨鈭?撟脫??

### Implementation for User Story 4

- [x] T027 [US4] Preserve UTF-8 CSV writing while supporting progress-enabled filtered/full outputs in src/lib/reporter.py
- [x] T028 [P] [US4] Apply report-type filtering after progress finalization to keep summary counts consistent in src/link_checker.py
- [x] T029 [US4] Append final run summary fields to logging context before CSV write in src/link_checker.py
- [x] T030 [US4] Ensure non-TTY/redirection auto-disables overwrite mode while retaining CSV generation in src/lib/progress.py

**Checkpoint**: User Story 4 independently delivers stable report output with progress mode enabled or disabled.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 頝冽?鈭??湔扼?隞嗅??湔扯??撽???

- [x] T031 [P] Document all new progress CLI options and examples in specs/002-realtime-progress/contracts/cli.md
- [x] T032 [P] Finalize user-facing progress usage and fallback guidance in README.md
- [x] T033 Benchmark progress rendering overhead and record findings in reports/progress_benchmark.md
- [x] T034 Validate quickstart scenarios and update implementation checkpoints in specs/002-realtime-progress/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: depends on Phase 1; blocks all stories
- **Phase 3-6 (User Stories)**: depend on Phase 2 completion
- **Phase 7 (Polish)**: depends on all selected stories being complete

### User Story Dependencies

- **US1 (P1)**: starts after Foundational; no dependency on other stories
- **US2 (P1)**: starts after US1 provides stable progress data hooks
- **US3 (P2)**: starts after US1; integrates with US2 renderer/output behavior
- **US4 (P2)**: starts after US1; can proceed in parallel with US3 once US2 output flow is stable

### Recommended Story Completion Order

1. US1 (stabilize static pipeline and progress data source)
2. US2 (deliver real-time visualization feature)
3. US3 and US4 (parallelizable P2 stories)

---

## Parallel Opportunities

### User Story 1

```bash
T011 [US1] in src/lib/fetcher.py
T012 [US1] in src/lib/progress.py
```

### User Story 2

```bash
T018 [US2] in src/lib/progress.py
T019 [US2] in src/link_checker.py
```

### User Story 3

```bash
T024 [US3] in src/lib/playwright_adapter.py
T026 [US3] in src/link_checker.py
```

### User Story 4

```bash
T027 [US4] in src/lib/reporter.py
T028 [US4] in src/link_checker.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational)
3. Complete Phase 3 (US1)
4. Complete Phase 4 (US2)
5. Validate real-time progress on static mode before moving to P2 stories

### Incremental Delivery

1. Deliver US1 + US2 as primary feature increment
2. Add US3 (dynamic mode parity)
3. Add US4 (report stability and filtering parity)
4. Run Phase 7 polish and performance validation

### Suggested MVP Scope

- **For this enhancement branch**: Phase 1 + Phase 2 + US1 + US2
- Rationale: feature value is realized when progress visualization is available on baseline static checks

---

## Notes

- `[P]` tasks are parallelizable only when they touch different files and have no unmet dependency
- 瘥?user story ?賣??函?撽璅?嚗?桃瞍內??霅?
- 隞餃??膩???急?蝣箸?獢楝敺??舐?乩漱??LLM/??銵?
