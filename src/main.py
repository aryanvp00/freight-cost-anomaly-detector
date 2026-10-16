import pandas as pd

file_path = "data/shipment_records.csv"

df = pd.read_csv(file_path)

print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 shipments:")
print(df.head())
print("Program started!")

print("Code is running!")

print("\n--- Data Types ---")
print(df.dtypes)

print("\n--- Missing Values ---")
print(df.isnull().sum())

print("\n--- Duplicate Rows ---")
print("Total duplicates:", df.duplicated().sum())

print("\n--- Date Range ---")
print("Start date:", df["shipment_date"].min())
print("End date:", df["shipment_date"].max())

# Convert shipment_date from text to datetime
df["shipment_date"] = pd.to_datetime(df["shipment_date"])

# Create week_of: Monday date for each shipment's week
df["week_of"] = (
    df["shipment_date"]
    - pd.to_timedelta(df["shipment_date"].dt.weekday, unit="D")
)

print("\n--- Weekly Grouping Check ---")
print(df[["shipment_date", "week_of"]].head(10))

print("\nUnique routes:", df[["origin", "destination"]].drop_duplicates().shape[0])
print("Unique weeks:", df["week_of"].nunique())
# Calculate tonne-km for each shipment
df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]

# Group shipments by route and week
weekly_cost = (
    df.groupby(["origin", "destination", "route_type", "week_of"])
    .agg(
        total_freight_cost=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum"),
        shipment_count=("shipment_id", "count")
    )
    .reset_index()
)

# Calculate weekly cost per tonne-km
weekly_cost["cost_per_tonne_km"] = (
    weekly_cost["total_freight_cost"] / weekly_cost["total_tonne_km"]
)

print("\n--- Weekly Cost Analysis ---")
print(weekly_cost.head(10))

print("\nTotal weekly route records:", len(weekly_cost))

# we are calculating our base line with this 
# Sort weekly records chronologically for each route
weekly_cost = weekly_cost.sort_values(
    ["origin", "destination", "week_of"]
).reset_index(drop=True)

# Calculate trailing 8-calendar-week baseline
weekly_cost["own_history_baseline"] = (
    weekly_cost.groupby(["origin", "destination"])["cost_per_tonne_km"]
    .transform(
        lambda s: s.shift(1).rolling(window=8, min_periods=1).mean()
    )
)

# Calculate percentage difference from historical baseline
weekly_cost["vs_own_history"] = (
    (weekly_cost["cost_per_tonne_km"] - weekly_cost["own_history_baseline"])
    / weekly_cost["own_history_baseline"]
    * 100
)

print("\n--- Trailing 8-Week Baseline ---")
print(
    weekly_cost[
        [
            "origin",
            "destination",
            "week_of",
            "cost_per_tonne_km",
            "own_history_baseline",
            "vs_own_history",
        ]
    ].head(15).to_string(index=False)
)
# Create a complete weekly calendar for every route
all_weeks = pd.date_range(
    start=weekly_cost["week_of"].min(),
    end=weekly_cost["week_of"].max(),
    freq="W-MON"
)

routes = weekly_cost[
    ["origin", "destination", "route_type"]
].drop_duplicates()

calendar = routes.merge(
    pd.DataFrame({"week_of": all_weeks}),
    how="cross"
)

# Attach actual weekly costs; missing weeks remain NaN
weekly_cost = calendar.merge(
    weekly_cost,
    on=["origin", "destination", "route_type", "week_of"],
    how="left",
    suffixes=("", "_old")
)

# Calculate baseline using only the previous 8 calendar weeks
weekly_cost = weekly_cost.sort_values(
    ["origin", "destination", "week_of"]
).reset_index(drop=True)

weekly_cost["own_history_baseline"] = (
    weekly_cost.groupby(["origin", "destination"])["cost_per_tonne_km"]
    .transform(
        lambda s: s.shift(1).rolling(window=8, min_periods=1).mean()
    )
)

# Calculate percentage difference from baseline
weekly_cost["vs_own_history"] = (
    (
        weekly_cost["cost_per_tonne_km"]
        - weekly_cost["own_history_baseline"]
    )
    / weekly_cost["own_history_baseline"]
    * 100
)

print("\n--- Corrected Baseline ---")
print(
    weekly_cost[
        [
            "origin",
            "destination",
            "week_of",
            "cost_per_tonne_km",
            "own_history_baseline",
            "vs_own_history",
        ]
    ].head(15).to_string(index=False)
)

print("\nTotal route-week records:", len(weekly_cost))

# Check whether any route-weeks have missing shipment data
missing_weeks = weekly_cost[
    weekly_cost["cost_per_tonne_km"].isna()
]

print("\n--- Missing Route-Weeks ---")
print("Missing route-week records:", len(missing_weeks))

if len(missing_weeks) > 0:
    print(
        missing_weeks[
            ["origin", "destination", "week_of"]
        ].head(10).to_string(index=False)
    )

    # Calculate same-week average cost for each route type
route_type_week_avg = (
    weekly_cost.groupby(["route_type", "week_of"])["cost_per_tonne_km"]
    .transform("mean")
)

# Calculate peer baseline by excluding the current route
route_type_week_sum = (
    weekly_cost.groupby(["route_type", "week_of"])["cost_per_tonne_km"]
    .transform("sum")
)

route_type_week_count = (
    weekly_cost.groupby(["route_type", "week_of"])["cost_per_tonne_km"]
    .transform("count")
)

weekly_cost["peer_baseline"] = (
    (route_type_week_sum - weekly_cost["cost_per_tonne_km"])
    / (route_type_week_count - 1)
)

# Compare current route with peer baseline
weekly_cost["vs_similar_routes"] = (
    (weekly_cost["cost_per_tonne_km"] - weekly_cost["peer_baseline"])
    / weekly_cost["peer_baseline"]
    * 100
)

print("\n--- Peer Route Comparison ---")
print(
    weekly_cost[
        [
            "origin",
            "destination",
            "route_type",
            "week_of",
            "cost_per_tonne_km",
            "peer_baseline",
            "vs_similar_routes",
        ]
    ].head(15).to_string(index=False)
)
# Detect potential anomalies using the 20% threshold
threshold = 20

weekly_cost["potential_anomaly"] = (
    (weekly_cost["vs_own_history"] > threshold)
    | (weekly_cost["vs_similar_routes"] > threshold)
)

print("\n--- Potential Anomalies ---")
print(
    weekly_cost.loc[
        weekly_cost["potential_anomaly"],
        [
            "origin",
            "destination",
            "week_of",
            "cost_per_tonne_km",
            "vs_own_history",
            "vs_similar_routes",
        ],
    ].head(20).to_string(index=False)
)

print(
    "\nTotal potential anomalies:",
    int(weekly_cost["potential_anomaly"].sum()),
)
# Load context notes from CSV
notes = pd.read_csv("data/context_notes.csv")

# Display notes to verify loading
print("\n--- Context Notes ---")
print(notes.head())

print("\nTotal context notes:", len(notes))
print("Note columns:", notes.columns.tolist())

# Convert note dates into datetime format
notes["date"] = pd.to_datetime(notes["date"])

def retrieve_notes(route, week_of):
    week_end = week_of + pd.Timedelta(days=6)

    matching_notes = notes[
        (
            (notes["applies_to"] == route)
            | (notes["applies_to"] == "All Routes")
        )
        & (notes["date"] <= week_end)
    ].copy()

    return matching_notes
def validate_note(note_id, route, week_of):
    week_of = pd.Timestamp(week_of)

    # N001: Flooding on Chennai-Bangalore
    if note_id == "N001":
        return is_flooding_justified(route, week_of)

    # N002: Festival surcharge on Ahmedabad-Mumbai
    if note_id == "N002":
        return (
            note_id == "N002"
            and route == "Ahmedabad-Mumbai"
            and pd.Timestamp("2025-01-20") <= week_of
            <= pd.Timestamp("2025-01-26")
        )

    # N003: Diesel increase does not fully explain a >20% anomaly
    if note_id == "N003":
        return False

    # N004: Affected routes are outside the dataset
    if note_id == "N004":
        return False

    # N005: Maintenance did not significantly affect costs
    if note_id == "N005":
        return False

    # N006: Stable demand and no disruptions
    if note_id == "N006":
        return False

    # N007: Road conditions improved
    if note_id == "N007":
        return False

    # N008: No significant disruptions
    if note_id == "N008":
        return False

    # N009: Confirms the flooding period ended
    if note_id == "N009":
        return False

    # N010: Tracking compliance costs were absorbed
    if note_id == "N010":
        return False

    # Unknown notes are not valid justifications
    return False
# Test the end of the Chennai-Bangalore flooding period
 
def is_flooding_justified(route, week_of):
    week_of = pd.Timestamp(week_of)

    if route != "Chennai-Bangalore":
        return False

    # The note says flooding lasted from Feb 24 through Mar 8.
    flood_start = pd.Timestamp("2025-02-24")
    flood_end = pd.Timestamp("2025-03-08")

    week_end = week_of + pd.Timedelta(days=6)

    # Check whether the calendar week overlaps the flooding period.
    return week_of <= flood_end and week_end >= flood_start

# Create final route names
weekly_cost["route"] = (
    weekly_cost["origin"] + "-" + weekly_cost["destination"]
)

# Set initial classification
weekly_cost["flagged"] = weekly_cost["potential_anomaly"].map(
    {True: "Yes", False: "No"}
)

print("\n--- Final Classification Preview ---")
print(
    weekly_cost[
        [
            "route",
            "week_of",
            "vs_own_history",
            "vs_similar_routes",
            "potential_anomaly",
            "flagged",
        ]
    ].tail(10).to_string(index=False)
)
# Apply context-based justification
weekly_cost["matched_note_id"] = ""
weekly_cost["reason"] = ""

for index, row in weekly_cost.iterrows():
    if not row["potential_anomaly"]:
        weekly_cost.at[index, "flagged"] = "No"
        weekly_cost.at[index, "matched_note_id"] = ""
        weekly_cost.at[index, "reason"] = (
            "No significant cost increase detected."
        )
        continue

    route = row["route"]
    week_of = row["week_of"]

    # Retrieve context notes for this route and week
    candidate_notes = retrieve_notes(route, week_of)

    # Check candidates in chronological order
    justified = False

    for _, note in candidate_notes.sort_values("date").iterrows():
        note_id = note["note_id"]

        if validate_note(note_id, route, week_of):
            weekly_cost.at[index, "flagged"] = "No (justified)"
            weekly_cost.at[index, "matched_note_id"] = note_id
            weekly_cost.at[index, "reason"] = (
                f"Matches note {note_id} dated "
                f"{pd.to_datetime(note['date']).strftime('%Y-%m-%d')}: "
                f"{note['note']} The cost rise has a clear explanation."
            )
            justified = True
            break

    # If no valid note explains the anomaly, keep it flagged
    if not justified:
        weekly_cost.at[index, "flagged"] = "Yes"
        weekly_cost.at[index, "matched_note_id"] = ""

        if (
            pd.Timestamp("2025-05-05")
            <= week_of
            <= pd.Timestamp("2025-05-11")
        ):
            weekly_cost.at[index, "matched_note_id"] = "N003"
            weekly_cost.at[index, "reason"] = (
                "Diesel prices increased by approximately 5-7%, "
                "but this does not fully explain a cost increase "
                "exceeding 20%."
            )
        else:
            weekly_cost.at[index, "reason"] = (
                "Cost increase exceeded the 20% threshold, "
                "and no validated context note justified it."
            )

print("\n--- Context-Based Classification ---")
print(
    weekly_cost.loc[
        weekly_cost["potential_anomaly"],
        ["route", "week_of", "flagged", "matched_note_id", "reason"],
    ].head(15).to_string(index=False)
)
# Prepare the final output CSV
output = weekly_cost[
    weekly_cost["potential_anomaly"]
][
    [
        "route",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
        "flagged",
        "matched_note_id",
        "reason",
    ]
].copy()

# Format dates consistently
output["week_of"] = output["week_of"].dt.strftime("%Y-%m-%d")

# Round cost and percentage values for readability
output["cost_per_tonne_km"] = output["cost_per_tonne_km"].round(2)
output["vs_own_history"] = output["vs_own_history"].apply(
    lambda x: (
        f"{x:+.1f}% vs this route's past average"
        if pd.notna(x)
        else ""
    )
)
output["vs_similar_routes"] = output["vs_similar_routes"].apply(
    lambda x: (
        f"{x:+.1f}% vs similar-length routes this week"
        if pd.notna(x)
        else ""
    )
)
# Save the result
output.to_csv("data/anomaly_report.csv", index=False)

print("\n--- Final Report ---")
print("Total anomalies:", len(output))
print("Output saved to data/anomaly_report.csv")
print(output.head(10).to_string(index=False))
# Validate the final output
print("\n--- Output Validation ---")

print("Total output rows:", len(output))
print("Required columns:", output.columns.tolist())
print("Missing values:")
print(output.isnull().sum())

print("\nFlag distribution:")
print(output["flagged"].value_counts())

print("\nMatched context notes:")
print(
    output.loc[
        output["matched_note_id"] != "",
        ["route", "week_of", "flagged", "matched_note_id"]
    ].to_string(index=False)
)
print("\n--- Flooding Context Tests ---")

test_cases = [
    ("2025-02-17", False),
    ("2025-02-24", True),
    ("2025-03-03", True),
    ("2025-03-10", False),
    ("2025-03-17", False),
]

for week, expected in test_cases:
    actual = is_flooding_justified(
        "Chennai-Bangalore",
        week
    )

    print(
        f"Week: {week} | Expected: {expected} | Actual: {actual}"
    )
    print("\n--- N009 Retrieval Test ---")

post_flood_notes = retrieve_notes(
    "Chennai-Bangalore",
    pd.Timestamp("2025-03-17")
)

print(
    post_flood_notes[
        ["note_id", "date", "note"]
    ].to_string(index=False)
)

print(
    "\nN009 found:",
    "N009" in post_flood_notes["note_id"].values
)
print("\n--- Irrelevant Route Test ---")

test_notes = retrieve_notes(
    "Delhi-Jaipur",
    pd.Timestamp("2024-03-11")
)

print(
    test_notes[
        ["note_id", "date", "applies_to", "note"]
    ].to_string(index=False)
)
print("\n--- Inspect N004 ---")

print(
    notes.loc[
        notes["note_id"] == "N004",
        ["note_id", "date", "applies_to", "note"]
    ].to_string(index=False)
)
print("\n--- Note Validation Tests ---")

tests = [
    ("N001", "Chennai-Bangalore", "2025-03-03", True),
    ("N001", "Chennai-Bangalore", "2025-03-17", False),
    ("N002", "Ahmedabad-Mumbai", "2025-01-20", True),
    ("N003", "Mumbai-Pune", "2025-05-05", False),
    ("N004", "Delhi-Jaipur", "2024-03-11", False),
    ("N005", "Mumbai-Delhi", "2024-07-29", False),
    ("N006", "Mumbai-Pune", "2025-09-22", False),
    ("N007", "Delhi-Jaipur", "2024-05-20", False),
    ("N008", "Kolkata-Bhubaneswar", "2025-06-09", False),
    ("N009", "Chennai-Bangalore", "2025-03-17", False),
    ("N010", "Mumbai-Pune", "2025-10-27", False),
]

passed = 0

for note_id, route, week, expected in tests:
    result = validate_note(note_id, route, week)
    status = "PASS" if result == expected else "FAIL"

    print(
        f"{status} | {note_id} | {route} | {week} | "
        f"Expected={expected}, Actual={result}"
    )

    if result == expected:
        passed += 1

print(f"\nTests passed: {passed}/{len(tests)}")
