# Power BI Build Guide: `clinical_dashboard.pbix`

A `.pbix` file can only be created in **Power BI Desktop** (free, Windows). This guide walks you through building the 4-page dashboard plus the drill-through page, step by step. Allow 2–3 hours.

Files you need from this folder:
* `measures.dax`: every DAX measure, ready to paste
* `theme.json`: colour theme (blue palette, red for "worse than average")

When finished, save as `powerbi/clinical_dashboard.pbix`, export a PDF (*File > Export > PDF*) to `powerbi/clinical_dashboard.pdf`, and take a screenshot of each page into `docs/images/` for the README.

---

## Step 1. Get the data in

**Option A: CSV (simplest, recommended)**
1. *Home > Get data > Text/CSV* > choose `data/cleaned_admissions.csv` > **Transform Data**.
2. In Power Query, check the column types:
   * `admission_date`, `discharge_date` → **Date**
   * `total_cost_ngn`, `amount_paid_ngn`, `outstanding_ngn`, `cost_per_day` → **Fixed decimal number**
   * `weekend_admission`, `is_icu_admission`, `died`, `readmitted_within_30_days`, `length_of_stay_days`, `age` → **Whole number**
   * `collection_rate` → **Decimal number**
3. Rename the query to **Admissions**, then *Close & Apply*.

**Option B: connect to the SQL view (what the brief describes)**
1. Run `python python/load_to_sql.py` to create `data/hospital_outcomes.db`.
2. Install the free **SQLite ODBC driver** (search "SQLite ODBC driver ch-werner"), then create a DSN pointing to the `.db` file.
3. *Get data > ODBC* > choose the DSN > select **vw_admissions_detail** (rename to `Admissions`) and **vw_hospital_outcomes_summary**.
   If you use PostgreSQL/MySQL/SQL Server instead, run `sql/schema.sql`, import the CSV, run `sql/views.sql`, and use that database's connector.

> Mention in your README which option you used. Option B scores better on "Connect to SQL view".

## Step 2. Model

1. *Modeling > New table* → paste the **Date** table from `measures.dax`.
2. Select the Date table > *Table tools > Mark as date table* > column `Date`.
3. In the Date table, select `Month` > *Sort by column* > `Month Number`.
4. *Model view*: drag `'Date'[Date]` onto `Admissions[admission_date]` (one-to-many, single direction).
5. In Admissions, select `age_group` > *Sort by column*: create a helper column first:
   `Age Order = SWITCH(Admissions[age_group], "Child",1, "Young Adult",2, "Adult",3, "Senior",4)` and sort `age_group` by it.
6. *Home > Enter data* → create an empty table called **_Measures**, then paste each measure from `measures.dax` via *New measure* with `_Measures` selected. Delete its blank column afterwards.
7. Format measures: rates → **Percentage, 1 decimal**; naira → **Whole number with thousands separator** (prefix ₦ in the visual title or via custom format `"₦"#,0`).

## Step 3. Theme

*View > Themes > Browse for themes* → `powerbi/theme.json`.

## Step 4. Slicers that appear on every page

Build these once on page 1, then copy-paste them to each page and choose **Sync** when prompted (*View > Sync slicers* to check):
* **Hospital** (`hospital_id`): dropdown, multi-select on
* **Date** (`'Date'[Date]`): "Between" slider
* **Diagnosis** (`primary_diagnosis`): dropdown

Put them in one row across the top of each page.

---

## Page 1: Admissions Overview

| Visual | Fields |
|---|---|
| 4 Cards | `Total Admissions`, `Unique Patients`, `Avg Length of Stay`, `Avg Cost per Admission` |
| Clustered bar | Y: `hospital_id` · X: `Total Admissions` · sort descending |
| Clustered bar | Y: `department` · X: `Total Admissions` |
| Line chart | X: `'Date'[Year-Month]` · Y: `Total Admissions` |
| Matrix (heatmap) | Rows: `department` · Columns: `'Date'[Month]` · Values: `Total Admissions` · *Cell elements > Background color* ON (light → dark blue) |

## Page 2: Patient Outcomes

| Visual | Fields |
|---|---|
| 4 Cards | `Mortality Rate`, `Recovery Rate`, `LAMA Rate`, `Referral Rate` |
| **100% stacked bar** (brief's hint) | Y: `department` · X: `Total Admissions` · Legend: `discharge_outcome` |
| Clustered bar | Y: `primary_diagnosis` · X: `Mortality Rate` · *Bars > Color > fx > Field value* = `Mortality Colour` (red if above network) |
| Clustered bar | Y: `department` · X: `Mortality Rate`, tooltip `Excess Deaths`, same colour rule |
| Clustered column | X: `admission_day_type` (or `'Date'[Is Weekend]`) · Y: `Mortality Rate`, `LAMA Rate` |

## Page 3: Readmissions Analysis

| Visual | Fields |
|---|---|
| Card + KPI | `Readmission Rate` vs target `Network Readmission Rate` |
| Clustered bar | Y: `primary_diagnosis` · X: `Readmission Rate` · colour = `Readmission Colour` |
| Clustered column | X: `age_group` · Y: `Readmission Rate` |
| Clustered column | X: `insurance_type` · Y: `Readmission Rate` |
| **Line chart (trend, "Impressive")** | X: `'Date'[Year-Month]` · Y: `Readmission Rate` and `Readmission Rate 3M Rolling` · *Analytics > Constant line* = 0.545 labelled "Network avg" |
| Table: doctor benchmark | `attending_doctor_id`, `Total Admissions`, `Readmission Rate`, `Doctor Expected Readmission`, `Doctor Gap vs Expected (pts)` · filter: `Total Admissions` ≥ 5 · conditional format the gap column (red if > 0) |

## Page 4: Financial and Operational Metrics

| Visual | Fields |
|---|---|
| Cards | `Total Billed`, `Total Collected`, `Collection Rate`, `Outstanding Balance` |
| Clustered column | X: `treatment_type` · Y: `Avg Cost per Admission` |
| Clustered column | X: `bed_type` · Y: `Avg Cost per Admission` and `Cost per Patient Day` (two small charts are cleaner than one) |
| Column chart (LOS distribution) | X: `los_band` (SQL view) **or** `length_of_stay_days` with *New group* bin size 7 · Y: `Total Admissions` |
| Clustered bar | Y: `insurance_type` · X: `Collection Rate` |
| Card pair | `ICU Cost per Day` vs `General Cost per Day` |

## Page 5: Hospital Detail (drill-through, "Impressive")

1. Add a new page called **Hospital Detail**.
2. In the *Visualizations* pane > *Drill through* well, drag `hospital_id`. Keep "Keep all filters" ON.
3. Add:
   * Card with `Selected Hospital` as the page title
   * Cards: `Total Admissions`, `Readmission Rate`, `Mortality Rate`, `Avg Length of Stay`, `Collection Rate`, plus `Readmission vs Network (pts)` and `Mortality vs Network (pts)`
   * **Matrix**: Rows `department` · Values `Total Admissions`, `Avg Length of Stay`, `Readmission Rate`, `Mortality Rate`, `Avg Cost per Admission`, with red conditional formatting where the rate is above network
   * 100% stacked bar: `department` × `discharge_outcome`
   * Table of doctors who treated patients at this hospital
4. Power BI adds a back arrow automatically.
5. **Test it:** on page 1, right-click a hospital bar > *Drill through > Hospital Detail*.

Add a text box on page 1: *"Right-click any hospital to drill through to its department breakdown."*

---

## Step 5. Final checks before you submit
- [ ] Hospital slicer filters every page (pick HOSP008: Readmission Rate should show **90.9%**)
- [ ] No-filter totals match the notebook: 200 admissions, readmission **54.5%**, mortality **22.5%**, avg LOS **23.2**
- [ ] Drill-through works from page 1 and page 2
- [ ] Every rate visual shows n somewhere (tooltip `Total Admissions`): many hospitals have < 10 admissions
- [ ] Saved as `powerbi/clinical_dashboard.pbix` + PDF export + page screenshots in `docs/images/`
