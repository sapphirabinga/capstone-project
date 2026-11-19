-- =====================================================================
-- schema.sql : table definition for the cleaned admissions data
-- Project 03 - Hospital Patient Outcomes Dashboard
--
-- Written in standard SQL. Tested on SQLite 3; runs on PostgreSQL / MySQL
-- with no changes (in SQL Server use NVARCHAR and DATE the same way).
-- Load the data with python/load_to_sql.py, or with your database's
-- CSV import tool pointed at data/cleaned_admissions.csv.
-- =====================================================================

DROP VIEW  IF EXISTS vw_hospital_outcomes_summary;
DROP VIEW  IF EXISTS vw_admissions_detail;
DROP TABLE IF EXISTS admissions;

CREATE TABLE admissions (
    admission_id              VARCHAR(10)   PRIMARY KEY,     -- one row = one hospital stay
    patient_id                VARCHAR(10)   NOT NULL,        -- can repeat across admissions
    hospital_id               VARCHAR(10)   NOT NULL,
    state                     VARCHAR(30)   NOT NULL,        -- patient's state
    admission_date            DATE          NOT NULL,
    discharge_date            DATE          NOT NULL,
    admission_month           CHAR(7)       NOT NULL,        -- 'YYYY-MM'
    admission_quarter         CHAR(6)       NOT NULL,        -- 'YYYYQn'
    admission_weekday         VARCHAR(10)   NOT NULL,
    weekend_admission         SMALLINT      NOT NULL CHECK (weekend_admission IN (0, 1)),
    age                       SMALLINT      NOT NULL CHECK (age BETWEEN 0 AND 110),
    age_group                 VARCHAR(12)   NOT NULL,        -- Child / Young Adult / Adult / Senior
    gender                    VARCHAR(10)   NOT NULL,
    insurance_type            VARCHAR(15)   NOT NULL,        -- NHIS / HMO / Private / Out-of-Pocket
    department                VARCHAR(15)   NOT NULL,        -- from ward_type
    bed_type                  VARCHAR(10)   NOT NULL,        -- General / Private / ICU
    is_icu_admission          SMALLINT      NOT NULL CHECK (is_icu_admission IN (0, 1)),
    treatment_type            VARCHAR(12)   NOT NULL,        -- Medical / Surgical / Observation (proxy)
    primary_diagnosis         VARCHAR(20)   NOT NULL,
    secondary_diagnosis       VARCHAR(20)   NOT NULL,        -- 'No secondary' when absent
    num_procedures            SMALLINT      NOT NULL,
    num_medications           SMALLINT      NOT NULL,
    length_of_stay_days       SMALLINT      NOT NULL CHECK (length_of_stay_days > 0),
    total_cost_ngn            DECIMAL(12,2) NOT NULL,
    amount_paid_ngn           DECIMAL(12,2) NOT NULL,
    outstanding_ngn           DECIMAL(12,2) NOT NULL,
    collection_rate           DECIMAL(6,4)  NOT NULL,
    cost_per_day              DECIMAL(12,2) NOT NULL,
    discharge_outcome         VARCHAR(20)   NOT NULL,        -- Recovered / Referred / Died / Left Against Advice
    died                      SMALLINT      NOT NULL CHECK (died IN (0, 1)),
    readmitted_within_30_days SMALLINT      NOT NULL CHECK (readmitted_within_30_days IN (0, 1)),
    attending_doctor_id       VARCHAR(10)   NOT NULL,
    nurse_ratio               DECIMAL(4,1)  NOT NULL
);

CREATE INDEX idx_adm_hospital  ON admissions (hospital_id);
CREATE INDEX idx_adm_diagnosis ON admissions (primary_diagnosis);
CREATE INDEX idx_adm_doctor    ON admissions (attending_doctor_id);
CREATE INDEX idx_adm_month     ON admissions (admission_month);
