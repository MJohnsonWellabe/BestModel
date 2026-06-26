"""Generate the seed CSVs from the analyst data-entry template.

Reads templates/sp_pull_template.xlsx and emits:
  - data/variable_dictionary.csv  (from the 'Data Dictionary' sheet)
  - data/carriers_seed.csv        (from the 'Carrier Roster + Assessments' sheet)

These are committed reference files; the pipeline validates pulled data against
the dictionary and uses the roster for carrier identity + stratification tags.
"""
from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "sp_pull_template.xlsx"
DATA = ROOT / "data"


def _rows(ws):
    for r in ws.iter_rows(values_only=True):
        cells = ["" if c is None else str(c).strip() for c in r]
        while cells and cells[-1] == "":
            cells.pop()
        yield cells


def make_dictionary(wb):
    ws = wb["Data Dictionary"]
    out = DATA / "variable_dictionary.csv"
    rows = [r for r in _rows(ws) if r]
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
    print(f"wrote {out.relative_to(ROOT)} ({len(rows)-1} fields)")


def make_roster(wb):
    ws = wb["Carrier Roster + Assessments"]
    out = DATA / "carriers_seed.csv"
    rows = [r for r in _rows(ws) if r]
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
    print(f"wrote {out.relative_to(ROOT)} ({len(rows)-1} carriers)")


def main():
    wb = openpyxl.load_workbook(TEMPLATE, data_only=True)
    DATA.mkdir(exist_ok=True)
    make_dictionary(wb)
    make_roster(wb)


if __name__ == "__main__":
    main()
