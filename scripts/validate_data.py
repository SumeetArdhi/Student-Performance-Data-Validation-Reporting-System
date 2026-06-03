"""
validate_data.py
----------------
Reads raw_students.csv, detects data quality issues, logs them,
and writes a cleaned CSV ready for database loading.

Issues detected:
  - Duplicate student_id entries
  - Missing values in required fields (student_id, name, subject, semester)
  - Out-of-range marks (must be 0-100)
  - Missing email addresses
  - Missing / invalid gender
"""

import pandas as pd
import os
import sys

# -- Paths -------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CSV    = os.path.join(BASE_DIR, "data", "raw_students.csv")
CLEAN_CSV  = os.path.join(BASE_DIR, "data", "clean_students.csv")
ISSUES_CSV = os.path.join(BASE_DIR, "data", "validation_issues.csv")

# -- Validation rules --------------------------------------------------------
REQUIRED_FIELDS      = ["student_id", "name", "subject", "semester"]
MARKS_MIN, MARKS_MAX = 0, 100
VALID_GENDERS        = {"Male", "Female", "Other"}


def validate(df: pd.DataFrame):
    """
    Validate df, return (clean_df, issues_list).
    Rows are dropped for: duplicates, missing required fields, out-of-range marks.
    Rows are retained (with warnings) for: missing marks, missing email, missing gender.
    """
    issues = []

    # Use a boolean Series aligned to df's actual index
    flags = pd.Series(False, index=df.index)

    def log(row_idx, student_id, issue_type, field, original_value, description):
        issues.append({
            "source_row":     row_idx + 2,   # +2: 1-based + header row
            "student_id":     student_id,
            "issue_type":     issue_type,
            "field_name":     field,
            "original_value": original_value,
            "description":    description,
        })

    # 1. Duplicates ----------------------------------------------------------
    dup_mask = df.duplicated(subset=["student_id"], keep="first")
    for idx in df.index[dup_mask]:
        row = df.loc[idx]
        log(idx, row["student_id"], "DUPLICATE", "student_id", row["student_id"],
            f"Duplicate student_id '{row['student_id']}' — keeping first occurrence only.")
    flags |= dup_mask

    # 2. Missing required fields ---------------------------------------------
    for field in REQUIRED_FIELDS:
        missing = df[field].isna() | (df[field].astype(str).str.strip() == "")
        for idx in df.index[missing]:
            row = df.loc[idx]
            log(idx, row["student_id"], "MISSING_VALUE", field, None,
                f"Required field '{field}' is empty.")
        flags |= missing

    # 3. Out-of-range marks --------------------------------------------------
    marks_num  = pd.to_numeric(df["marks"], errors="coerce")
    range_mask = marks_num.notna() & ((marks_num < MARKS_MIN) | (marks_num > MARKS_MAX))
    for idx in df.index[range_mask]:
        row = df.loc[idx]
        log(idx, row["student_id"], "OUT_OF_RANGE", "marks", row["marks"],
            f"Marks value {row['marks']} is outside allowed range ({MARKS_MIN}-{MARKS_MAX}).")
    flags |= range_mask

    # 4. Missing marks (warn, keep row) --------------------------------------
    missing_marks = marks_num.isna() & ~flags
    for idx in df.index[missing_marks]:
        row = df.loc[idx]
        log(idx, row["student_id"], "MISSING_VALUE", "marks", None,
            "Marks field is empty; row retained with null marks.")

    # 5. Missing email (warn, keep) ------------------------------------------
    missing_email = df["email"].isna() | (df["email"].astype(str).str.strip() == "")
    for idx in df.index[missing_email & ~flags]:
        row = df.loc[idx]
        log(idx, row["student_id"], "MISSING_VALUE", "email", None,
            "Email address is missing.")

    # 6. Missing / invalid gender (warn, keep) --------------------------------
    invalid_gender = df["gender"].isna() | ~df["gender"].isin(VALID_GENDERS)
    for idx in df.index[invalid_gender & ~flags]:
        row = df.loc[idx]
        log(idx, row["student_id"], "MISSING_VALUE", "gender", row["gender"],
            f"Gender is missing or invalid (expected one of {sorted(VALID_GENDERS)}).")

    clean_df = df[~flags].copy()
    return clean_df, issues


def main():
    print("=" * 60)
    print("  Student Data Validation")
    print("=" * 60)

    if not os.path.exists(RAW_CSV):
        print(f"[ERROR] Raw CSV not found: {RAW_CSV}")
        sys.exit(1)

    raw_df     = pd.read_csv(RAW_CSV, dtype=str)
    total_raw  = len(raw_df)
    print(f"\n[INFO] Loaded {total_raw} rows from {os.path.basename(RAW_CSV)}")

    clean_df, issues = validate(raw_df)
    total_clean  = len(clean_df)
    total_issues = len(issues)
    dropped      = total_raw - total_clean

    # Save outputs -----------------------------------------------------------
    clean_df.to_csv(CLEAN_CSV, index=False)
    issues_df = pd.DataFrame(issues)
    issues_df.to_csv(ISSUES_CSV, index=False)

    # Summary ----------------------------------------------------------------
    print("\n[RESULT] Validation complete")
    print(f"  Raw rows         : {total_raw}")
    print(f"  Clean rows       : {total_clean}")
    print(f"  Rows dropped     : {dropped}")
    print(f"  Issues flagged   : {total_issues}")

    if total_issues:
        by_type = issues_df["issue_type"].value_counts()
        print("\n  Issues by type:")
        for itype, cnt in by_type.items():
            print(f"    {itype:<20} {cnt}")

    completeness = round(total_clean / total_raw * 100, 1) if total_raw else 0
    print(f"\n  Data completeness after cleaning: {completeness}%")
    print(f"\n[OUTPUT] Clean data  -> {CLEAN_CSV}")
    print(f"[OUTPUT] Issues log  -> {ISSUES_CSV}")
    print("=" * 60)


if __name__ == "__main__":
    main()
