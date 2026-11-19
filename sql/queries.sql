-- =====================================================================
-- queries.sql : analytical queries for Project 03
-- Run after schema.sql + data load (python/load_to_sql.py).
-- Rates are returned as percentages rounded to 1 decimal place.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q0. Data completeness by facility (check before aggregating)
-- ---------------------------------------------------------------------
SELECT hospital_id,
       COUNT(*)                         AS admissions,
       MIN(admission_date)              AS first_admission,
       MAX(admission_date)              AS last_admission,
       COUNT(DISTINCT admission_month)  AS months_with_data
FROM admissions
GROUP BY hospital_id
ORDER BY admissions DESC;


-- ---------------------------------------------------------------------
-- Q1. Overall 30-day readmission and mortality rate (network headline KPIs)
-- ---------------------------------------------------------------------
SELECT COUNT(*)                                                      AS admissions,
       COUNT(DISTINCT patient_id)                                    AS unique_patients,
       ROUND(AVG(readmitted_within_30_days) * 100.0, 1)              AS readmission_rate_pct,
       ROUND(COUNT(CASE WHEN discharge_outcome = 'Died' THEN 1 END) * 100.0 / COUNT(*), 1) AS mortality_rate_pct,
       ROUND(AVG(length_of_stay_days), 1)                            AS avg_los_days,
       ROUND(AVG(total_cost_ngn), 0)                                 AS avg_cost_per_admission_ngn
FROM admissions;


-- ---------------------------------------------------------------------
-- REQUIRED 1. Average length of stay by diagnosis and hospital
-- ---------------------------------------------------------------------
-- (a) by diagnosis
SELECT primary_diagnosis,
       COUNT(*)                            AS admissions,
       ROUND(AVG(length_of_stay_days), 1)  AS avg_los_days
FROM admissions
GROUP BY primary_diagnosis
ORDER BY AVG(length_of_stay_days) DESC;

-- (b) by hospital and diagnosis (grain used in the dashboard matrix)
SELECT hospital_id,
       primary_diagnosis,
       COUNT(*)                            AS admissions,
       ROUND(AVG(length_of_stay_days), 1)  AS avg_los_days
FROM admissions
GROUP BY hospital_id, primary_diagnosis
ORDER BY hospital_id, avg_los_days DESC;


-- ---------------------------------------------------------------------
-- REQUIRED 2. Mortality rate by department
-- ---------------------------------------------------------------------
SELECT department,
       COUNT(*)                                                    AS admissions,
       COUNT(CASE WHEN discharge_outcome = 'Died' THEN 1 END)      AS deaths,
       ROUND(COUNT(CASE WHEN discharge_outcome = 'Died' THEN 1 END) * 100.0 / COUNT(*), 1) AS mortality_rate_pct,
       -- deaths above what the network-wide rate would predict for this volume
       ROUND(COUNT(CASE WHEN discharge_outcome = 'Died' THEN 1 END)
             - COUNT(*) * (SELECT AVG(died * 1.0) FROM admissions), 1)                    AS excess_deaths
FROM admissions
GROUP BY department
ORDER BY mortality_rate_pct DESC;


-- ---------------------------------------------------------------------
-- REQUIRED 3. Readmission rate by insurance type
-- ---------------------------------------------------------------------
SELECT insurance_type,
       COUNT(*)                                          AS admissions,
       SUM(readmitted_within_30_days)                    AS readmissions,
       ROUND(AVG(readmitted_within_30_days) * 100.0, 1)  AS readmission_rate_pct,
       ROUND(AVG(length_of_stay_days), 1)                AS avg_los_days
FROM admissions
GROUP BY insurance_type
ORDER BY readmission_rate_pct DESC;


-- ---------------------------------------------------------------------
-- REQUIRED 4. Top 10 most common diagnoses
-- ---------------------------------------------------------------------
SELECT primary_diagnosis,
       COUNT(*)                                          AS admissions,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM admissions), 1) AS share_pct,
       ROUND(AVG(readmitted_within_30_days) * 100.0, 1)  AS readmission_rate_pct,
       ROUND(AVG(died) * 100.0, 1)                       AS mortality_rate_pct
FROM admissions
GROUP BY primary_diagnosis
ORDER BY admissions DESC, primary_diagnosis
LIMIT 10;     -- SQL Server: use SELECT TOP 10 instead


-- ---------------------------------------------------------------------
-- REQUIRED 5. Cost per patient day by bed type
-- length_of_stay_days is constrained > 0 in schema.sql, so no divide-by-zero.
-- pooled = total billed / total bed-days (the finance definition)
-- ---------------------------------------------------------------------
SELECT bed_type,
       COUNT(*)                                            AS admissions,
       SUM(length_of_stay_days)                            AS bed_days,
       ROUND(SUM(total_cost_ngn) / SUM(length_of_stay_days), 0) AS pooled_cost_per_day_ngn,
       ROUND(AVG(cost_per_day), 0)                         AS mean_cost_per_day_ngn,
       ROUND(AVG(total_cost_ngn), 0)                       AS avg_cost_per_admission_ngn
FROM admissions
GROUP BY bed_type
ORDER BY pooled_cost_per_day_ngn DESC;


-- ---------------------------------------------------------------------
-- EXTRA. Weekend vs weekday admissions and outcome (Key Question 6)
-- ---------------------------------------------------------------------
SELECT CASE weekend_admission WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS admission_day,
       COUNT(*)                                                                       AS admissions,
       ROUND(AVG(died) * 100.0, 1)                                                    AS mortality_rate_pct,
       ROUND(COUNT(CASE WHEN discharge_outcome = 'Left Against Advice' THEN 1 END) * 100.0 / COUNT(*), 1) AS lama_rate_pct,
       ROUND(COUNT(CASE WHEN discharge_outcome = 'Recovered' THEN 1 END) * 100.0 / COUNT(*), 1)           AS recovered_rate_pct,
       ROUND(AVG(readmitted_within_30_days) * 100.0, 1)                               AS readmission_rate_pct
FROM admissions
GROUP BY weekend_admission;


-- ---------------------------------------------------------------------
-- EXTRA. Age group volumes and their #1 diagnosis (Key Question 8)
-- ---------------------------------------------------------------------
WITH dx AS (
    SELECT age_group, primary_diagnosis, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY age_group ORDER BY COUNT(*) DESC, primary_diagnosis) AS rk
    FROM admissions
    GROUP BY age_group, primary_diagnosis
)
SELECT a.age_group,
       COUNT(*)                 AS admissions,
       MAX(dx.primary_diagnosis) AS top_diagnosis,
       MAX(dx.n)                AS top_diagnosis_admissions
FROM admissions a
JOIN dx ON dx.age_group = a.age_group AND dx.rk = 1
GROUP BY a.age_group
ORDER BY admissions DESC;


-- ---------------------------------------------------------------------
-- EXTRA. Monthly readmission and mortality trend (time series)
-- ---------------------------------------------------------------------
SELECT admission_month,
       COUNT(*)                                          AS admissions,
       ROUND(AVG(readmitted_within_30_days) * 100.0, 1)  AS readmission_rate_pct,
       ROUND(AVG(died) * 100.0, 1)                       AS mortality_rate_pct
FROM admissions
GROUP BY admission_month
ORDER BY admission_month;


-- ---------------------------------------------------------------------
-- IMPRESSIVE. Doctors with readmission rates above their hospital average
-- (subquery benchmark, as suggested in the brief)
--
-- Doctors in this dataset work across several hospitals, so each admission
-- is compared with the readmission rate of the hospital it happened in, and
-- the doctor's "expected" rate is the average of those hospital rates.
-- ---------------------------------------------------------------------
SELECT d.attending_doctor_id,
       d.admissions,
       d.hospitals_worked,
       d.readmission_rate_pct,
       d.expected_rate_pct,
       ROUND(d.readmission_rate_pct - d.expected_rate_pct, 1) AS gap_pts
FROM (
    SELECT a.attending_doctor_id,
           COUNT(*)                                          AS admissions,
           COUNT(DISTINCT a.hospital_id)                     AS hospitals_worked,
           ROUND(AVG(a.readmitted_within_30_days) * 100.0, 1) AS readmission_rate_pct,
           ROUND(AVG(h.hospital_rate) * 100.0, 1)            AS expected_rate_pct
    FROM admissions a
    JOIN (SELECT hospital_id, AVG(readmitted_within_30_days * 1.0) AS hospital_rate
          FROM admissions
          GROUP BY hospital_id) h
      ON h.hospital_id = a.hospital_id
    GROUP BY a.attending_doctor_id
) d
WHERE d.readmission_rate_pct > d.expected_rate_pct
  AND d.admissions >= 5                       -- ignore doctors with too few patients to judge
ORDER BY gap_pts DESC;


-- ---------------------------------------------------------------------
-- Hospital scorecard straight from the view
-- ---------------------------------------------------------------------
SELECT hospital_id,
       SUM(admissions)                                             AS admissions,
       ROUND(SUM(total_los_days) * 1.0 / SUM(admissions), 1)       AS avg_los_days,
       ROUND(SUM(readmissions) * 100.0 / SUM(admissions), 1)       AS readmission_rate_pct,
       ROUND(SUM(deaths) * 100.0 / SUM(admissions), 1)             AS mortality_rate_pct,
       ROUND(SUM(recovered) * 100.0 / SUM(admissions), 1)          AS recovery_rate_pct,
       ROUND(SUM(total_cost_ngn) / SUM(admissions), 0)             AS avg_cost_ngn,
       ROUND(SUM(amount_paid_ngn) * 100.0 / SUM(total_cost_ngn), 1) AS collection_rate_pct
FROM vw_hospital_outcomes_summary
GROUP BY hospital_id
ORDER BY recovery_rate_pct DESC;
