"""Load data/cleaned_admissions.csv into a SQLite database and build the views.

Usage (run from the repo root):
    python python/load_to_sql.py

Creates data/hospital_outcomes.db. Open it with DB Browser for SQLite,
DBeaver, or the VS Code SQLite extension and run sql/queries.sql.
Power BI can read it through the SQLite ODBC driver (see powerbi/BUILD_GUIDE.md).
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "hospital_outcomes.db"

df = pd.read_csv(ROOT / "data" / "cleaned_admissions.csv")

with sqlite3.connect(DB) as con:
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    df.to_sql("admissions", con, if_exists="append", index=False)
    con.executescript((ROOT / "sql" / "views.sql").read_text())
    n = con.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
    v = con.execute("SELECT SUM(admissions) FROM vw_hospital_outcomes_summary").fetchone()[0]

print(f"Loaded {n} admissions into {DB.name}; summary view covers {v} admissions.")
assert n == v == len(df), "row counts do not reconcile"
