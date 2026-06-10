# Code Review — AccountReportingWebapp & AccountReporting

Review date: 2026-06-10. Scope: the Dash webapp (`AccountReportingWebapp`) and the `bkanalysis` package (`AccountReporting`). Findings are grouped by repo and by theme: bugs, robustness, performance, and general improvements. Line numbers refer to the current state of each repo.

## Top findings (prioritized)

| # | Where | What |
|---|-------|------|
| 1 [DONE] | webapp `app_initialisation.py:15` | `data_path` used before assignment → `NameError` instead of the intended error message |
| 2 [DONE] | webapp `tabs.py:12` | `get_color` has a duplicated condition: negative values can never get `text-danger` |
| 3 [open — see body for why it matters] | package `process.py:86` | `Process.__del__` silently rewrites all mapping CSVs on garbage collection; `save_on_exit` config key is ignored. Why it's bad: `__del__` fires at unpredictable times (or not at all), and it saves even when you only *read* data — so an interrupted run can persist half-built mappings and clobber your hand-maintained CSVs, with no way to opt out. Detailed scenario in the body. |
| 4 [FIXED] | package `salary.py:88` | `.loc[prev_year_end]` raises `KeyError` when there is no salary in December of the previous year → Tab 1 crashes for early years. Fixed with `try/except KeyError` (carried-over salary defaults to 0) in both `Salary` and `SalaryLegacy`. |
| 5 [FIXED] | package `figure_manager.py:341` | `categorised_flows.drop("Salary")` raises `KeyError` for years without salary income. Fixed with `errors="ignore"`; the `loc["Others"]` lookup now uses `.get("Others", 0.0)`. |
| 6 [FIXED] | webapp `callbacks.py:156` | Saving-rate gauge computed `month - 1`/`month - 2`, which is `0` or `-1` in January/February. Fixed with a `previous_month(year, month)` helper that wraps to December of the prior year; `get_saving_ratio` now also returns NaN instead of dividing by zero when a month has no income. |
| 7 | package `transformation_manager_cache.py:56` | Cache class rejects the webapp's Dec-31→Dec-31 date ranges (`start.year != end.year`) — likely why `USE_TRANSFORMATION_MANAGER_CACHE` is off |
| 8 [FIXED] | package `market_manager.py:86-88` | FX frame was duplicated once per currency (loop variable unused). Fixed: the FX rows are now selected once. Output is unchanged (the duplicates were dropped downstream); the build is just leaner and no longer crashes when all prices are already in the reference currency. |
| 9 [reviewed — agreed, by design] | package `process_helper.py:36,55,70` | The `input()` prompts are the intended interactive workflow for categorising new memos — not a bug. Reclassified as a design note: it only becomes a problem if `load_data_from_disk` is ever run unattended (cron/Docker), where an unmapped memo raises `EOFError`. An optional non-interactive mode remains a nice-to-have, not a fix. |
| 10 [explained — see Performance section] | both | Heavy recomputation per callback — `get_values_by_asset`/`get_flow_values` re-merge the full history on every tab refresh. Fix: cache results inside `TransformationManager` in a dict keyed by the call arguments, since the underlying data never changes after startup. Concrete recipe in the package Performance section. |

### Regression tests

Each fix above is covered by one targeted test:

| Fix | Test |
|-----|------|
| #4 `Salary` missing previous December | package `tests/unit/test_salary.py::TestSalary::test_no_salary_in_previous_december` |
| #4 `SalaryLegacy` missing previous December | package `tests/unit/test_salary.py::TestSalaryLegacy::test_no_salary_in_previous_december` |
| #5 waterfall without `Salary`/`Others` | package `tests/unit/test_figure_manager.py::test_waterfall_without_salary_or_others_categories` |
| #6 `get_saving_ratio` with no income → NaN | package `tests/unit/test_figure_manager.py::test_get_saving_ratio_without_income_returns_nan` |
| #6 January month wrap | webapp `test/test_callbacks.py::test_previous_month_wraps_to_previous_december` (`previous_month` was lifted to module level in `callbacks.py` to make it testable) |
| #8 `load_prices` FX frame | package `tests/unit/test_managers.py::TestMarketManager::test_load_prices_with_ref_currency_only` |

Writing the `load_prices` test surfaced an additional bug: under pandas 3 (which the package test venv runs), `groupby(...).apply(...)` no longer includes the grouping column, so the price-reindexing step in `market_manager.load_prices` dropped `AssetMapped` and crashed. Fixed by iterating the groups explicitly (`pd.concat([... for name, group in df.groupby(...)])`), which behaves identically on pandas 2 and 3.

---

## AccountReportingWebapp

### Bugs

- **`app_initialisation.py:15` — `data_path` referenced before assignment.** The `raise OSError(f"no config found in {os.path.abspath(data_path)}")` line runs before `data_path` is defined (line 17), so a missing config produces a confusing `NameError` instead of the intended message. The message should reference `ch.source` (the config path), not the data path. Move the `data_path = os.getenv(...)` line up and fix the message.

- **`tabs.py:12` — `get_color` never returns `text-danger`.**
  ```python
  return "text-success" if v > 0 else "text-danger" if v > 0 else "text-warning"
  ```
  The second condition repeats `v > 0`, so negative values fall through to `text-warning`. The YoY-change and capital-gain cards therefore show warning-yellow instead of red for losses. Should be `... else "text-danger" if v < 0 else "text-warning"`.

- **[FIXED] `callbacks.py:150-159` — month arithmetic breaks at year boundaries.** `datetime.today().month - 1` was `0` in January and `datetime.today().month - 2` was `0` in February; `get_saving_ratio(year, 0)` matches nothing, so the ratio became `inf`/`nan` and the title displayed "Month 2026-0". Fixed with a `previous_month(year, month)` helper that wraps to `(year - 1, 12)`, and the title now zero-pads the month. As an extra guard, `get_saving_ratio` returns NaN instead of dividing by zero when a period has no income (the gauge renders an empty number rather than crashing).

- **`callbacks.py:156` — monthly gauge ignores the selected year.** The monthly saving-rate gauge always uses *today's* month, even when the user selects a past year, producing e.g. "Saving Rate for Month 2018-5" computed from May-2018 data but presented as if current. Either hide the monthly gauge for past years or use December for non-current years.

- **`callbacks.py:17` — stray `@staticmethod` on a nested function.** `get_date_range` is a local function, not a class member. It happens to work on Python ≥3.10 (staticmethod became callable) but it's incorrect and would fail on 3.9. Remove the decorator.

### Robustness

- **`callbacks.py:104` — `category.split(": ")` assumes exactly one separator.** A category whose name itself contains `": "` would make the unpacking raise `ValueError`. Use `category.split(": ", 1)`.

- **Year dropdown requires a manual yearly bump.** `defaults.YEARS = range(2016, 2027)` and the most recent commit is literally "Update Year Selection Range for 2026". Use `range(2016, datetime.today().year + 1)` so the new year appears automatically (and `DEFAULT_YEAR` is always a valid option — today it would silently fall outside the options if the bump is forgotten).

- **No error containment in callbacks.** Any data irregularity (missing salary, missing category, empty year) bubbles up as a raw Dash error overlay. Consider a small `try/except` wrapper per tab returning a `dbc.Alert` with the error message — much friendlier when a CSV is half-updated.

- **`test/test_core.py:35` — exact float equality.** `total_value_end_1 == total_value_start_2` compares floats with `==`; use `assertAlmostEqual`. Also, both test modules need real data under `DATA_PATH`, so they can't run in CI — consider marking them as integration tests.

- **Stateful managers and threading.** The Flask dev server handles requests in threads, and the managers are shared module-level state. With `TransformationManagerCache` enabled, `_populate_cache` mutates shared state per request — two simultaneous requests for different years would race. Fine for a single user; worth a comment or a lock if the cache is re-enabled.

### Performance

- **Redundant heavy computation per year switch.** Selecting a year fires all four tab callbacks; each one independently calls `get_flow_values`/`get_values_by_asset`, which re-merge and re-explode the entire transaction history. `update_tab_1` alone triggers it ~4× (total flow, salary construction, waterfall, capital gain). Since the data is immutable after startup, memoizing the expensive `TransformationManager` calls (e.g. `functools.lru_cache` keyed on `(start, end, account, how)`, dates as strings) would make year switching near-instant.

- **`Salary` is rebuilt from the full flow history on every Tab 1 refresh** (`callbacks.py:41` → `bkanalysis.salary.Salary.__init__` calls `get_flow_values()` with no range). Same memoization fix applies.

- **`tabs.py` / `callbacks.py:35` — `df.sum()` over a string column.** `df_cash_account_type.sum()` also "sums" (concatenates) the `AccountType` strings before the needed column is picked out. Use `df_cash_account_type[col].sum()`.

- **Docker image carries dev tooling.** `requirements.txt` includes pylint, astroid, isort, dill, mccabe, tomlkit etc. Split into `requirements.txt` / `requirements-dev.txt` to slim the image and speed up builds. Also `BUILD_HELP.bat` always builds with `--no-cache`.

### General

- **`src/utils.py` is dead code.** `FinancialData` (and its `read_csv`) is imported nowhere, and it depends on the legacy `ui`/`ui_old` modules and input files (`df_trans.csv`, `df.csv`) the app no longer uses. Delete it (also note the `self.df_trans = df_trans = ...` double assignment). `defaults.CATEGORY_MAP` and `defaults.REF_CURRENCY` are likewise unused.

- **Personal data committed to the repo.** `src/defaults.py` hardcodes employer payroll names and a base salary; `config/config.ini` contains local file paths and account numbers (sort codes). Since the repo is public-facing, consider loading these from environment variables or a non-committed config overlay.

- **Production server.** `app.run_server(...)` uses the Flask development server. For a long-running home deployment, `gunicorn app:server` (exposing `server = app.server`) is more robust. Note `run_server` is removed in Dash 3 (`app.run` replaces it) — fine while pinned to Dash 2.18, but worth doing during the next upgrade.

- **Unpinned git dependency.** `requirements.txt` installs `bkanalysis` from the GitHub default branch HEAD, so Docker builds are not reproducible — a package push can silently change the next image build. Pin a tag/commit (`...@v0.3#egg=bkanalysis`).

- **`tabs_container.py:5-22` — kebab-case style keys are ignored.** React inline styles require camelCase; `"border-radius"`, `"background-color"`, `"box-shadow"`, `"align-items"` in the tab styles silently do nothing. Convert to camelCase to get the intended look.

- **Title says "Year-End Spending Analysis"** (`layouts/title.py:11`) while the app is a general wealth dashboard — consider renaming.

---

## AccountReporting (`bkanalysis`)

### Bugs

- **`process.py:86-91` — saving mapping files in `__del__`, and `save_on_exit` is ignored.** `Process.__del__` writes all five mapping CSVs whenever the object is garbage-collected. Why that is bad, concretely:
  1. *It saves even when you didn't change anything.* Any code path that constructs a `Process` (e.g. `DataManager.load_data_from_disk`) rewrites `MemoMapping.csv`, `TypeMapping.csv`, etc. on exit, even for a pure read. Your hand-maintained mapping files get touched on every run, so any in-memory corruption gets persisted.
  2. *It persists half-finished state.* `map_type` appends rows to `map_main` as it walks the transactions. If you hit Ctrl+C mid-run (or an exception aborts processing), the destructor still fires and writes the partially-updated mappings over the good files. There is no "abort without saving".
  3. *Destructors are unreliable.* `__del__` may run at interpreter shutdown when modules/globals are already torn down (exceptions there are swallowed, so a failed save is silent), may be delayed arbitrarily, or may never run at all on a hard crash. If two `Process` instances exist, whichever is destroyed last wins and can clobber the other's writes.
  4. *The opt-out doesn't work.* The config defines `save_on_exit : False`, but the code never reads it — there is currently no way to disable this behavior. (`ignore_overrides` in config is likewise unused; `DataManager` hardcodes `ignore_overrides=True`.)

  Recommended fix: delete `__del__` and add an explicit `save_mappings()` method, called deliberately at the end of a successful run and gated on the `save_on_exit` config key.

- **[FIXED] `salary.py:87-91` — `KeyError` when December of the previous year has no salary.** `self.monthly_salaries.loc[prev_year_end]` required a `"{year-1}-12"` row; selecting an early year (or any year preceded by a salary-free December) crashed Tab 1. Now wrapped in `try/except KeyError`: when the row is missing, the carried-over salary defaults to `0.0`. Applied to both `Salary` and `SalaryLegacy`.

- **[FIXED] `figure_manager.py:341,351` — `KeyError` on missing categories in the waterfall.** `categorised_flows.drop("Salary", axis=0)` failed for years with no `Salary` flow, and `categorised_flows.loc["Others"]` failed when no `Others` bucket exists. Now uses `drop(..., errors="ignore")` and `.get("Others", 0.0)`.

- **[FIXED] `market_manager.py:86-88` — loop variable unused; FX rows duplicated per currency.** The comprehension `[... for ccy in df_prices.Currency.unique() if ccy != self.ref_currency]` never used `ccy`, so the same FX frame was concatenated N times; the later merge then multiplied rows before `drop_duplicates` cleaned them up. Now the FX rows are selected once (`df_prices[df_prices.AssetMapped.str.endswith("=X")].copy()`). The final output is identical — the duplicates were deduplicated downstream — but the build uses less memory and no longer raises "No objects to concatenate" when every price is already in the reference currency. While testing this, a second bug was found and fixed in the same function: the `groupby("AssetMapped").apply(reindex_group)` step silently relied on pandas 2 including the grouping column in each group; under pandas 3 it doesn't, and `load_prices` crashed with `KeyError: 'AssetMapped'`. The reindexing now iterates the groups explicitly, which works on both pandas versions.

- **`process/status.py:9-13` — `LastUpdate` broken when a config is passed.** `self.config` is only assigned in the `config is None` branch, but `self.config.read(...)` runs unconditionally → `AttributeError` for callers who pass a config (and the passed config is never used).

- **`market_prices.py:116-117` — removed pandas API.** `result.dropna(1, "all")` / `result.dropna(0, "any")` use positional arguments removed in pandas 2.0 → `TypeError` if `__get_time_series_in_currency` is ever called (it currently appears unused — consider deleting). Similarly `hist.Close[-1]` (`__get_last_close`, line 144) relies on deprecated positional fallback indexing that is removed in pandas 3.x; use `.iloc[-1]`.

- **`process.py:132` — broken error path.** The `AttributeError` handler in `get_master_type` formats `f"failed on: {type} {master_type_mapping[type]}"` using the *builtin* `type` instead of `type_key`, so the error message itself raises. Use `type_key`.

- **`process.py:200` / `apply_overrides` assumes parsed dates.** `self.mapping_override_df["Date"].apply(lambda x: x.strftime(...))` runs on a column read by `pd.read_csv` without `parse_dates` — strings have no `strftime`, so overrides crash on any non-empty `TypeOverrides.csv` unless the date column happens to be pre-parsed. Add `pd.to_datetime` first. (Currently masked because `DataManager` hardcodes `ignore_overrides=True`.)

- **`transformation_manager.py:87` — `get_all_categories` computes the MasterType breakdown (`df_fmt`) and then drops it** from `pd.concat([df_ft, df_st])`. Either intentional (the webapp can't filter on `FullMasterType` because `get_flow_values` doesn't emit that column — a `"MasterType: X"` selection would render an empty tab) or a regression; in both cases delete the dead `df_fmt` computation or add `FullMasterType` to the flow values and re-include it.

- **`test2.py` (repo root) is broken** — imports `bkanalysis.data_manager` (module moved to `bkanalysis.managers`) and reads a nonexistent `dm.data` attribute. `test.py`/`test2.py`/`get_stats.py` are ad-hoc profiling scripts at the package root; move them to a `scripts/` folder or delete so they don't get picked up as tests.

### Robustness

- **`process_helper.py:36,55,70` — interactive `input()` prompts (by design, reviewed).** On review: prompting the user to categorise a new memo is the intended workflow — the suggestions via `difflib` and the immediate persistence into the mapping are the point of the tool, not an accident. This is therefore *not* a bug. The only caveat worth keeping in mind: it assumes a console. If `load_data_from_disk` is ever run unattended (cron job, Docker container, CI), an unmapped memo raises `EOFError` instead of asking. If that ever becomes a use case, an opt-in non-interactive mode (map unknowns to `""` and log them to the `path_missing_map` file the config already defines) would cover it — a nice-to-have, not a fix.

- **`transformation_manager_cache.py:52-69` — cache contract doesn't match the webapp.** The webapp's `get_date_range` spans Dec-31 of the prior year to Dec-31 of the selected year, which fails the `date_start.year != date_end.year` check; also `date_start.year` is dereferenced before the None-check combination is validated (a call with only `date_end` set raises `AttributeError`). Worth fixing because this class is exactly the right answer to the webapp's performance problem (see below). The `copy(deep=True)` per call is also expensive — consider returning a read-only view or copying lazily.

- **`master_transform.py:77-89` — failures are swallowed per file.** `load_multi_thread` prints the exception and drops the file; a typo in one bank export silently vanishes from your wealth. Collect failures and raise (or at least summarize loudly at the end). Also `load_all` returns `None` when no files are found (line 250) — callers then crash later with a cryptic error; raise a clear exception instead. `pd.concat([])` when *all* files fail raises an unrelated `ValueError` too.

- **`market_loader.py` / `market_prices.py` — error handling.** `get_spot_price` has a bare `except:` (line 55); `get_currency` raises a generic `Exception` losing the original type. `get_history` results are cached in an unbounded-lifetime LRU — fine for batch jobs, but a long-lived process never sees fresh prices; a TTL cache (`cachetools.TTLCache`) matches the use better.

- **`config/config_helper.py:4` — config path is CWD-relative.** `source = r"config/config.ini"` means every entry point must be launched from the right directory. Support an env-var override (e.g. `BKANALYSIS_CONFIG`) — the webapp already half-does this with `DATA_PATH`.

- **`figure_manager.py:422-468` — `get_capital_gain_brkdn` edge cases.** `cum_coverage.index[-1]` raises `IndexError` when the first asset alone exceeds the coverage target; `Return` divides by `StartPrice` which may be 0/NaN for assets first priced inside the window.

- **[PARTLY FIXED] `figure_manager.py:491-511` — `get_saving_ratio`.** The divide-by-zero is fixed: the method now returns NaN when there is no salary income in the period. Still open: it hardcodes personal strings ("UBS Bonus") in library code — pass these as parameters with defaults.

- **Date-like signature defaults.** Several `FigureManager` methods declare `date_range: list = None` but immediately do `date_range[0]` (`get_figure_sunburst`, `get_figure_bar`, `get_category_breakdown`, `get_figure_waterfall`) — either make the parameter required or handle None.

- **Coverage gate inconsistency.** `pyproject.toml` sets `fail_under = 75` while TESTING.md reports 45% actual coverage — any `pytest --cov` run fails the threshold. Lower the gate to the current baseline and ratchet it up, otherwise the gate trains people to ignore red CI.

### Performance

- **`get_values_by_asset` re-merges everything on every call** (`transformation_manager.py:89-122`): full outer merge of all grouped transactions with all prices, then cumsum — even when the caller only wants one year. The date filter is applied *after* the merge. Since `DataManager.transactions` is immutable in the webapp, this work is identical every time for the same arguments, so it can be cached. Concretely, how to fix it:

  1. **Add a result cache inside `TransformationManager`.** A plain dict, no library needed:
     ```python
     def __init__(self, ...):
         ...
         self._cache = {}

     def get_values_by_asset(self, date_range=None, account=None):
         key = (
             "values_by_asset",
             tuple(d.isoformat() for d in date_range) if date_range else None,
             tuple(account) if isinstance(account, list) else account,
         )
         if key not in self._cache:
             self._cache[key] = self._compute_values_by_asset(date_range, account)  # current body
         return self._cache[key]
     ```
     Do the same in `get_flow_values` (key on `(date_start, date_end, account, how, include_iat, include_full_types)`) and `get_values_timeseries`. Lists/datetimes must be converted to tuples/strings because dict keys have to be hashable — that's also why `functools.lru_cache` can't be slapped on directly.
  2. **Invalidate in one place.** The data only changes when `group_transaction()` is re-run, so clear the dict there (`self._cache.clear()`). No TTL or size management is needed: there are ~10 years × a few argument combinations, each a modest DataFrame.
  3. **Decide copy vs. view.** If callers mutate the returned frame (the webapp's `get_figure_bar` does `df_expenses["Value"] = -df_expenses["Value"]`), return `self._cache[key].copy()` — still ~100× cheaper than recomputing the merge.
  4. **Effect.** A year switch currently triggers the full-history merge ~6× across the four tab callbacks (total flow, salary construction, waterfall, sunburst, capital gain, timeseries). With the cache, the first tab refresh computes each unique result once and every other call is a dict lookup, so switching back to an already-viewed year becomes essentially free.

  Alternative: fix `TransformationManagerCache` instead (it has the right idea but rejects the webapp's Dec-31→Dec-31 ranges and only caches `get_flow_values`). The dict-cache above is simpler and covers all three hot methods, so it's the recommended route — and the cache subclass can then be retired.

- **`master_transform.Loader.load_internal` re-reads each file per candidate loader.** Each `can_handle` does `pd.read_csv(path, nrows=1)`, so one file may be opened ~28 times. Read the header once and dispatch on the column set (most loaders only compare `set(df.columns)`).

- **`iat_identification.map_iat` iterates with `iterrows`** and does repeated `.loc` scalar writes — O(n) python-level loop over all IAT rows on every load. `map_iat_fx` builds a full cross join (`dummy_key`) of FX rows — O(n²) memory; a `merge_asof`/groupby-window approach would scale much better.

- **`process.apply_overrides` uses `df.apply(..., axis=1)`** over the whole frame to apply a handful of overrides. Build an index from the override keys and update only matching rows.

- **`manager_helper.normalize_date_column`** maps a Python function over every row and then calls `pd.to_datetime` again. `pd.to_datetime(date_column, errors="raise").dt.normalize()` does the same vectorized.

### General

- **Packaging metadata is incomplete.** `setup.py` lists `pandas, numpy, matplotlib, mortgage, yfinance, yahooquery, cachetools` but the package imports `plotly` (managers/ui) and `requests` (market_prices) — a clean `pip install bkanalysis` then breaks at import. Add them, and consider migrating the metadata into `pyproject.toml` (it already exists for tools) with a real version scheme.

- **Legacy code retention.** `ui/ui_old.py`, `ui/salary.py` (superseded by `bkanalysis/salary.py`), `master_transform.load_internal_old`/`USE_LEGACY_LOADER`, and `SalaryLegacy` all duplicate live functionality. The webapp keeps `USE_LEGACY_SALARY_CLASS=False` and tests prove parity (`test_salary_comparison`) — good position to delete the legacy paths and reduce the surface area.

- **Personal configuration baked into library code.** `salary.py:10-63` (`create_legacy`/`create_default`) hardcodes employers and salary amounts; `figure_manager.get_saving_ratio` hardcodes "UBS Bonus"; `market_prices.py` hardcodes ISIN/currency maps. These belong in the config file alongside the existing `[Market] source_map`.

- **Repo hygiene.** Generated artifacts are committed: `htmlcov/`, `.coverage`, `.pytest_cache`, `bkanalysis.egg-info/`, profiling CSVs in `notebooks/`. Add them to `.gitignore` and remove from the index.

- **CI mismatch.** `.github/workflows/python-package.yml` triggers on `master` but the default branch appears to be `main` in the webapp repo — verify the package repo's branch names so CI actually runs.

---

## Suggested order of attack

1. ~~The one-line bug fixes: `get_color`, `data_path` NameError~~ **done**; still open: the `LastUpdate` config bug in `status.py`.
2. ~~Crash-proof Tab 1/Tab 4 for edge years: salary `KeyError`, waterfall `drop("Salary")`, January month arithmetic, `get_saving_ratio` divide-by-zero~~ **done** (plus the `market_manager.py` FX duplication).
3. Replace `Process.__del__` with an explicit `save_mappings()` honoring `save_on_exit`.
4. Add the dict-based result cache to `TransformationManager` (recipe in the Performance section) — biggest UX improvement.
5. Cleanups: delete `src/utils.py`, legacy salary/UI/loader paths, broken root scripts; fix packaging metadata; auto-extend `YEARS`.
