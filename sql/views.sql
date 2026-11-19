-- =====================================================================
-- views.sql : views consumed by Power BI and the scorecard
-- =====================================================================

DROP VIEW IF EXISTS vw_hospital_outcomes_summary;
DROP VIEW IF EXISTS vw_admissions_detail;

-- ---------------------------------------------------------------------
-- vw_hospital_outcomes_summary  (required by the brief)
--
-- One row per hospital x department x diagnosis x month.
-- It stores COUNTS and SUMS, not percentages, so any slice
-- (one hospital, one diagnosis, a date range) can be re-aggregated
-- correctly: rate = SUM(events) / SUM(admissions).
-- Averaging pre-computed percentages would give wrong answers.
-- ---------------------------------------------------------------------
CREATE VIEW vw_hospital_outcomes_summary AS
SELECT
    hospital_id,
    department,
    primary_diagnosis,
    admission_month,
    COUNT(*)                                                        AS admissions,
    COUNT(DISTINCT patient_id)                                      AS unique_patients,
    SUM(length_of_stay_days)                                        AS total_los_days,
    SUM(readmitted_within_30_days)                                  AS readmissions,
    SUM(CASE WHEN discharge_outcome = 'Died'                THEN 1 ELSE 0 END) AS deaths,
    SUM(CASE WHEN discharge_outcome = 'Recovered'           THEN 1 ELSE 0 END) AS recovered,
    SUM(CASE WHEN discharge_outcome = 'Referred'            THEN 1 ELSE 0 END) AS referred,
    SUM(CASE WHEN discharge_outcome = 'Left Against Advice' THEN 1 ELSE 0 END) AS left_against_advice,
    SUM(is_icu_admission)                                           AS icu_admissions,
    SUM(weekend_admission)                                          AS weekend_admissions,
    SUM(total_cost_ngn)                                             AS total_cost_ngn,
    SUM(amount_paid_ngn)                                            AS amount_paid_ngn,
    SUM(outstanding_ngn)                                            AS outstanding_ngn,
    -- convenience rates for this exact grain (do NOT average these across rows)
    ROUND(AVG(length_of_stay_days), 1)                              AS avg_los_days,
    ROUND(AVG(readmitted_within_30_days) * 100.0, 1)                AS readmission_rate_pct,
    ROUND(SUM(CASE WHEN discharge_outcome = 'Died' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS mortality_rate_pct
FROM admissions
GROUP BY hospital_id, department, primary_diagnosis, admission_month;


-- ---------------------------------------------------------------------
-- vw_admissions_detail
-- Row-level table for Power BI. Power BI needs one row per admission
-- for slicers on date/diagnosis, the LOS histogram, and doctor drill-down.
-- ---------------------------------------------------------------------
CREATE VIEW vw_admissions_detail AS
SELECT
    admission_id, patient_id, hospital_id, state,
    admission_date, discharge_date, admission_month, admission_quarter, admission_weekday,
    CASE weekend_admission WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS admission_day_type,
    weekend_admission, age, age_group, gender, insurance_type,
    department, bed_type, is_icu_admission, treatment_type,
    primary_diagnosis, secondary_diagnosis, num_procedures, num_medications,
    length_of_stay_days,
    CASE WHEN length_of_stay_days <= 7  THEN '01-07 days'
         WHEN length_of_stay_days <= 14 THEN '08-14 days'
         WHEN length_of_stay_days <= 21 THEN '15-21 days'
         WHEN length_of_stay_days <= 28 THEN '22-28 days'
         WHEN length_of_stay_days <= 35 THEN '29-35 days'
         ELSE '36-45 days' END                                   AS los_band,
    total_cost_ngn, amount_paid_ngn, outstanding_ngn, collection_rate, cost_per_day,
    discharge_outcome, died, readmitted_within_30_days,
    attending_doctor_id, nurse_ratio
FROM admissions;
