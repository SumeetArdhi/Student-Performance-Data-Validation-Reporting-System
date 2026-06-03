-- ============================================================
-- Student Performance Data Validation & Reporting System
-- Database Schema
-- ============================================================

-- Drop views first (depend on tables), then tables (for clean re-runs)
DROP VIEW  IF EXISTS v_at_risk_students;
DROP VIEW  IF EXISTS v_top_performers;
DROP VIEW  IF EXISTS v_grade_distribution;
DROP VIEW  IF EXISTS v_subject_summary;
DROP TABLE IF EXISTS validation_log;
DROP TABLE IF EXISTS student_performance;
DROP TABLE IF EXISTS students;

-- ============================================================
-- Core Tables
-- ============================================================

CREATE TABLE students (
    student_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    age             INTEGER,
    gender          TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    email           TEXT,
    semester        INTEGER CHECK(semester BETWEEN 1 AND 8),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_performance (
    record_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      TEXT NOT NULL,
    subject         TEXT NOT NULL,
    marks           REAL CHECK(marks BETWEEN 0 AND 100),
    grade           TEXT,
    attendance_pct  REAL CHECK(attendance_pct BETWEEN 0 AND 100),
    semester        INTEGER CHECK(semester BETWEEN 1 AND 8),
    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- ============================================================
-- Validation Log Table
-- ============================================================

CREATE TABLE validation_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_row      INTEGER,
    student_id      TEXT,
    issue_type      TEXT NOT NULL,   -- 'DUPLICATE', 'MISSING_VALUE', 'OUT_OF_RANGE', 'INVALID_FORMAT'
    field_name      TEXT,
    original_value  TEXT,
    description     TEXT,
    flagged_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Reporting Views
-- ============================================================

-- Subject-wise performance summary
CREATE VIEW v_subject_summary AS
SELECT
    subject,
    COUNT(*)                          AS total_students,
    ROUND(AVG(marks), 2)              AS avg_marks,
    MAX(marks)                        AS max_marks,
    MIN(marks)                        AS min_marks,
    ROUND(AVG(attendance_pct), 2)     AS avg_attendance,
    SUM(CASE WHEN marks >= 75 THEN 1 ELSE 0 END) AS students_above_75,
    SUM(CASE WHEN marks < 50  THEN 1 ELSE 0 END) AS students_failing
FROM student_performance
GROUP BY subject;

-- Grade distribution
CREATE VIEW v_grade_distribution AS
SELECT
    grade,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM student_performance), 2) AS percentage
FROM student_performance
GROUP BY grade
ORDER BY count DESC;

-- Top performers
CREATE VIEW v_top_performers AS
SELECT
    s.student_id,
    s.name,
    s.semester,
    p.subject,
    p.marks,
    p.grade,
    p.attendance_pct
FROM students s
JOIN student_performance p ON s.student_id = p.student_id
WHERE p.marks >= 85
ORDER BY p.marks DESC;

-- At-risk students (low marks OR low attendance)
CREATE VIEW v_at_risk_students AS
SELECT
    s.student_id,
    s.name,
    s.semester,
    p.subject,
    p.marks,
    p.attendance_pct,
    CASE
        WHEN p.marks < 50 AND p.attendance_pct < 60 THEN 'Critical'
        WHEN p.marks < 50 THEN 'Low Marks'
        WHEN p.attendance_pct < 60 THEN 'Low Attendance'
        ELSE 'Monitor'
    END AS risk_category
FROM students s
JOIN student_performance p ON s.student_id = p.student_id
WHERE p.marks < 60 OR p.attendance_pct < 65;
