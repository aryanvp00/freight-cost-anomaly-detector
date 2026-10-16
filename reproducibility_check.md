# Reproducibility Check

## Objective
Verify that repeated executions produce identical anomaly reports.

## Procedure
The program was executed three times using the same input dataset.
Each output was saved separately:

- `repro/run_1.csv`
- `repro/run_2.csv`
- `repro/run_3.csv`

## Verification
The following command was used to compare the outputs:

```bash
cmp repro/run_1.csv repro/run_2.csv
cmp repro/run_2.csv repro/run_3.csv