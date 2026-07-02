"""Emit tool/public_data.json: the curated, non-proprietary subset the site ships with.

Only fields that are publicly derivable from statutory filings (the NAIC "bluebook") or from
public AM Best rating actions are included. Raw S&P/SNL pull rows and any licensed detail are
excluded. BCAR scores (from each carrier's public Best's Credit Report) are joined from
data/bcar_scores.csv, which the analyst fills in as they pull the reports.

Run:  python src/emit_public_data.py
Reads:  tool/data.json (the full derived frame, gitignored) + data/bcar_scores.csv
Writes: tool/public_data.json (committed; the site auto-loads it)
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAME = ROOT / "tool" / "data.json"
BCAR = ROOT / "data" / "bcar_scores.csv"
OUT = ROOT / "tool" / "public_data.json"

# Fields safe to publish: public statutory (bluebook) values + public AM Best assessments.
# Everything here is either filed publicly by the carrier or published by AM Best in a rating action.
WHITELIST = [
    # identity
    "rating_unit_name", "lead_entity", "naic_code", "domicile_state", "is_wellabe", "rating_basis",
    "stratum", "ownership",
    # AM Best assessments (public rating actions)
    "fsr", "icr", "outlook", "under_review", "bs_assessment", "op_assessment", "bp_assessment",
    "erm_assessment", "rating_action_date", "source_url",
    # capital / balance sheet (statutory)
    "rbc_cal_pct", "bcar_score", "capital_surplus_usd", "total_assets_usd",
    "total_invested_assets_usd", "surplus_notes_pct", "reserves_to_surplus",
    # asset risk (statutory schedules)
    "below_ig_pct", "common_stock_pct", "bonds_pct", "bond_avg_quality",
    "higher_risk_leverage_partial", "reinsurance_leverage",
    # operating performance (statutory)
    "roe_5yr_mean", "roe_5yr_std", "roe_trend", "roe_latest", "roe_series",
    "benefit_ratio_latest", "expense_ratio_latest", "commission_ratio_latest",
    "ah_combined_ratio", "ah_cr_trend", "premium_cagr_5yr", "total_premium_usd", "net_income_series",
    # business profile (statutory segment mix)
    "segment_mix_pct", "hhi_segments", "material_segment_count", "risk_type_mix",
    "top_state_pct", "top5_state_pct", "states_licensed", "channel_count", "medsup_market_rank",
    # reconstruction (computed from the public assessments above)
    "notching", "icr_residual_notches",
]


def load_bcar() -> dict:
    """name -> BCAR score (99.6% VaR, %). Creates a template with every carrier if absent."""
    if not BCAR.exists():
        return {}
    out = {}
    with BCAR.open(newline="") as f:
        for row in csv.DictReader(f):
            v = (row.get("bcar_996") or "").strip()
            if v:
                try:
                    out[row["rating_unit_name"].strip()] = float(v)
                except ValueError:
                    pass
    return out


def write_bcar_template(names: list[str], have: dict) -> None:
    """Seed/extend data/bcar_scores.csv so the analyst has a row per carrier to fill in."""
    BCAR.parent.mkdir(parents=True, exist_ok=True)
    with BCAR.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rating_unit_name", "bcar_996", "note"])
        for n in names:
            w.writerow([n, have.get(n, ""), ""])


def main() -> int:
    if not FRAME.exists():
        print("No tool/data.json. Run: python src/build.py first.")
        return 1
    frame = json.loads(FRAME.read_text())
    carriers = frame.get("carriers", [])
    bcar = load_bcar()

    pub = []
    for c in carriers:
        rec = {k: c.get(k) for k in WHITELIST if k in c}
        rec["bcar_score"] = bcar.get(c["rating_unit_name"])  # 99.6% VaR BCAR, or None
        pub.append(rec)

    # keep the BCAR template in sync with the roster so nothing is missed
    write_bcar_template([c["rating_unit_name"] for c in carriers], bcar)

    out = {
        "meta": {
            "n": len(pub),
            "source": "Public statutory (NAIC annual statement / bluebook) values and public AM Best "
                      "rating actions. No licensed S&P/SNL pull rows. BCAR from public Best's Credit Reports.",
            "rbc_basis": "CAL (TAC / Company Action Level RBC).",
        },
        "carriers": pub,
    }
    OUT.write_text(json.dumps(out, indent=2, default=str))
    have = sum(1 for r in pub if r.get("bcar_score") is not None)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(pub)} carriers, {have} with BCAR.")
    print(f"Fill BCAR scores in {BCAR.relative_to(ROOT)} (99.6% VaR, %), then re-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
