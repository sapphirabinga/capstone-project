# Key Findings: Hospital Patient Outcomes

**Data:** 200 admissions · 20 hospitals · 48 doctors · Jan 2022 to Oct 2024
**Method:** Python (pandas, scipy) for cleaning, features and statistical tests; SQL for the required aggregations; numbers cross-checked across Python, SQL and Excel.
**Significance rule:** p < 0.05. Small groups are reported with their sample size **n**.

> **Read this first.** The supplied file differs from the brief (200 rows, not 3,000; no satisfaction score), and ward labels don't match the patients (34 of 40 "Paediatric" patients are adults; 15 of 30 "Maternity" patients are male). Findings below describe this dataset honestly, and the first recommendation is to fix data capture before making clinical decisions.

## Headline numbers

| Measure | Value |
|---|---|
| Admissions | 200 |
| 30-day readmission rate | **54.5%** (95% CI 47.6–61.3%) |
| In-hospital mortality | **22.5%** |
| Left against medical advice | **24.5%** |
| Average length of stay | 23.2 days |
| Average bill per admission | ₦426,306 |
| Collected / billed | ₦56.4m / ₦85.3m = **66.2%** (₦28.8m outstanding) |

---

## Answers to the 10 key questions

### 1. What is the overall 30-day readmission rate?
**54.5%** (109 of 200), 95% confidence interval 47.6–61.3%. That is roughly 3–5× typical published rates (10–20%), so either the flag counts any return visit or the data is synthetic. Quarterly rates range from 40.0% (2023 Q3) to 75.0% (2024 Q4). The upward slope (+1.5 points a quarter) is **not significant** (p = 0.11), so we cannot call it a rising trend yet. *(Chart: `images/readmission_trend.png`)*

### 2. Which diagnosis has the highest readmission rate? Why?
**Malaria: 66.7%** (12 of 18), then Typhoid 63.6%, Diabetes 60.9%, Appendicitis 60.0%. Lowest: Hypertension and Tuberculosis, 40.0% each.
**Statistical test:** chi-square of diagnosis × readmission, χ² = 5.62, p = 0.78. The differences are **not significant**: we cannot reject the hypothesis that all diagnoses carry the same readmission risk.
**Plausible explanations if it holds on more data:** malaria and typhoid recur when patients don't finish their antimalarial/antibiotic course after discharge (cost, stock-outs) or go back to the same exposure (mosquitoes, unsafe water). Diabetes readmissions usually reflect poor glucose control at home and weak outpatient follow-up.

### 3. Is there a significant difference in length of stay between insurance types?
| Insurance | n | Mean LOS | Median LOS |
|---|---|---|---|
| HMO | 49 | 26.0 | 26.0 |
| NHIS | 52 | 25.6 | 25.5 |
| Private | 43 | 21.7 | 19.0 |
| Out-of-Pocket | 56 | 19.6 | 15.5 |

ANOVA p = 0.049 (just significant); Kruskal-Wallis p = 0.057 (just not). The evidence is **borderline**: out-of-pocket patients appear to stay about 6 days less than insured patients. This fits the idea that self-paying patients ask to go home early to limit the bill. Worth retesting on the full dataset.

### 4. Which hospital has the highest and lowest patient satisfaction score?
**Cannot be answered: `satisfaction_score` is not in the supplied data**, and no scores were invented. Using **recovery rate** as a proxy (hospitals with ≥ 8 admissions):
* Highest: **HOSP013**, 37.5% recovered (n = 16). *HOSP002 is 71.4% but on only 7 admissions.*
* Lowest: **HOSP020**, 9.1% recovered (n = 11).
* Highest mortality: **HOSP004**, 41.2% (7 of 17). HOSP012 had no deaths (n = 13).

### 5. Mortality rate by department: where is the most room for improvement?
| Department | n | Deaths | Mortality | Excess deaths vs network rate |
|---|---|---|---|---|
| Paediatric | 40 | 14 | **35.0%** | **+5.0** |
| ICU | 42 | 10 | 23.8% | +0.5 |
| Maternity | 30 | 7 | 23.3% | +0.2 |
| General | 51 | 9 | 17.6% | −2.5 |
| Private | 37 | 5 | 13.5% | −3.3 |

**Paediatrics** has the most room for improvement: the highest rate and 5 more deaths than the network rate predicts. Chi-square p = 0.20, so this is not statistically conclusive. Also, 34 of its 40 patients are adults, so the ward label itself needs checking. A **mortality case review** of those 14 deaths is the right next step.

### 6. Is there a relationship between weekend admissions and discharge outcomes?
| | n | Died | Left against advice | Recovered | Referred |
|---|---|---|---|---|---|
| Weekday | 136 | 27.2% | 20.6% | 26.5% | 25.7% |
| Weekend | 64 | **12.5%** | **32.8%** | 23.4% | 31.2% |

Across all four outcomes the link is borderline (χ² p = 0.058). Weekend admissions had **lower** mortality (12.5% vs 27.2%, p = 0.032). That is the opposite of the classic "weekend effect" and is fragile given the number of tests run here. The more useful operational signal: **1 in 3 weekend admissions leave against medical advice**, versus 1 in 5 on weekdays.

### 7. Average cost per patient day: ICU vs General ward?
| Bed type | Pooled ₦ / bed-day | Median ₦ / day | n |
|---|---|---|---|
| ICU | **₦20,529** | ₦23,874 | 42 |
| General | **₦17,799** | ₦16,821 | 121 |
| Private | ₦18,141 | ₦18,152 | 37 |

ICU is about **15% more** per bed-day than General (pooled), but the difference is **not significant** (Mann-Whitney p = 0.36). In real hospitals ICU typically costs several times a general bed, which supports the view that billing here doesn't reflect intensity of care. LOS and total bill are also uncorrelated (r = −0.06). *Pooled = total billed ÷ total bed-days. The mean of per-admission cost/day (₦41k–42k) is inflated by short, expensive stays.*

### 8. Which age group accounts for the most admissions? What are their main diagnoses?
**Seniors (61+): 75 admissions (37.5%)**, then Adults 48, Young Adults 42, Children 35.
Seniors' top diagnoses: **HIV/AIDS (13)**, Fracture (10), Pneumonia (9), Malaria (7), Anaemia (7). Fractures and pneumonia fit an older population (falls, weaker immunity). HIV/AIDS at the top suggests an ageing cohort living with HIV who need chronic-care pathways.
Readmission by age: Young Adults have the highest rate (71.4%, n = 42), Children the lowest (34.3%, n = 35).

### 9. Are certain doctors associated with higher readmission rates?
Each doctor was benchmarked against the average readmission rate of the hospitals they worked in, then tested with a binomial test and a funnel plot. *(Chart: `images/doctor_funnel.png`)*
* 21 of 48 doctors are above their expected rate, about what chance alone would produce.
* **No doctor is statistically outside the 95% control limits.**
* Doctors closest to the limit, worth monitoring: **DR011** and **DR044**, each 7 of 8 patients readmitted (87.5% vs 49.5% and 54.1% expected, p ≈ 0.06). Next: DR045, DR021 (5 of 6 each) and DR006 (4 of 5).

Treat this as a watch-list for case-mix review, not a performance judgement: 8 patients is too few to separate skill from case mix or luck.

### 10. Three operational recommendations
See `executive_brief.md` for the version addressed to the executive committee.
1. **Fix the data before the next decision.** Correct ward/department coding, start recording patient satisfaction at discharge, and define "readmission" (unplanned, same condition, within 30 days). In parallel, run a mortality case review of the 14 Paediatric deaths and HOSP004 (7 deaths in 17 admissions).
2. **Launch a discharge-and-follow-up programme to cut readmissions,** starting with NHIS patients (65.4% readmitted vs 44.9% for HMO) and the infectious and chronic diagnoses (malaria, typhoid, diabetes): give the full medication course before discharge, make a follow-up call at 7 days, and book a clinic review. Track the doctor funnel plot monthly.
3. **Reduce leaving-against-advice and close the revenue gap.** 24.5% of patients leave against advice (32.8% at weekends). Add weekend senior cover and discharge counselling, and give cost estimates at admission. Only 66.2% of billing is collected (₦28.8m outstanding); HMO and Private payers collect the least (about 64%), so introduce pre-authorisation and claims follow-up.

---

## Statistical tests summary
| Hypothesis | Test | Statistic | p | Verdict |
|---|---|---|---|---|
| Readmission depends on diagnosis | Chi-square | χ² = 5.62 | 0.778 | Not supported |
| Readmission depends on insurance type | Chi-square | χ² = 4.52 | 0.211 | Not supported |
| LOS differs by insurance type | ANOVA / Kruskal-Wallis | F = 2.67 / H = 7.53 | 0.049 / 0.057 | Borderline |
| Mortality differs by department | Chi-square | χ² = 6.04 | 0.196 | Not supported |
| Weekend admission linked to outcome | Chi-square | χ² = 7.48 | 0.058 | Borderline |
| Weekend admission linked to death | Chi-square | χ² = 4.59 | 0.032 | Significant (fragile) |
| ICU cost/day differs from General | Mann-Whitney U | U = 2784 | 0.357 | Not supported |
| LOS correlates with total cost | Pearson | r = −0.06 | 0.408 | No relationship |
| Readmission trend over time | Linear regression on quarters | +1.46 pts/qtr | 0.112 | No significant trend |
| Any doctor unusually high | Binomial / funnel | n/a | min ≈ 0.06 | None outside limits |

## Limitations
* 200 rows: most tests have low power, so "not significant" means "not proven", not "no effect".
* Many tests were run; at p < 0.05, about 1 in 20 true-null tests will look significant by chance.
* Department labels are unreliable (see data dictionary). Satisfaction score is absent.
* Distributions are near-uniform, which suggests synthetic data. Methods carry over to the full 3,000-row file unchanged: re-run the notebooks.
