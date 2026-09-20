# request-delay

## Objective
Add a configurable `request_delay` (seconds) to `config.yaml` that pauses before each HTTP call to the Massive API.

## Problem
Rate-limiting protection. User wants 20s default between requests.

## Scope
- Add `request_delay` field to config.yaml (default: 20s)
- Validate in `load_config` (numeric >= 0)
- Pass to `MassiveDownloader` constructor
- `time.sleep` in `_get_json()` before each request
- Tests for delay behavior and validation

## Constraints
- Sleep in `_get_json()` to cover pagination, packages, and tickers
- No new dependencies (time is stdlib)
- Default 0.0 in MassiveDownloader (config sets the real value)
- Don't touch DataDownloader interface

## Tasks

- [x] T1: Update `src/config/config.yaml` with `request_delay: 20`
- [x] T2: Add `request_delay` param to `MassiveDownloader.__init__`, sleep in `_get_json()`
- [x] T3: Validate `request_delay` in `load_config`, pass to downloader in `download_massive`
- [x] T4: Test delay behavior in `tests/test_download_massive.py`
- [x] T5: Update `tests/test_small_cli.py` configs and add validation cases

## Acceptance criteria
- All tests pass (`python -m unittest discover`)
- `init.sh` passes
- `request_delay` is configurable and validated
- Sleep happens before every Massive HTTP call

## Verification
```bash
venv/Scripts/python.exe -m unittest discover
./init.sh
```

## Result
- Status: ✅ Complete
- Commit: `1ee8f48`
- Tests: 44 passed
- Route: delegated direct (5 files)
