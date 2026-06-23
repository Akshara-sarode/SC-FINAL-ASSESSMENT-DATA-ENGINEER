# Referral Pipeline Analysis

## Overview

This project builds a referral data pipeline using Python (Pandas) to process referral records, profile source tables, validate business rules, and detect potential fraud in reward allocation.

## Project Objectives

* Load and profile raw referral data sources
* Clean and standardize the datasets
* Merge all source tables into a master referral dataset
* Apply business logic validation to identify valid and invalid reward scenarios
* Generate a final CSV report for business users
* Containerize the application using Docker

## Source Tables

* user_referrals
* user_logs
* user_referral_logs
* referral_rewards
* paid_transactions
* lead_logs
* user_referral_statuses

## Pipeline Flow

1. Data Loading
2. Data Profiling
3. Data Cleaning
4. Data Standardization
5. Data Joining
6. Business Logic Validation
7. Final Report Export

## Output Files

Located in `/output`

* data_dictionary.xlsx
* data_profiling.csv
* referral_report.csv

## Business Logic Validation Rules

A referral reward is valid if:

* Reward value exists and is greater than 0
* Referral status is successful (Berhasil)
* Transaction exists
* Transaction status is PAID
* Transaction type is NEW
* Transaction happened after referral creation
* Transaction occurred in the same month as referral creation
* Referrer membership is still active
* Referrer account is not deleted
* Reward has been granted

Invalid scenarios include:

* Reward exists but referral failed
* Reward exists without transaction
* Successful referral without reward
* Transaction before referral date

## How to Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run script:

```bash
python pipeline.py
```

## Docker Usage

Build image:

```bash
docker build -t referral-pipeline .
```

Run container:

```bash
docker run --rm -v ${PWD}/output:/app/output referral-pipeline
```

## Final Output

Expected output:

* Final Report Shape: (46, 22)

## Tools Used

* Python
* Pandas
* Docker
* OpenPyXL

## Author

Prepared for Springer Capital Data Engineer Take-Home Test