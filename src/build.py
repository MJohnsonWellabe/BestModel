"""Build the analysis frame: parse every raw S&P pull -> derive -> join labels -> data.json.

Run:  python src/build.py
Outputs:
  - tool/data.json                      (the frame the interactive tool + paper read)
  - data/processed/missingness.csv      (per-carrier field coverage, for QC)
Prints a coverage summary so the analyst sees gaps before analysing. Never invents values.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parse_sp_pull import normalize, parse_highlights  # noqa: E402
from features import build_record  # noqa: E402
import notching  # noqa: E402

RAW = ROOT / "data" / "raw"
ROSTER_CSV = ROOT / "data" / "carriers_seed.csv"
ASSESS_CSV = ROOT / "data" / "assessments.csv"
OUT_JSON = ROOT / "tool" / "data.json"
MISS_CSV = ROOT / "data" / "processed" / "missingness.csv"

ASSESSMENT_FIELDS = [
    "amb_number", "naic_code", "domicile_state", "fsr", "icr", "outlook", "under_review",
    "bs_assessment", "op_assessment", "bp_assessment", "erm_assessment",
    "rating_action_date", "last_action_type", "source_url", "rating_basis",
]
WELLABE_NAMES = {"wellabegroup", "medicoinsurancecompany", "americanrepublicinsurancecompany",
                 "greatwesterninsurancecompany"}


def load_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def match_roster(name: str, entity_key: str | None, roster: list[dict]) -> dict | None:
    """Match a parsed pull to a roster row by normalized lead_entity / rating_unit_name."""
    nn = normalize(name)
    best = None
    for row in roster:
        for key in ("lead_entity", "rating_unit_name"):
            rv = normalize(row.get(key, ""))
            if not rv:
                continue
            # containment either direction handles "... Co" vs "... Company"
            if rv == nn or rv in nn or nn in rv:
                # prefer the longest overlap
                score = len(set(rv) & set(nn)) + (10 if rv == nn else 0)
                if best is None or score > best[0]:
                    best = (score, row)
    return best[1] if best else None


def main() -> int:
    roster = load_csv_rows(ROSTER_CSV)
    assessments = {normalize(r.get("rating_unit_name", "")): r for r in load_csv_rows(ASSESS_CSV)}

    raw_files = sorted(RAW.glob("*.xlsx"))
    if not raw_files:
        print("No raw pulls in data/raw/. Drop the S&P Highlights exports there first.")
        return 1

    records, miss_rows = [], []
    for fp in raw_files:
        pull = parse_highlights(fp)
        roster_row = match_roster(pull.name, pull.entity_key, roster) or {}
        rec = build_record(pull, roster_row)

        # join assessment labels (Y) if confirmed
        rname = normalize(rec["rating_unit_name"])
        a = assessments.get(rname, {})
        for fld in ASSESSMENT_FIELDS:
            rec[fld] = (a.get(fld) or "").strip() or None
        rec["is_wellabe"] = (
            normalize(rec["rating_unit_name"]) in WELLABE_NAMES
            or normalize(rec["lead_entity"]) in WELLABE_NAMES
            or "wellabe" in rname
        )

        # notching reconstruction (only meaningful once block assessments are confirmed)
        if rec.get("bs_assessment"):
            pred = notching.predict(rec["bs_assessment"], rec.get("op_assessment"),
                                    rec.get("bp_assessment"), rec.get("erm_assessment"))
            rng = notching.predict_range(rec["bs_assessment"], rec.get("op_assessment"),
                                         rec.get("bp_assessment"), rec.get("erm_assessment"))
            pred["predicted_strong"] = rng.get("predicted_strong")
            pred["predicted_weak"] = rng.get("predicted_weak")
            pred["in_range"] = notching.in_range(rng, rec.get("icr"))
            rec["notching"] = pred
            rec["icr_residual_notches"] = notching.residual(pred.get("predicted_icr"), rec.get("icr"))
        else:
            rec["notching"] = None
            rec["icr_residual_notches"] = None

        # de-dupe: same rating unit pulled twice (identical files) -> keep first
        if any(x["rating_unit_name"] == rec["rating_unit_name"] for x in records):
            continue
        records.append(rec)
        miss_rows.append({
            "carrier": rec["rating_unit_name"],
            "source_file": rec["source_file"],
            "matched_roster": bool(roster_row),
            "has_assessment": bool(a),
            "missing_fields": "; ".join(rec.get("_missing", [])),
            "unmatched_source_rows": len(pull.unmatched),
        })

    # composites: sample medians by stratum-derived segment (approximation; labeled in tool)
    frame = {
        "meta": {
            "n": len(records),
            "note": "Peer-relative metrics are sample approximations, not AM Best composites.",
            "rbc_basis": "CAL (TAC / Company Action Level RBC = TAC/ACL ratio / 2).",
        },
        "carriers": records,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(frame, indent=2, default=str))

    MISS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with MISS_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(miss_rows[0].keys()))
        w.writeheader()
        w.writerows(miss_rows)

    # ---- console summary ----
    print(f"Built {OUT_JSON.relative_to(ROOT)} from {len(records)} carrier(s).")
    have_rbc = sum(1 for r in records if r.get("rbc_cal_pct") is not None)
    have_y = sum(1 for r in records if r.get("bs_assessment"))
    print(f"  RBC (CAL %) present:        {have_rbc}/{len(records)}")
    print(f"  Assessment labels present:  {have_y}/{len(records)}")
    print(f"  Missingness report:         {MISS_CSV.relative_to(ROOT)}")
    for r in records:
        flag = " [no roster match]" if not any(m["carrier"] == r["rating_unit_name"] and m["matched_roster"] for m in miss_rows) else ""
        print(f"   - {r['rating_unit_name']:<42} RBC(CAL)={r.get('rbc_cal_pct')}%  "
              f"HRL*={r.get('higher_risk_leverage_partial')}%  ROE5y={r.get('roe_5yr_mean')}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
