# DATA PROFILING
# Profiles every CSV table in the dataset and writes a summary to output folder


import os
import pandas as pd

# CONFIGURATION
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All source CSV files to profile
CSV_FILES = [
    "lead_log.csv",
    "paid_transactions.csv",
    "referral_rewards.csv",
    "user_logs.csv",
    "user_referral_logs.csv",
    "user_referral_statuses.csv",
    "user_referrals.csv",
]

def profile_table(filepath: str, table_name: str) -> pd.DataFrame:
    # Profile a single CSV file
    # Returns one row per column with profiling statistics.

    # Read raw (no type inference) so we can inspect original values
    df = pd.read_csv(filepath, dtype=str)
    # Replace literal "null" strings with real NaN so they count as missing

    df.replace({"null": pd.NA, "NULL": pd.NA}, inplace=True)

    rows = []
    for col in df.columns:
        series = df[col]
        total = len(series)
        nulls = series.isna().sum()
        non_null = series.dropna()

        rows.append({
            "table_name":       table_name,
            "column_name":      col,
            "data_type":        "string (raw CSV)",
            "total_rows":       total,
            "null_count":       nulls,
            "null_percentage":  round(nulls / total * 100, 2) if total > 0 else 0,
            "populated_pct":    round((total - nulls) / total * 100, 2) if total > 0 else 0,
            "distinct_count":   non_null.nunique(),
            "min_value":        non_null.min() if len(non_null) > 0 else None,
            "max_value":        non_null.max() if len(non_null) > 0 else None,
            "sample_value":     non_null.iloc[0] if len(non_null) > 0 else None,

        })

    return pd.DataFrame(rows)


# Main profiling loop
print("\n === DATA PROFILNG ===\n")
all_profiles = []

for filename in CSV_FILES:
    filepath = os.path.join(DATA_DIR, filename)
    table_name = filename.replace(".csv", "")

    if not os.path.exists(filepath):
        print(f" SKIP {filename} - file not found")
        continue


    profile = profile_table(filepath, table_name)
    all_profiles.append(profile)
    print(f" Profiled {table_name:<30} {len(profile)} columns")


# Combine all table profiles into one DataFrame
profiling_report = pd.concat(all_profiles, ignore_index=True)

# Save to CSV
out_path = os.path.join(OUTPUT_DIR, "data_profiling.csv")
profiling_report.to_csv(out_path, index=False)

print(f"\n Profiling report saved -> {out_path}")
print(f" Total columns profiled: {len(profiling_report)}")

# Also print a quick summary to the console
print("\n" + "=" * 90)
for tbl in profiling_report["table_name"].unique():
    subset = profiling_report[profiling_report["table_name"] == tbl]
    print(f"\n-- {tbl} ({subset['total_rows'].iloc[0]} rows) " + "-" * 50)
    print(subset[["column_name", "null_count", "distinct_count",
                  "populated_pct", "min_value", "max_value"]].to_string(index=False))
    
print()
                                  
     