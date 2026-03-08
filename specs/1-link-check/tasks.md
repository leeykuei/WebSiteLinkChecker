# Tasks for Feature 1 - Link Check

This document translates the specification, research, and plan into a phased set of implementation tasks.  Phases are **setup**, **foundational**, one phase per user story, and **polish**.  Each task includes dependencies, opportunities for parallel work, test criteria, and implementation notes.

---

## 📦 Phase: Setup

**Goal**: bootstrap environment and project structure before coding.

_Status: all setup tasks complete; environment prepared and documentation copied._

1. **Configure Python environment**
   - Create and activate a virtualenv/conda as described in quickstart.
   - Install dependencies from `requirements.txt`（含 `openpyxl`）。
   - Run `playwright install` to ensure browsers are available (non-blocking).  
   - **Dependencies**: none.
   - **Tests**: `python -c "import aiohttp, asyncio, playwright, openpyxl"` succeeds.
   - **Parallel**: independent from any development.

2. **Initialize repository tooling**
   - Add pre-commit/flake8/black if not already present (optional).
   - Ensure `src/` and `tests/` packages are importable by adding `__init__.py` if needed.
   - **Dependencies**: environment configured.
   - **Tests**: `pytest` runs with no tests but returns zero exit.

3. **Copy spec artifacts into docs**
   - Confirm `specs/1-link-check/{spec,plan,data-model,quickstart,contracts,research}.md` exist (done).
   - Create this `tasks.md` file.
   - **Dependencies**: none.
   - **Tests**: manual review.

---

## 🧱 Phase: Foundational

**Goal**: establish core utilities and data models used by all stories.

_Status: configuration, models, logging, parser, and fetcher skeletons implemented and tested._

1. **Define data models & config structures**
   - Implement `src/lib/config.py` with `Configuration` dataclass/pydantic model containing timeout, concurrency, retries, use_playwright, report_type.
   - Implement `src/lib/models.py` (or within config) with `Link` and `CheckResult` dataclasses matching `data-model.md`.
   - Add validation rules (e.g. absolute URL parsing).
   - **Dependencies**: none
   - **Parallel**: testers can start writing unit tests for validation.
   - **Tests**: unit tests for model instantiation, URL parsing, invalid data raises errors.

2. **Logging setup**
   - In `src/lib/config.py` or a dedicated `logger.py`, configure `logging` to output structured JSON to console/file.
   - Ensure different levels available and environment variable to change level.
   - **Dependencies**: none.
   - **Tests**: logger outputs valid JSON lines; level filtering works.

3. **Utility for URL normalization**
   - Implement helper to resolve relative URLs against base (use `yarl.URL` or `urllib.parse.urljoin`).
   - **Tests**: unit tests covering relative, absolute, fragments.

4. **HTTP client session wrapper**
   - Create `lib/fetcher.py` skeleton with asynchronous session management, concurrency control, retry/backoff logic stubbed.
   - **Dependencies**: config models.
   - **Tests**: stubbed tests verifying session created with correct limits; retry logic can be exercised with a local aiohttp test server.

5. **Parser skeleton**
   - `lib/parser.py` with functions `extract_links(html, base_url)` and an async variant for Playwright to fetch page then parse.
   - **Dependencies**: config models, URL utils.
   - **Tests**: static HTML samples; Playwright tests can be simple mock or real page if env.


---

## 🔗 Phase: User Story 1 – Basic static link validation (P1)

_Status: core static-check engine implemented; CLI integration done; tests passing._

**Goal**: fetch a page, parse `<a>` links, check each link’s HTTP status.

1. **CLI argument parsing**
   - Update `src/link_checker.py` to accept command‑line flags per `contracts/cli.md` (use argparse).
   - Build `Configuration` instance from args.
   - **Dependencies**: config model.
   - **Tests**: unit tests for CLI parsing; invalid args produce error.

2. **Static page fetch & link extraction**
   - In `link_checker.py`, perform a simple GET request for the target URL using aiohttp; feed result to `parser.extract_links`.
   - Make sure to follow redirects (aiohttp default does).
   - **Dependencies**: fetcher and parser utilities.
   - **Tests**: integration test against a static HTML served by `tests/fixtures` using `aiohttp` test server. Verify extracted links list matches expected.

3. **Concurrent link checking engine**
   - Complete `fetcher.check_links(urls, config)` returning list of `Link` results with status, elapsed, error.
   - Use asyncio.Semaphore or aiohttp.TCPConnector limit to enforce concurrency; implement retries with exponential backoff.
   - Handle timeouts and exceptions, populating `Link.error` and `status_code` correctly.
   - **Dependencies**: URL util, config, models.
   - **Tests**: use a local test server that can return 200, 404, 500, delay responses; verify concurrency limit, retries, timeouts.

4. **Aggregate results into CheckResult**
   - After all links checked, build `CheckResult` with counts and timestamps.
   - **Dependencies**: models.
   - **Tests**: assert fields correct given controlled inputs.

5. **Excel reporting**
   - Implement `lib/reporter.py` with `write_excel()` to output `.xlsx` with 11 fixed columns.
   - Include conditional `Page URL` omission when `Page URL == Link URL`.
   - Keep `report_type == 'failures'` filtering behavior.
   - **Dependencies**: models, `openpyxl`.
   - **Tests**: generate Excel from sample result; read back and assert rows, columns, and conditional blanking.

6. **Tie into CLI main**
   - Wire steps: parse CLI -> fetch page -> extract links -> check links -> aggregate -> report -> log summary.
   - **Dependencies**: previous tasks.
   - **Tests**: end‑to‑end test against a simple site fixture verifying Excel output and exit code 0.

**Parallel Opportunities**:
- While one developer builds the fetcher engine, another can flesh out parser and the Excel reporter.
- Test cases can be written concurrently to the implementations since contracts are defined.

**Independent Test Criteria**:
- Parser and fetcher modules should be unit-testable in isolation with fakes.
- CLI integration tests should rely only on local servers and fixtures.

---

## 🛠️ Phase: User Story 2 – Dynamic menu link detection (P2)

_Status: Playwright adapter implemented and integrated; dynamic links detected in tests._

**Goal**: when requested, load page in headless browser and extract links after JS execution.

1. **Implement Playwright adapter**
   - Add `lib/playwright_adapter.py` with async function `crawl_with_playwright(url, timeout)` that launches browser, navigates, waits for `networkidle`, then returns page HTML or list of `href`s via `page.evaluate`.
   - Add retry/backoff for navigation failures and optional headful flag for debugging.
   - **Dependencies**: config, parser.
   - **Tests**: simple test using a local html file with JS injecting links; run adapter and ensure links returned. (May require the test to skip if Playwright not installed or slow). Keep tests optional (mark xfail).

2. **Integrate into extraction path**
   - In parser or link_checker main, decide based on `use_playwright` config whether to call the adapter or fetch raw HTML.
   - **Dependencies**: CLI config.
   - **Tests**: new integration test where `--use-playwright` true; fixture page has dynamic link; ensure it's captured.

3. **Document dependency**
   - Update quickstart and README to note Playwright installation (`playwright install`) and performance considerations.
   - **Dependencies**: none.
   - **Tests**: manual review.

**Parallel Opportunities**:
- Playwright adapter development can occur alongside improvements to fetcher engine; tests can be added after the adapter stub exists.

**Independent Test Criteria**:
- The adapter should be testable separately by mocking Playwright, or by using a simple static HTML file with embedded script.

---

## 📊 Phase: User Story 3 – Excel report generation (P2)

_Status: reporter supports full output; filtering stub exists; tested._

(Partially covered in Story 1 but polish here.)

1. **Enhance reporter**
   - Support `report_type` filtering and stable Excel schema output.
   - **Tests**: verify filtering; load output with `openpyxl` to confirm columns and values.

2. **CLI flag parsing for report type & output path**
   - Already included earlier; add validation.
   - **Tests**: passing invalid value raises error.

3. **Edge cases**
   - Handle case where no links found -> still create empty Excel with header.
   - Handle duplicate URLs gracefully (still list each occurrence).
   - **Tests**: specific scenarios.

**Parallel Opportunities**:
- Reporter improvements and CLI flag validation can be done by a different engineer while fetcher/Playwright tasks progress.

---

## ✨ Phase: Polish & Additional Enhancements

_Status: documentation updated, README expanded, tests added. Additional polish remaining optionally._

**Goal**: harden, document, and prepare release.

1. **Logging improvements**
   - Add contextual info (page_url, link index) to logs.
   - Add log rotation or file configuration.
   - **Tests**: integration test checking log file lines contain expected fields.

2. **Error handling & user messages**
   - Validate URL format early and provide helpful CLI error.
   - Catch uncaught exceptions in main and exit with non-zero status.
   - **Tests**: run CLI with invalid URL and confirm stderr message & exit 2.

3. **Performance tuning**
   - Benchmark with 100‑link page to meet SC-001; adjust default concurrency or connection pool settings as needed.
   - Add option to adjust delay between requests for rate‑limit.
   - **Tests**: simple timing test and concurrency verification.

4. **Documentation**
   - Flesh out README with installation, examples, assumptions, and mention robots/ethical usage note.
   - Add comments & docstrings in code, especially for exported functions.
   - **Tests**: manual review; ensure README has quickstart steps.
   - [X] Sync `spec.md`, `quickstart.md`, `plan.md`, `tasks.md`, `contracts/cli.md` to Excel output and current report schema.

5. **Packaging & releases**
   - Optionally add `setup.py` or `pyproject.toml` if distributing as package.
   - Prepare a version bump and changelog.
   - **Tests**: `pip install -e .` works; CLI entry point function executes.

6. **Additional tests**
   - Add tests for edge cases: redirect handling, relative URL resolution, self-referential links.
   - Add smoke test for Playwright skip when not installed.

**Parallel Opportunities**:
- Documentation work, packaging, and log improvements can be executed simultaneously since they don't rely heavily on core logic.

---

## ✅ Summary

- **Phases**: 6 total (setup, foundational, 3 story phases, polish)
- **Tasks**: ~25 distinct tasks defined above; may expand during implementation.
- **File**: `specs/1-link-check/tasks.md`

This breakdown should guide development and testing for the link-checker feature.  Each task is scoped for independent verification and highlights points where team members can work concurrently.  Adjustments may be made as new information arises or requirements shift.