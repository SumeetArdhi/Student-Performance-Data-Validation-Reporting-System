"""
transform_load.py
-----------------
Transforms clean_students.csv and loads it into a SQLite database,
applying schema standardisation (data types, grade normalisation, etc.)
"""

import pandas as pd
import sqlite3
import os
import sys

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV  = os.path.join(BASE_DIR, "data", "clean_students.csv")
SCHEMA_SQL = os.path.join(BASE_DIR, "db", "schema.sql")
DB_PATH    = os.path.join(BASE_DIR, "db", "student_performance.db")

# ── Grade normalisation map ────────────────────────────────────────────────
GRADE_MAP = {
    "a+": "A+", "a":  "A",  "a-": "A-",
    "b+": "B+", "b":  "B",  "b-": "B-",
    "c+": "C+", "c":  "C",  "c-": "C-",
    "d":  "D",  "f":  "F",
}


def normalise(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the flat CSV into students and performance DataFrames."""
    df = df.copy()

    # Cast types
    df["age"]            = pd.to_numeric(df["age"],            errors="coerce").astype("Int64")
    df["marks"]          = pd.to_numeric(df["marks"],          errors="coerce")
    df["attendance_pct"] = pd.to_numeric(df["attendance_pct"], errors="coerce")
    df["semester"]       = pd.to_numeric(df["semester"],       errors="coerce").astype("Int64")

    # Standardise text fields
    df["name"]    = df["name"].str.strip().str.title()
    df["gender"]  = df["gender"].str.strip().str.title()
    df["subject"] = df["subject"].str.strip().str.title()
    df["email"]   = df["email"].str.strip().str.lower()
    df["grade"]   = df["grade"].str.strip().map(
        lambda g: GRADE_MAP.get(g.lower(), g) if isinstance(g, str) else g
    )

    # ── students table ───────────────────────────────────────────────────
    students_df = (
        df[["student_id", "name", "age", "gender", "email", "semester"]]
        .drop_duplicates(subset=["student_id"])
        .reset_index(drop=True)
    )

    # ── performance table ────────────────────────────────────────────────
    perf_df = (
        df[["student_id", "subject", "marks", "grade", "attendance_pct", "semester"]]
        .reset_index(drop=True)
    )

    return students_df, perf_df


def create_schema(conn: sqlite3.Connection):
    with open(SCHEMA_SQL, "r") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    print("[DB]  Schema created.")


def load_to_db(students_df: pd.DataFrame, perf_df: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    # Load students
    students_df.to_sql("students", conn, if_exists="append", index=False)
    print(f"[DB]  Inserted {len(students_df)} rows → students")

    # Load performance
    perf_df.to_sql("student_performance", conn, if_exists="append", index=False)
    print(f"[DB]  Inserted {len(perf_df)} rows → student_performance")

    conn.commit()
    conn.close()


def verify_db():
    """Quick query check after loading."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    checks = [
        ("students",            "SELECT COUNT(*) FROM students"),
        ("student_performance", "SELECT COUNT(*) FROM student_performance"),
        ("v_subject_summary",   "SELECT COUNT(*) FROM v_subject_summary"),
        ("v_at_risk_students",  "SELECT COUNT(*) FROM v_at_risk_students"),
    ]

    print("\n[VERIFY] Row counts after load:")
    for label, sql in checks:
        cnt = cur.execute(sql).fetchone()[0]
        print(f"  {label:<25} {cnt}")

    conn.close()


def main():
    print("=" * 60)
    print("  Data Transformation & DB Load")
    print("=" * 60)

    if not os.path.exists(CLEAN_CSV):
        print(f"[ERROR] Clean CSV not found: {CLEAN_CSV}")
        print("        Run validate_data.py first.")
        sys.exit(1)

    df = pd.read_csv(CLEAN_CSV, dtype=str)
    print(f"\n[INFO] Loaded {len(df)} clean rows from {os.path.basename(CLEAN_CSV)}")

    students_df, perf_df = normalise(df)
    print(f"[TRANSFORM] {len(students_df)} unique students | {len(perf_df)} performance records")

    load_to_db(students_df, perf_df)
    verify_db()

    print(f"\n[OUTPUT] Database → {DB_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
