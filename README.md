# Freight Cost Anomaly Checker

## 1. Overview

The Freight Cost Anomaly Checker analyzes weekly freight costs across shipping routes and identifies unusual cost increases.

It compares each route's cost against:
- Its own historical costs.
- Similar routes during the same week.
- Context notes that may explain unusual cost changes.

The system generates a CSV report containing potential anomalies, comparison metrics, classifications, and explanations.

**Technologies:** Python, pandas

## 2. Project Structure

```text
freight-cost-checker/
├── data/
│   ├── shipment_records.csv
│   ├── context_notes.csv
│   └── anomaly_report.csv
├── src/
│   └── main.py
├── tests/
│   └── test_note_validation.py
├── repro/
│   ├── run_1.csv
│   ├── run_2.csv
│   └── run_3.csv
├── README.md
├── reproducibility_check.md
└── token_cost_log.md
```

## 3. Dataset

### Input Files

- `data/shipment_records.csv`: Shipment records containing routes, quantities, distances, freight costs, dates, and transporter information.
- `data/context_notes.csv`: Context notes describing events that may explain freight cost changes.

The shipment dataset contains 2,940 records.

### Output File

- `data/anomaly_report.csv`: Final report containing potential anomalies and their classifications.

## 4. Methodology

### 4.1 Weekly Aggregation

Shipments are grouped by route and week. Each week runs from Monday through Sunday, and `week_of` represents the Monday date.

Cost per tonne-km is calculated as:

**Cost per tonne-km = Total Freight Cost / Total Tonne-km**

Where:

**Tonne-km = Quantity in Tonnes × Distance in Kilometres**

The calculation uses total freight cost divided by total tonne-km rather than averaging individual shipment ratios.

### 4.2 Own-History Baseline

Each week's cost is compared with the average cost of the previous eight available weekly observations for the same route.

- The current week is excluded from the historical baseline.
- When fewer than eight previous observations exist, all available prior observations are used.
- Historical values are not padded or extrapolated.
- If no previous observations exist, the historical comparison is unavailable.

### 4.3 Similar-Route Baseline

Each week's cost is compared with the average cost of other routes of the same route type during that week.

The route being evaluated is excluded from the peer average.

If no eligible peer routes are available, the peer comparison is undefined.

### 4.4 Anomaly Detection

A 20% threshold is used as an implementation choice to identify potentially significant cost increases.

A route-week is identified as a potential anomaly if either:

- Its cost is more than 20% above its own historical baseline.
- Its cost is more than 20% above the peer baseline.

The threshold can be calibrated further using business requirements and labeled historical data.

### 4.5 Context-Note Validation

Context notes are checked against route and date conditions before they can justify an anomaly.

Examples include:

- **N001:** Flooding on the Chennai-Bangalore route temporarily disrupted transport.
- **N002:** A regional festival caused a temporary surcharge on the Ahmedabad-Mumbai route.
- **N003:** A nationwide diesel-price increase of approximately 5–7% is not considered sufficient by itself to justify a cost increase exceeding the 20% threshold.

Irrelevant notes, unsupported explanations, and notes outside their applicable periods are not accepted as justifications.

A potential anomaly without a validated explanation remains flagged for human review.

### 4.6 Final Classification

The output report contains potential anomalies only.

- **`Yes`:** A potential anomaly has no validated context-based justification and requires human review.
- **`No (justified)`:** A potential anomaly has a validated context note explaining the cost increase.

Ordinary route-weeks that are not identified as potential anomalies are excluded from the final report.

## 5. Output Columns

The output CSV uses the following column order:

| Column | Description |
|---|---|
| `route` | Shipping route |
| `week_of` | Monday date for the week |
| `cost_per_tonne_km` | Weekly freight cost per tonne-km, rounded to two decimal places |
| `vs_own_history` | Percentage difference from the historical baseline |
| `vs_similar_routes` | Percentage difference from the peer baseline |
| `flagged` | Final anomaly classification |
| `matched_note_id` | Validated context note ID, if applicable |
| `reason` | Explanation for the classification |

Percentage comparisons are formatted as descriptive strings.

For unexplained anomalies, `matched_note_id` is left blank.

## 6. Installation and Execution

Python 3 and pandas are required.

Install pandas if necessary:

```bash
python3 -m pip install pandas
```

Run the project from the project root:

```bash
python3 src/main.py
```

The program processes the input data, calculates historical and peer baselines, identifies potential anomalies, validates context notes, and generates:

```text
data/anomaly_report.csv
```

## 7. Testing

The dedicated context-validation test suite is located at:

```text
tests/test_note_validation.py
```

Install pytest if necessary:

```bash
python3 -m pip install pytest
```

Run the tests:

```bash
python3 -m pytest -v tests/test_note_validation.py
```

The test suite covers:

- Valid context-note justifications.
- Incorrect routes.
- Incorrect dates.
- Irrelevant context notes.
- Unknown note IDs.

**Latest test result: 9 tests passed.**

## 8. Reproducibility

The program was executed three times using the same input data.

The generated outputs were saved as:

- `repro/run_1.csv`
- `repro/run_2.csv`
- `repro/run_3.csv`

The files were compared using the `cmp` command. All three outputs were byte-for-byte identical.

This confirms reproducibility across the three tested runs with the same inputs and execution environment.

See `reproducibility_check.md` for the verification record.

## 9. Execution Summary

The latest successful run reported:

| Metric | Result 
|---|---:|
| Input shipment records | 2,940 |
| Weekly route records | 728 |
| Potential anomalies | 20 |
| Unexplained anomalies flagged for review | 17 |
| Anomalies justified by validated context | 3 |
| Dedicated context-validation tests | 9 passed |

These results describe the supplied dataset and the current implementation. They do not guarantee future detection accuracy.

## 10. AI and Cost Considerations

The current implementation uses deterministic Python and pandas logic for weekly aggregation, baseline comparisons, anomaly detection, and context-note validation.

It does not currently make LLM API calls.

- **LLM API calls:** 0
- **Input tokens:** 0
- **Output tokens:** 0
- **LLM API cost:** ₹0

Local machine execution costs were not measured.

The deterministic approach supports reproducibility and avoids LLM API costs. However, context-note interpretation relies on explicitly implemented validation rules rather than a general-purpose language model.

See `token_cost_log.md` for the usage record.

## 11. Limitations and Future Improvements

Potential improvements include:

 Calibrating the anomaly threshold using labeled historical data.
Adding automated tests for aggregation and baseline calculations.
 Expanding context validation to support additional event types.
 Developing an evaluation harness with labeled examples.
 Exploring an LLM-based explanation layer with evidence references, strict grounding, and usage-cost monitoring.

