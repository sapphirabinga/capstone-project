# Data Dictionary

**Source file:** `data/project3_hospital_patients.xlsx` (200 rows × 20 columns), also saved as `data/project3_hospital_outcomes.csv`
**Cleaned file:** `data/cleaned_admissions.csv` (200 rows × 33 columns), produced by `python/01_cleaning_and_eda.ipynb`
**SQL table:** `admissions` (`sql/schema.sql`) · **Views:** `vw_hospital_outcomes_summary`, `vw_admissions_detail` (`sql/views.sql`)
**Grain:** one row = one hospital admission. Admission window 5 Jan 2022 to 31 Oct 2024.

## Columns in the cleaned table

| Column | Type | Origin | Description / values |
|---|---|---|---|
| `admission_id` | text | **created** | `ADM0001`–`ADM0200`, unique key (not in the supplied file) |
| `patient_id` | text | source | Patient identifier. Can repeat in principle; in this extract all 200 are unique |
| `hospital_id` | text | source | Facility, `HOSP001`–`HOSP020` (stands in for the brief's `hospital_name`) |
| `state` | text | source | Patient's state (10 states; hospitals serve patients from 4–10 states) |
| `admission_date` | date | source | Parsed with `pd.to_datetime` |
| `discharge_date` | date | source | Parsed with `pd.to_datetime` |
| `admission_month` | text | engineered | `YYYY-MM` |
| `admission_quarter` | text | engineered | `YYYYQn` |
| `admission_weekday` | text | engineered | Monday … Sunday |
| `weekend_admission` | 0/1 | **engineered (required)** | 1 if admitted Saturday or Sunday |
| `age` | int | source | Years, 1–90 |
| `age_group` | text | **engineered (required)** | `pd.cut(age, [0,18,35,60,100])`: Child (≤18), Young Adult (19–35), Adult (36–60), Senior (61+) |
| `gender` | text | source | Female / Male |
| `insurance_type` | text | source | NHIS, HMO, Private, Out-of-Pocket |
| `department` | text | source `ward_type` | General, ICU, Paediatric, Private, Maternity. ⚠️ See data quality note |
| `bed_type` | text | engineered | ICU → ICU, Private → Private, all other wards → General |
| `is_icu_admission` | 0/1 | **engineered (required)** | 1 if department = ICU |
| `treatment_type` | text | engineered **proxy** | Surgical (Appendicitis, Fracture), Observation (non-surgical with 0 procedures), Medical (rest). Not in source |
| `primary_diagnosis` | text | source `diagnosis_primary` | 10 categories: HIV/AIDS, Pneumonia, Fracture, Diabetes, Typhoid, Anaemia, Malaria, Hypertension, Tuberculosis, Appendicitis |
| `secondary_diagnosis` | text | source `diagnosis_secondary` | Same 10 categories or `No secondary` (22 nulls + 21 rows that repeated the primary) |
| `num_procedures` | int | source | 0–8 |
| `num_medications` | int | source | 0–10 |
| `length_of_stay_days` | int | source, **verified** | Recomputed as discharge − admission; matched on all rows; range 1–45, never 0 |
| `total_cost_ngn` | money | source `total_bill_naira` | Total billed, ₦ |
| `amount_paid_ngn` | money | source `amount_paid_naira` | Amount collected, ₦ (never exceeds bill) |
| `outstanding_ngn` | money | engineered | `total_cost_ngn − amount_paid_ngn` |
| `collection_rate` | 0–1 | engineered | `amount_paid_ngn / total_cost_ngn` |
| `cost_per_day` | money | **engineered (required)** | `total_cost_ngn / length_of_stay_days` (LOS checked > 0 first) |
| `discharge_outcome` | text | source `discharge_status` | Recovered (was Discharged), Referred, Died (was Deceased), Left Against Advice (was LAMA) |
| `died` | 0/1 | engineered | 1 if discharge_outcome = Died. Died rows are valid and kept |
| `readmitted_within_30_days` | 0/1 | source `readmission_30_days` | 1 = readmitted within 30 days |
| `attending_doctor_id` | text | source `doctor_id` | 48 doctors; each works across 1–8 hospitals |
| `nurse_ratio` | decimal | source | Patients per nurse on the ward, 1.1–9.9 |

## Brief columns not in the supplied data
| Brief column | Status |
|---|---|
| `satisfaction_score` | **Missing.** Not imputed or invented. Recovery rate used as proxy on the scorecard |
| `hospital_name` | Missing; `hospital_id` used |
| `treatment_type` | Missing; proxy derived (above) |
| `bed_type` | Missing; derived from `ward_type` (above) |
| `admission_id` | Missing; created |

## Data quality notes
1. **Size:** 200 admissions, not the 3,000 stated in the brief. Hospitals have 5–18 admissions and doctors 1–9, so facility and doctor rates have wide uncertainty.
2. **Ward vs patient mismatch:** 34 of 40 Paediatric patients are aged 18+, 15 of 30 Maternity patients are male, and 24 of 30 children were admitted outside Paediatrics. Department-level results should not be acted on until ward coding is confirmed.
3. **Uniform distributions:** age, LOS and cost are roughly flat, and LOS has no correlation with cost (r = −0.06). Both are unusual for real hospital data and suggest synthetic records.
4. **Very high rates:** 30-day readmission 54.5% and in-hospital mortality 22.5% are several times typical benchmarks. Confirm the definitions before quoting them externally.
