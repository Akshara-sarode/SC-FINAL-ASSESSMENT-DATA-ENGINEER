# Springer Capital - Data Engineer Intern Take-Home Assessment

## Project Overview

This project implements a complete referral reward validation pipeline for Springer Capital.

The objective is to process referral data, perform data profiling, apply business validation rules, identify potential fraud cases, and generate a final referral reward report.

The solution was implemented using Python, Pandas, and PySpark.

---

# Business Objective

The referral program rewards existing users (referrers) for bringing new users (referees) to the platform.

The pipeline validates referral rewards by checking:

- Referral status
- Transaction validity
- Reward eligibility
- Membership status
- Reward grant status
- Transaction timing

The final output identifies whether each referral reward follows the defined business rules.

---

# Source Tables

The pipeline processes the following source files:

| File Name | Description |
|------------|------------|
| lead_log.csv | Lead source information |
| user_referrals.csv | Referral records |
| user_referral_logs.csv | Referral reward logs |
| user_logs.csv | User information |
| user_referral_statuses.csv | Referral status definitions |
| referral_rewards.csv | Reward information |
| paid_transactions.csv | Transaction details |

---

# Project Structure

```text
.
├── your_script.py
├── data_profile.py
├── Dockerfile
├── requirements.txt
├── README.md
├── data_dictionary.xlsx
│
├── lead_log.csv
├── user_referrals.csv
├── user_referral_logs.csv
├── user_logs.csv
├── user_referral_statuses.csv
├── referral_rewards.csv
├── paid_transactions.csv
│
└── referral_report.csv
```

---

# Data Profiling

The profiling script evaluates each source table and generates:

- Null Count
- Distinct Value Count
- Data Type
- Minimum Value
- Maximum Value

This helps identify data quality issues before processing.

Run:

```bash
python data_profile.py
```

---

# Data Processing Workflow

## Step 1 – Data Loading

Load all source CSV files into DataFrames.

## Step 2 – Data Cleaning

The following transformations are applied:

- Remove duplicate records
- Handle missing values
- Correct data types
- Standardize string values
- Convert timestamps

## Step 3 – Timezone Conversion

All timestamps are stored in UTC.

Timestamp values are converted into local time using:

- timezone_homeclub
- timezone_transaction
- timezone_location

If a timezone is unavailable, related tables are joined to retrieve the correct timezone.

## Step 4 – Table Joins

The following tables are joined:

- user_referrals
- user_referral_logs
- user_logs
- user_referral_statuses
- referral_rewards
- paid_transactions
- lead_log

Duplicate records are removed after joining.

## Step 5 – Referral Source Category

Business rule:

```sql
CASE
WHEN referral_source = 'User Sign Up'
THEN 'Online'

WHEN referral_source = 'Draft Transaction'
THEN 'Offline'

WHEN referral_source = 'Lead'
THEN source_category

END
```

This creates:

```text
referral_source_category
```

:contentReference[oaicite:1]{index=1}

---

# Business Logic Validation

The final report contains:

```text
is_business_logic_valid
```

A referral reward is considered valid when:

- Reward value > 0
- Referral status = Berhasil
- Transaction exists
- Transaction status = PAID
- Transaction type = NEW
- Transaction occurs after referral creation
- Transaction occurs in the same month
- Membership is active
- User account is not deleted
- Reward has been granted

A referral reward is considered invalid when any required validation rule fails.

The implementation follows the fraud detection rules defined in the assessment document. :contentReference[oaicite:2]{index=2}

---

# Output Report

Generated file:

```text
referral_report.csv
```

Expected output:

- 46 rows
- One record per referral reward evaluation

Required output columns include:

- referral_details_id
- referral_id
- referral_source
- referral_source_category
- referral_at
- referrer_id
- referrer_name
- referrer_phone_number
- referrer_homeclub
- referee_id
- referee_name
- referee_phone
- referral_status
- num_reward_days
- transaction_id
- transaction_status
- transaction_at
- transaction_location
- transaction_type
- updated_at
- reward_granted_at
- is_business_logic_valid

The assessment specifies that the final report should contain 46 rows. :contentReference[oaicite:3]{index=3}

---

# Running Locally

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Profiling

```bash
python data_profile.py
```

## Run Main Pipeline

```bash
python your_script.py
```

---

# Docker Instructions

## Build Docker Image

```bash
docker build -t springer-assessment .
```

## Run Container

```bash
docker run springer-assessment
```

The pipeline will execute:

1. Data Profiling
2. Data Processing
3. Business Logic Validation
4. Report Generation

---

# Deliverables

This repository contains all required submission assets:

✅ Python Processing Script (`your_script.py`)

✅ Data Profiling Script (`data_profile.py`)

✅ Dockerfile

✅ Data Dictionary (`data_dictionary.xlsx`)

✅ README Documentation

✅ Final Report (`referral_report.csv`)

---

# Demo Workflow

The demonstration follows:

1. Clone repository
2. Install dependencies
3. Run data profiling
4. Run referral processing pipeline
5. Validate final report
6. Verify output row count
7. Review valid and invalid referral cases

---

# Author

Akshara Avinash Sarode

Springer Capital – Data Engineer Intern Take-Home Assessment
