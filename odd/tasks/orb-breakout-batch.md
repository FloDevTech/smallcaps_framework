# OrbBreakout batch notebook

## Objective

Create an isolated `test_parquet_data_5.ipynb` experiment that runs the existing
`OrbBreakout` strategy against the same Parquet batch workflow as data_4.

## Problem and scope

`test_parquet_data_4.ipynb` can run a supplied strategy class but does not build the
opening-range or median-volume columns consumed by `OrbBreakout`. The approved scope is
limited to a copied notebook and its strategy-specific indicator and batch setup.

## Constraints

- Preserve `test_parquet_data_4.ipynb` unchanged.
- Reuse the `OrbBreakout` behavior from `strategy_tests.ipynb`.
- Notebook-only changes do not require automated tests or `init.sh` execution.
- Route: delegated. Trigger: notebook needs strategy-source reading and non-mechanical
  indicator, class, and batch changes.

## Tasks

- [x] ORB-1 Create `test_parquet_data_5.ipynb` from data_4 and adapt it for `OrbBreakout`.
  - Acceptance: the notebook creates `orb_high_15m`, `orb_low_15m`, and
    `median_vol_100`; its single and batch runs select `OrbBreakout`.
  - Evidence: notebook JSON is valid; its modified cells were inspected to confirm
    the ORB indicators, `OrbBreakout` inputs, and explicit batch selection.
  - Limitation: by explicit user instruction, no notebook tests, Parquet batch, or
    `init.sh` execution was run.
  - Commit: c6f9e737166556858bdac1dda2dde5542005120d

## Progress

ORB-1 completed and committed. No batch was executed by user instruction.
