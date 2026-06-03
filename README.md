# Student Performance Data Validation & Reporting System

A Python + SQL + Excel pipeline that validates, transforms, loads, and reports on student academic performance data.

## Project Structure

```
student_performance/
├── data/
│   └── raw_students.csv              # Raw input dataset (with intentional errors)
├── db/
│   └── schema.sql                    # SQLite schema + reporting views
├── reports/                          # Output folder (generated files go here)
├── scripts/
│   ├── validate_data.py              # Step 1: detect & log data quality issues
│   ├── transform_load.py             # Step 2: normalise data and load into SQLite
│   └── generate_report.py            # Step 3: produce formatted Excel report
├── run_pipeline.py                   # Runs all 3 steps in sequence
├── requirements.txt
└── .gitignore
```

> **Generated files** (`data/clean_students.csv`, `data/validation_issues.csv`, `db/student_performance.db`, `reports/student_performance_report.xlsx`) are excluded from version control via `.gitignore` — they are produced when you run the pipeline.

---

## Setup

**Requirements:** Python 3.9+

```bash
pip install -r requirements.txt
```

---

## Run the Full Pipeline

```bash
python run_pipeline.py
```

This runs all three steps in order and produces `reports/student_performance_report.xlsx`.

---

## Run Steps Individually

```bash
python scripts/validate_data.py      # Step 1
python scripts/transform_load.py     # Step 2
python scripts/generate_report.py    # Step 3
```

---

## What Each Step Does

### Step 1 — `validate_data.py`
- Reads `data/raw_students.csv`
- Detects: **duplicates**, **missing required fields**, **out-of-range marks** (>100), missing email, invalid gender
- Writes `data/clean_students.csv` — rows that pass all hard rules
- Writes `data/validation_issues.csv` — full audit log of every issue found
- Prints data completeness %

### Step 2 — `transform_load.py`
- Reads `data/clean_students.csv`
- Standardises data types and text (title-case names, lowercase email, canonical grade format)
- Loads into SQLite: `students` and `student_performance` tables
- Creates 4 reporting views: `v_subject_summary`, `v_grade_distribution`, `v_top_performers`, `v_at_risk_students`

### Step 3 — `generate_report.py`
- Queries the SQLite database
- Produces a 4-sheet formatted Excel workbook:
  - **Summary Dashboard** — KPI cards + subject-wise performance table
  - **All Student Records** — full data with colour-coded marks (green ≥75, red <50)
  - **Validation Issues** — audit log of all data quality flags
  - **At-Risk Students** — students with low marks or attendance, with risk category

---

## Data Quality Issues in the Sample Dataset

| Student | Issue | Detail |
|---------|-------|--------|
| S001 | Duplicate row | Appears twice — second occurrence dropped |
| S005 | Missing age | Age field is empty |
| S006 | Missing marks | Marks field is empty — row retained with null marks |
| S012 | Missing email | Email address is missing |
| S017 | Missing gender | Gender field is empty |
| S022 | Out-of-range marks | Marks = 120 (allowed range: 0–100) — row dropped |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.9+ |
| Data processing | pandas |
| Database | SQLite (via sqlite3) |
| Report output | openpyxl |
| Input data | CSV |
