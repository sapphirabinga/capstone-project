"""Build excel/hospital_scorecard.xlsx from data/cleaned_admissions.csv.

Every number on the Scorecard and By Diagnosis sheets is a live Excel formula
(COUNTIF / COUNTIFS / AVERAGEIF / SUMIF) over the Data sheet, so the workbook
recalculates if the data is replaced. Upload to Google Sheets works as-is.

Usage (from repo root):  python python/build_scorecard.py
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "cleaned_admissions.csv", parse_dates=["admission_date"])

F = "Arial"
NAVY, INK, MUTED, LINE = "0D366B", "1F1F1F", "6B6A66", "D9D8D3"
HEAD_FILL = PatternFill("solid", fgColor=NAVY)
NET_FILL = PatternFill("solid", fgColor="E8F0FB")
TILE_FILL = PatternFill("solid", fgColor="F4F8FD")
RED_FILL = PatternFill("solid", fgColor="F8D7DA")
RED_FONT = Font(name=F, color="9C0006", bold=True)
thin = Side(style="thin", color=LINE)
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
BOTTOM = Border(bottom=thin)


def font(size=10, bold=False, color=INK, italic=False):
    return Font(name=F, size=size, bold=bold, color=color, italic=italic)


wb = Workbook()

# ---------------------------------------------------------------- Data sheet
data = wb.active
data.title = "Data"
cols = ["admission_id", "hospital_id", "admission_date", "primary_diagnosis", "department",
        "bed_type", "insurance_type", "age_group", "length_of_stay_days",
        "readmitted_within_30_days", "discharge_outcome", "total_cost_ngn", "amount_paid_ngn",
        "attending_doctor_id"]
d = df[cols].sort_values("admission_id")
data.append(cols)
for row in d.itertuples(index=False):
    r = list(row)
    r[2] = r[2].to_pydatetime().date()
    data.append(r)
N = len(d) + 1  # last data row
for c in data[1]:
    c.font = font(bold=True, color="FFFFFF"); c.fill = HEAD_FILL
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for row in data.iter_rows(min_row=2, max_row=N):
    for c in row:
        c.font = font()
    row[2].number_format = "yyyy-mm-dd"
    row[11].number_format = "#,##0"; row[12].number_format = "#,##0"
widths = [13, 11, 12, 17, 12, 10, 14, 12, 10, 11, 20, 14, 14, 11]
for i, w in enumerate(widths, 1):
    data.column_dimensions[get_column_letter(i)].width = w
data.row_dimensions[1].height = 32
data.freeze_panes = "A2"
tbl = Table(displayName="Admissions", ref=f"A1:{get_column_letter(len(cols))}{N}")
tbl.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
data.add_table(tbl)

# absolute ranges on the Data sheet
R = lambda col: f"Data!${col}$2:${col}${N}"
HOSP, DX, LOS, READ, OUT, COST, PAID = (R(c) for c in "BDIJKLM")

# ---------------------------------------------------------------- Scorecard
sc = wb.create_sheet("Scorecard", 0)
sc.sheet_view.showGridLines = False
sc["A1"] = "Hospital Performance Scorecard"
sc["A1"].font = font(18, True, NAVY)
sc["A2"] = (f"Network of {df.hospital_id.nunique()} hospitals  ·  {len(df)} admissions  ·  "
            f"{df.admission_date.min():%b %Y} to {df.admission_date.max():%b %Y}  ·  "
            "Red = worse than network average")
sc["A2"].font = font(10, color=MUTED)

# KPI tiles (rows 4-5) - reference the network row
first, last = 10, 10 + df.hospital_id.nunique() - 1
NET = last + 1
tiles = [("Admissions", f"=B{NET}", "#,##0"), ("Avg length of stay (days)", f"=C{NET}", "0.0"),
         ("30-day readmission", f"=D{NET}", "0.0%"), ("Mortality rate", f"=E{NET}", "0.0%"),
         ("Recovery rate", f"=F{NET}", "0.0%"), ("Avg cost / admission (₦)", f"=G{NET}", "#,##0"),
         ("Collection rate", f"=H{NET}", "0.0%")]
for i, (lab, f_, fmt) in enumerate(tiles):
    col = get_column_letter(i + 2)
    a, b = sc[f"{col}4"], sc[f"{col}5"]
    a.value, b.value = lab, f_
    a.font = font(8.5, color=MUTED); b.font = font(15, True, NAVY)
    b.number_format = fmt
    for c in (a, b):
        c.fill = TILE_FILL; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
sc.row_dimensions[4].height = 26; sc.row_dimensions[5].height = 30

sc["A7"] = ("Note: satisfaction_score is not in the supplied dataset, so Recovery rate "
            "(share discharged as Recovered) is shown as the patient-experience proxy.")
sc["A7"].font = font(8.5, italic=True, color=MUTED)

# Hospital table
heads = ["Hospital", "Admissions", "Avg LOS (days)", "Readmission rate", "Mortality rate",
         "Recovery rate", "Avg cost per admission (₦)", "Collection rate", "Red flags (of 6)", "Volume"]
for i, h in enumerate(heads, 1):
    c = sc.cell(row=9, column=i, value=h)
    c.font = font(9.5, True, "FFFFFF"); c.fill = HEAD_FILL; c.border = BOX
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
sc.row_dimensions[9].height = 34

for r, h in enumerate(sorted(df.hospital_id.unique()), start=first):
    sc[f"A{r}"] = h
    sc[f"B{r}"] = f"=COUNTIF({HOSP},A{r})"
    sc[f"C{r}"] = f"=AVERAGEIF({HOSP},A{r},{LOS})"
    sc[f"D{r}"] = f"=COUNTIFS({HOSP},A{r},{READ},1)/B{r}"
    sc[f"E{r}"] = f'=COUNTIFS({HOSP},A{r},{OUT},"Died")/B{r}'
    sc[f"F{r}"] = f'=COUNTIFS({HOSP},A{r},{OUT},"Recovered")/B{r}'
    sc[f"G{r}"] = f"=AVERAGEIF({HOSP},A{r},{COST})"
    sc[f"H{r}"] = f"=SUMIF({HOSP},A{r},{PAID})/SUMIF({HOSP},A{r},{COST})"
    sc[f"I{r}"] = (f"=(C{r}>$C${NET})+(D{r}>$D${NET})+(E{r}>$E${NET})"
                   f"+(F{r}<$F${NET})+(G{r}>$G${NET})+(H{r}<$H${NET})")
    sc[f"J{r}"] = f'=IF(B{r}<8,"Low (<8)","OK")'

sc[f"A{NET}"] = "Network average"
sc[f"B{NET}"] = f"=COUNTA({R('A')})"
sc[f"C{NET}"] = f"=AVERAGE({LOS})"
sc[f"D{NET}"] = f"=COUNTIF({READ},1)/B{NET}"
sc[f"E{NET}"] = f'=COUNTIF({OUT},"Died")/B{NET}'
sc[f"F{NET}"] = f'=COUNTIF({OUT},"Recovered")/B{NET}'
sc[f"G{NET}"] = f"=AVERAGE({COST})"
sc[f"H{NET}"] = f"=SUM({PAID})/SUM({COST})"
sc[f"I{NET}"] = "—"; sc[f"J{NET}"] = "—"

fmts = {"B": "#,##0", "C": "0.0", "D": "0.0%", "E": "0.0%", "F": "0.0%", "G": "#,##0", "H": "0.0%", "I": "0"}
for r in range(first, NET + 1):
    for col in "ABCDEFGHIJ":
        c = sc[f"{col}{r}"]
        c.border = BOX
        c.font = font(10, bold=(r == NET or col == "A"))
        c.alignment = Alignment(horizontal="left" if col == "A" else "center", vertical="center")
        if col in fmts: c.number_format = fmts[col]
        if r == NET: c.fill = NET_FILL

# Conditional formatting: red where the hospital is worse than the network average
rng = lambda col: f"{col}{first}:{col}{last}"
worse = {"C": ">", "D": ">", "E": ">", "F": "<", "G": ">", "H": "<"}
for col, op in worse.items():
    sc.conditional_formatting.add(rng(col), FormulaRule(
        formula=[f"{col}{first}{op}${col}${NET}"], fill=RED_FILL, font=RED_FONT))
sc.conditional_formatting.add(rng("I"), FormulaRule(formula=[f"I{first}>=4"], fill=RED_FILL, font=RED_FONT))
sc.conditional_formatting.add(rng("J"), FormulaRule(formula=[f'J{first}="Low (<8)"'],
                              font=Font(name=F, color=MUTED, italic=True)))

notes_row = NET + 2
notes = [
    "How to read: a red cell means the hospital is worse than the network average on that measure "
    "(higher LOS, readmission, mortality or cost; lower recovery or collection).",
    "Red flags counts how many of the 6 measures are red; 4 or more is highlighted. "
    "Hospitals marked Low (<8) have too few admissions for reliable rates.",
    "All figures are live formulas (COUNTIF, COUNTIFS, AVERAGEIF, SUMIF) on the Data sheet. "
    "Source: data/cleaned_admissions.csv, built by python/01_cleaning_and_eda.ipynb.",
]
for i, t in enumerate(notes):
    c = sc[f"A{notes_row + i}"]; c.value = t; c.font = font(8.5, color=MUTED)

for col, w in zip("ABCDEFGHIJ", [16, 11, 11, 13, 12, 12, 15, 12, 11, 11]):
    sc.column_dimensions[col].width = w
sc.freeze_panes = "B10"
sc.page_setup.orientation = "landscape"
sc.page_setup.paperSize = sc.PAPERSIZE_A4
sc.page_setup.fitToWidth = 1; sc.page_setup.fitToHeight = 1
sc.sheet_properties.pageSetUpPr.fitToPage = True
sc.print_area = f"A1:J{notes_row + len(notes) - 1}"
sc.page_margins.left = sc.page_margins.right = 0.4

# ---------------------------------------------------------------- By Diagnosis
dx = wb.create_sheet("By Diagnosis", 1)
dx.sheet_view.showGridLines = False
dx["A1"] = "Outcomes by Primary Diagnosis"; dx["A1"].font = font(16, True, NAVY)
dx["A2"] = "Red = worse than network average. Live COUNTIFS / AVERAGEIF formulas on the Data sheet."
dx["A2"].font = font(9, color=MUTED)
dh = ["Diagnosis", "Admissions", "Avg LOS (days)", "Readmission rate", "Mortality rate", "Avg cost (₦)"]
for i, h in enumerate(dh, 1):
    c = dx.cell(row=4, column=i, value=h)
    c.font = font(9.5, True, "FFFFFF"); c.fill = HEAD_FILL; c.border = BOX
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
dxs = df.primary_diagnosis.value_counts().index.tolist()
d1, d2 = 5, 5 + len(dxs) - 1
DN = d2 + 1
for r, name in enumerate(dxs, start=d1):
    dx[f"A{r}"] = name
    dx[f"B{r}"] = f"=COUNTIF({DX},A{r})"
    dx[f"C{r}"] = f"=AVERAGEIF({DX},A{r},{LOS})"
    dx[f"D{r}"] = f"=COUNTIFS({DX},A{r},{READ},1)/B{r}"
    dx[f"E{r}"] = f'=COUNTIFS({DX},A{r},{OUT},"Died")/B{r}'
    dx[f"F{r}"] = f"=AVERAGEIF({DX},A{r},{COST})"
dx[f"A{DN}"] = "Network average"
dx[f"B{DN}"] = f"=SUM(B{d1}:B{d2})"
dx[f"C{DN}"] = f"=AVERAGE({LOS})"
dx[f"D{DN}"] = f"=COUNTIF({READ},1)/B{DN}"
dx[f"E{DN}"] = f'=COUNTIF({OUT},"Died")/B{DN}'
dx[f"F{DN}"] = f"=AVERAGE({COST})"
dfm = {"B": "#,##0", "C": "0.0", "D": "0.0%", "E": "0.0%", "F": "#,##0"}
for r in range(d1, DN + 1):
    for col in "ABCDEF":
        c = dx[f"{col}{r}"]; c.border = BOX; c.font = font(10, bold=(r == DN or col == "A"))
        c.alignment = Alignment(horizontal="left" if col == "A" else "center")
        if col in dfm: c.number_format = dfm[col]
        if r == DN: c.fill = NET_FILL
for col in "CDEF":
    dx.conditional_formatting.add(f"{col}{d1}:{col}{d2}", FormulaRule(
        formula=[f"{col}{d1}>${col}${DN}"], fill=RED_FILL, font=RED_FONT))

# Hospital x diagnosis admissions matrix (COUNTIFS)
m0 = DN + 3
dx[f"A{m0 - 1}"] = "Admissions by hospital and diagnosis (COUNTIFS)"
dx[f"A{m0 - 1}"].font = font(12, True, NAVY)
dx.cell(row=m0, column=1, value="Hospital")
for j, name in enumerate(dxs, start=2):
    dx.cell(row=m0, column=j, value=name)
dx.cell(row=m0, column=len(dxs) + 2, value="Total")
for c in dx[m0]:
    if c.value is not None:
        c.font = font(9, True, "FFFFFF"); c.fill = HEAD_FILL; c.border = BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
dx.row_dimensions[m0].height = 30
hosps = sorted(df.hospital_id.unique())
for i, h in enumerate(hosps, start=m0 + 1):
    dx.cell(row=i, column=1, value=h).font = font(10, True)
    for j in range(2, len(dxs) + 2):
        col = get_column_letter(j)
        c = dx.cell(row=i, column=j, value=f"=COUNTIFS({HOSP},$A{i},{DX},{col}${m0})")
        c.font = font(); c.alignment = Alignment(horizontal="center"); c.border = BOX
    tc = get_column_letter(len(dxs) + 2)
    t = dx.cell(row=i, column=len(dxs) + 2, value=f"=SUM(B{i}:{get_column_letter(len(dxs) + 1)}{i})")
    t.font = font(bold=True); t.alignment = Alignment(horizontal="center"); t.border = BOX
    dx.cell(row=i, column=1).border = BOX
mlast = m0 + len(hosps)
dx.conditional_formatting.add(f"B{m0 + 1}:{get_column_letter(len(dxs) + 1)}{mlast}",
                              ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                                             end_type="max", end_color="86B6EF"))
dx.column_dimensions["A"].width = 16
for j in range(2, len(dxs) + 3):
    dx.column_dimensions[get_column_letter(j)].width = 12.5
dx.page_setup.orientation = "landscape"; dx.sheet_properties.pageSetUpPr.fitToPage = True
dx.page_setup.fitToWidth = 1; dx.page_setup.fitToHeight = 1

# ---------------------------------------------------------------- Notes
nt = wb.create_sheet("Notes")
nt.sheet_view.showGridLines = False
rows = [
    ("Hospital Scorecard: definitions", None),
    ("Avg LOS", "AVERAGEIF of length_of_stay_days (discharge date minus admission date)."),
    ("Readmission rate", "COUNTIFS(readmitted_within_30_days = 1) / admissions."),
    ("Mortality rate", 'COUNTIFS(discharge_outcome = "Died") / admissions.'),
    ("Recovery rate", 'COUNTIFS(discharge_outcome = "Recovered") / admissions. Proxy for satisfaction_score, which is not in the supplied data.'),
    ("Avg cost per admission", "AVERAGEIF of total_cost_ngn (total billed, naira)."),
    ("Collection rate", "SUMIF(amount_paid) / SUMIF(total_cost): share of the bill actually collected."),
    ("Network average", "Computed over all admissions (not an average of hospital averages), so large hospitals weigh more."),
    ("Red flag", "Cell is worse than the network average. Higher is worse for LOS, readmission, mortality, cost; lower is worse for recovery, collection."),
    ("Low volume", "Fewer than 8 admissions: one patient moves a rate by more than 12 points, so treat with caution."),
    ("Data", "Data sheet = data/cleaned_admissions.csv (200 admissions, 2022-01 to 2024-10). Replace rows to refresh; formulas cover rows 2 to %d." % N),
    ("Google Sheets", "File > Import > Upload this .xlsx; formulas and conditional formatting carry over."),
]
for i, (k, v) in enumerate(rows, start=1):
    nt.cell(row=i, column=1, value=k).font = font(14 if v is None else 10, True, NAVY if v is None else INK)
    if v:
        c = nt.cell(row=i, column=2, value=v); c.font = font(); c.alignment = Alignment(wrap_text=True, vertical="top")
        nt.cell(row=i, column=1).alignment = Alignment(vertical="top")
nt.column_dimensions["A"].width = 22; nt.column_dimensions["B"].width = 95

out = ROOT / "excel" / "hospital_scorecard.xlsx"
wb.save(out)
print("saved", out)
