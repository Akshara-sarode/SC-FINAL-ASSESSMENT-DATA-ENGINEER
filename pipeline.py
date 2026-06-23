"""
Springer Capital - Referral Program Data Pipeline
=================================================
Processes referral data, applies business logic to detect potential fraud, and produces a validated report

Author  : Empire Ogbueghu
Dataset : Springer DE Intern Dataset
Output  : output/referral_report.csv ( expected 46 rows)
"""

# 1. IMPORTS
import os
import pandas as pd
from zoneinfo import ZoneInfo  # IANA timezone conversion

# 2. CONFIGURATION
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3. HELPER FUNCTIONS
def load_csv(filename: str) -> pd.DataFrame:
    """Load a CSV file from DATA_DIR. All columns read as str for safe casting"""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Expected CSV not found: {path}")
    df = pd.read_csv(path, dtype=str)
    print(f" Loaded {filename:<35} {len(df):>10} rows")
    return df

def to_utc(series: pd.Series) -> pd.Series:
    """Parse ISO-8601 strings (including trailing Z) -> UTC-aware Timestamps"""
    return pd.to_datetime(series,utc=True, errors="coerce")


def convert_to_local(utc_series: pd.Series, tz_series: pd.Series) -> pd.Series:
    """ Row-wise UTC -> local time conversion
        Returns a timezone_NAIVE series (tzinfo stripped for clean CSV output)"""
    
    results = []
    for utc_ts, tz_name in zip(utc_series, tz_series):
        if pd.isna(utc_ts) or pd.isna(tz_name):
            results.append(pd.NaT)
        else:
            try:
                local_ts = utc_ts.astimezone(ZoneInfo(str(tz_name)))
                results.append(local_ts.replace(tzinfo=None))
            except Exception:
                results.append(pd.NaT)
    return pd.Series(results, index=utc_series.index)


def initcap(series: pd.Series) -> pd.Series:
    """Title-case every string; leave NaN as NaN."""
    return series.where(series.isna(), series.str.title())


def extract_reward_days(series: pd.Series) -> pd.Series:
    """Extract integer from strings like '10 days' -> 10."""
    return pd.to_numeric(series.str.extract(r"(\d+)")[0], errors="coerce")



# 4. DATA LOADING
print("\n=== STEP 1 - LOADING DATA ===")

lead_log               = load_csv("lead_log.csv")
paid_transactions       = load_csv("paid_transactions.csv")
referral_rewards        = load_csv("referral_rewards.csv")
user_logs               = load_csv("user_logs.csv")
user_referral_logs      = load_csv("user_referral_logs.csv")
user_referral_statuses  = load_csv("user_referral_statuses.csv")
user_referrals          = load_csv("user_referrals.csv")


# 5. DATA CLEANING
print("\n=== STEP 2 - DATA CLEANING ===")

# --- 5a. Replace literal "null" strings (how NULL was serialised in these CSVs) ---
ALL_DFS = [lead_log, paid_transactions, referral_rewards, user_logs, user_referral_logs, user_referral_statuses, user_referrals]
for df in ALL_DFS:
    df.replace({"null": pd.NA, "NULL": pd.NA}, inplace=True)

# --- 5b. Cast boolean columns stored as "TRUE" / "FALSE" strings ---
user_logs["is_deleted"] = (
    user_logs["is_deleted"].str.upper().map({"TRUE": True, "FALSE": False})
)
user_referral_logs["is_reward_granted"] = (
    user_referral_logs["is_reward_granted"].str.upper().map({"TRUE": True, "FALSE": False})
)


# --- 5c. Cast numeric IDs ---
user_referrals["user_referral_status_id"] = pd.to_numeric(
    user_referrals["user_referral_status_id"], errors="coerce"
)
user_referrals["referral_reward_id"] = pd.to_numeric(
    user_referrals["referral_reward_id"], errors="coerce"
)
user_referral_statuses["id"] = pd.to_numeric(
    user_referral_statuses["id"], errors="coerce"
)
referral_rewards["id"] = pd.to_numeric(referral_rewards["id"], errors="coerce")


# --- 5d. Parse timestamps to UTC ---
user_referrals["referral_at"]                   = to_utc(user_referrals["referral_at"])
user_referrals["updated_at"]                    = to_utc(user_referrals["updated_at"])
paid_transactions["transaction_at"]            = to_utc(paid_transactions["transaction_at"])
user_referral_logs["created_at"]                = to_utc(user_referral_logs["created_at"])
user_logs["membership_expired_date"]            = pd.to_datetime(
    user_logs["membership_expired_date"], errors="coerce"
)

# --- 5e. Deduplicate history / log tables ---

# user_logs is an audit log; the same user_id can appear many times.
# I keep the latest record per user_id (highest surrogate 'id').
user_logs["id"] = pd.to_numeric(user_logs["id"], errors="coerce")
user_logs = (
    user_logs.sort_values("id", ascending=False)
    .drop_duplicates(subset=["user_id"], keep="first")
    .reset_index(drop=True)
)
print(f"user_logs after dedup: {len(user_logs)} unique users")

# lead_log is also a history table; keep latest per lead_id.
lead_log["id"] = pd.to_numeric(lead_log["id"], errors="coerce")
lead_log = (
    lead_log.sort_values("id", ascending=False)
    .drop_duplicates(subset=["lead_id"], keep="first")
    .reset_index(drop=True)
)
print(f" lead_log after dedup: {len(lead_log)} unique leads")

# user_referral_logs: multiple entries per referral - keep the latest (most recent created_at)
# The latest entry reflects the current reward-grant status.
user_referral_logs = (
    user_referral_logs.sort_values("created_at", ascending=False)
    .drop_duplicates(subset=["user_referral_id"], keep="first")
    .reset_index(drop=True)
)
print(f" referral_logs after dedup: {len(user_referral_logs)} unique referrals")

print(" Data Cleaning Complete")


# 
# 6. DATA PROCESSING (joins, time conversion, string normalisation)

print("\n === STEP 3 - DATA PROCESSING ===")

# 6a. Start from user_referrals (1 row per referral = 46 rows)
df = user_referrals.copy()

# 6b. Attach referral status description
df = df.merge(
    user_referral_statuses[["id", "description"]].rename(
        columns={"id": "user_referral_status_id", "description": "referral_status"}
    ),
    on="user_referral_status_id",
    how="left"
)

# 6c. Attach reward value
df = df.merge(
    referral_rewards[["id", "reward_value"]].rename(
        columns={"id": "referral_reward_id"}
    ),
    on="referral_reward_id",
    how="left"
)
df["num_reward_days"] = extract_reward_days(df["reward_value"])


# 6d. Attach latest referral-log info (reward grant status + timestamp) -
df = df.merge(
    user_referral_logs[["user_referral_id", "created_at", "is_reward_granted"]].rename(
        columns={"created_at": "reward_granted_at"}
    ),
    left_on="referral_id",
    right_on="user_referral_id",
    how="left"
)

# 6e. Attach paid transaction details
df = df.merge(
    paid_transactions,
    on="transaction_id",            # transaction_id, transaction_status, transaction_at, etc
    how="left"
)

# 6f. Attach referrer info from user_logs
# referrer_id is NULL for some draft-transaction referrals; those rows
# will have NaN referrer fiels, which is expected.
df = df.merge(
    user_logs[["user_id", "name", "phone_number", "homeclub", "timezone_homeclub",
               "membership_expired_date", "is_deleted"]].rename(columns={
                   "user_id":                   "referrer_id",
                   "name":                      "referrer_name",
                   "phone_number":              "referrer_phone_number",
                   "homeclub":                  "referrer_homeclub",
                   "timezone_homeclub":         "timezone_referrer",
                   "membership_expired_date":   "referrer_membership_expired",
                   "is_deleted":                "referrer_is_deleted",
    }),
    on="referrer_id",
    how="left"
)



# 6g. Attach lead source category (only relevant when referral_source = 'Lead')
# referee_id == lead_log.lead_id for Lead- sourced referrals
df = df.merge(
    lead_log[["lead_id", "source_category", "timezone_location"]].rename(columns={
        "lead_id":                   "referee_id",
        "source_category":           "lead_source_category",
        "timezone_location":         "timezone_lead"
    }),
    on="referee_id",
    how="left"
)

print(f"  Rows after all joins: {len(df)}  (expected 46)") 


# 6h. Source category derivation
# 'User Sign Up'  -> Online
# 'Draft Transaction' -> Offline
# 'Lead' -> value from lead_log.source_category
def assign_source_category(row):
    src = row["referral_source"]
    if src == "User Sign Up":
        return "Online"
    elif src == "Draft Transaction":
        return "Offline"
    elif src == "Lead":
        return row.get("lead_source_category", pd.NA)
    return pd.NA

df["referral_source_category"] = df.apply(assign_source_category, axis=1)


# 6i. Timezone conversion
# All raw timestamps are UTC; convert each to the relevant local timezone.
# Priority for timezone lookup:
#   - transaction_at   -> timezone_transaction (already on paid_transactions)
#   - referral_at      -> timezone_referrer (referrer's homeclub timezone)
#   - updated_at       -> timezone_referrer
#   - reward_granted_at -> timezone_referrer

tz_txn = df["timezone_transaction"].fillna(df["timezone_referrer"])

df["transaction_at"]      = convert_to_local(df["transaction_at"], tz_txn)
df["referral_at"]         = convert_to_local(df["referral_at"],     df["timezone_referrer"])
df["updated_at"]          = convert_to_local(df["updated_at"],      df["timezone_referrer"])
df["reward_granted_at"]   = convert_to_local(df["reward_granted_at"], df["timezone_referrer"])


# 6j. String normalisation - Initcap on human - readable string fields
# Club names are left as-is (spec explicitly excludes them).
# Name columns (referrer_name, referee_name) are hashed/masked in this
# dataset, so Initcap is only applied to status, source, and type fields.

for col in ["referral_status", "referral_source", "referral_source_category",
            "transaction_status", "transaction_type"]:
    if col in df.columns:
        df[col] = initcap(df[col])

print(" Joins, timezone conversion, and string normalization complete")


# 7. BUSINESS LOGIC VALIDATION (fraud detection)

print("\n === STEP 4 - BUSINESS LOGIC VALIDATION ===")

def evaluate_business_logic(row) -> bool:

    """
    Returns True if the referral reward record is VALID; False if INVALID.
    
    - VALID cases
    Condition 1 - Sucessful referral, fully validated:
     - reward value > 0
     - referral status = "Berhasil"
     - transaction_id exists
     - transaction_status = "PAID"
     - transaction_type = "NEW"
     - transaction occurred AFTER referral was created
     - transaction is in the SAME calender month as the referral
     - referrer membership has NOT expired at time of referral
     - referrer account is NOT deleted
     - reward has been granted (is_reward_granted = True)

     Condition 2 - Pending / failed with no reward (expected / clean state):
     - referrer status = {"Menunggu", "Tidak Berhasil"}
     - no reward value (null or 0)

     - INVALID (everything else)-
     Catches scenarios such as:
     - reward > 0 but status is NOT "Berhasil"
     - reward > 0 but no transaction ID
     - no reward but has a paid transaction (reward omitted in error)
     - status = "Berhasil" but reward is null / 0
     - transaction occurred before the referral was created
    """


    #   Extract row fields
    status          = str(row.get("referral_status") or "").strip()
    reward_days     = row.get("num_reward_days")
    txn_id          = row.get("transaction_id")
    txn_status      = str(row.get("transaction_status") or "").strip()
    txn_type        = str(row.get("transaction_type") or "").strip()
    txn_at          = row.get("transaction_at")
    ref_at          = row.get("referral_at")
    is_rewarded     = row.get("is_reward_granted")
    mem_exp         = row.get("referrer_membership_expired")
    is_deleted      = row.get("referrer_is_deleted")

    
    # Derived boolean flags 
    has_reward      = pd.notna(reward_days) and float(reward_days) > 0
    has_txn         = pd.notna(txn_id)
    paid_txn        = txn_status.title() == "Paid"
    is_new_txn      = txn_type.title() == "New"

    txn_after_ref  = (
        pd.notna(txn_at) and pd.notna(ref_at)
        and pd.Timestamp(txn_at).year == pd.Timestamp(ref_at).year
        and pd.Timestamp(txn_at).month == pd.Timestamp(ref_at).month
    )

    # Membership not expired: expired date must be >= referral date
    membership_ok = (
        pd.notna(mem_exp) and pd.notna(ref_at)
        and pd.Timestamp(mem_exp) >= pd.Timestamp(ref_at).normalize()
    )
    referrer_active = (is_deleted is False)
    reward_granted = (is_rewarded is True)

    # --- Valid Condition 1 ---
    if (has_reward
        and status == "Berhasil"
        and has_txn
        and paid_txn
        and is_new_txn
        and txn_after_ref
        #and same_month
        and membership_ok
        and referrer_active
        and reward_granted):
        return True
    
    # --- Valid Condition 2 ---
    if (status in {"Menunggu", "Tidak Berhasil"}
        and not has_reward):
        return True
    
    # --- Invalid (everything else) ---
    return False

df["is_business_logic_valid"] = df.apply(evaluate_business_logic, axis=1)

valid_count = df["is_business_logic_valid"].sum()
invalid_count = (~df["is_business_logic_valid"]).sum()

print(f"Valid records: {valid_count}")
print(f"Invalid records: {invalid_count}")
print(f" Total         : {len(df)}")


# 8. BUILD & SAVE OUTPUT REPORT

print("\n === STEP 5 - BUILDING OUTPUT REPORT ===")

df = df.reset_index(drop=True)
# Surrogate PK starting at 101 (matches sample data in the spec)
df.insert(0, "referral_details_id", df.index + 101)

# Select only the columns required in the output spec
report = df[[
    "referral_details_id",
    "referral_id",
    "referral_source",
    "referral_source_category",
    "referral_at",
    "referrer_id",
    "referrer_name",
    "referrer_phone_number",
    "referrer_homeclub",
    "referee_id",
    "referee_name",
    "referee_phone",
    "referral_status",
    "num_reward_days",
    "transaction_id",
    "transaction_status",
    "transaction_at",
    "transaction_location",
    "transaction_type",
    "updated_at",
    "reward_granted_at",
    "is_business_logic_valid",
]].copy()

# Format datetime columns as "YYYY-MM-DD HH:MM:SS" strings for clean CSV output and readability
for col in ["referral_at", "transaction_at", "updated_at", "reward_granted_at"]:
    report[col] = pd.to_datetime(report[col], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")

# Store reward days as nullable integer (blank when null, not "NaN")
report["num_reward_days"] = (
    pd.to_numeric(report["num_reward_days"], errors="coerce").astype("Int64")
)

output_path = os.path.join(OUTPUT_DIR, "referral_report.csv")
report.to_csv(output_path, index=False)

print(f" Report saved to {output_path}")
print(f" Total rows  : {len(report)}")
print(f"\n{'='*60} PIPELINE COMPLETED SUCCESSFULLY {'='*60}\n")

