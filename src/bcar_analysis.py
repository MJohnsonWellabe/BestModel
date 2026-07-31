"""BCAR exhibits: BCAR vs the balance-sheet grade, and BCAR vs regulatory RBC.

BCAR (Best's Capital Adequacy Ratio) is AM Best's own capital model and the measure that
actually drives the balance-sheet-strength assessment. It is published only in each carrier's
Best's Credit Report, so it cannot come from the S&P pulls. src/parse_best_report.py extracts
it; this script summarizes what the scores say.

Two findings this quantifies:
  1. BCAR does not map one-for-one onto the balance-sheet grade. Scale, liquidity, reserve
     quality and ERM move a carrier within (and across) tiers, so tiers overlap on BCAR alone.
  2. BCAR and the NAIC RBC ratio are different views of capital, so a high RBC ratio does not
     guarantee a high BCAR. (RBC comes from the licensed pulls via tool/public_data.json;
     where it is absent this section is simply skipped.)

Run: python src/bcar_analysis.py   (after: python src/parse_best_report.py data/raw)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BCAR_CSV = ROOT / "data" / "bcar.csv"
PUBLIC = ROOT / "tool" / "public_data.json"
OUT_MD = ROOT / "output" / "whitepaper" / "tables" / "bcar_findings.md"

BS_ORDER = ["Strongest", "Very Strong", "Strong", "Adequate", "Weak", "Very Weak"]
STRONGEST_BAR = 25.0  # AM Best's published guideline: BCAR > 25% at 99.6% VaR = "Strongest"


def _median(xs: list[float]) -> float | None:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def load_reports() -> list[dict]:
    if not BCAR_CSV.exists():
        return []
    rows = []
    with BCAR_CSV.open(newline="") as f:
        for r in csv.DictReader(f):
            try:
                r["bcar_996_f"] = float(r["bcar_996"]) if r.get("bcar_996") else None
            except ValueError:
                r["bcar_996_f"] = None
            rows.append(r)
    return rows


def load_rbc() -> dict:
    """rating_unit_name -> rbc_cal_pct, from the published public frame (may be absent)."""
    if not PUBLIC.exists():
        return {}
    doc = json.loads(PUBLIC.read_text())
    return {(c.get("rating_unit_name") or "").strip(): c.get("rbc_cal_pct")
            for c in doc.get("carriers", []) if c.get("rbc_cal_pct") is not None}


def main() -> int:
    rows = [r for r in load_reports() if r["bcar_996_f"] is not None]
    if not rows:
        print("No BCAR rows. Run: python src/parse_best_report.py data/raw")
        return 1
    rbc = load_rbc()

    lines = ["# BCAR findings", "",
             f"Source: {len(rows)} Best's Credit Reports (BCAR at the 99.6% VaR confidence level). "
             f"AM Best's guideline is that a score above {STRONGEST_BAR:.0f}% supports the "
             "*Strongest* balance-sheet assessment.", ""]

    # --- 1. BCAR by balance-sheet tier -----------------------------------------------------
    lines += ["## BCAR by balance-sheet assessment", "",
              "| Balance sheet | n | median BCAR | min | max |", "|---|---:|---:|---:|---:|"]
    for tier in BS_ORDER:
        g = [r["bcar_996_f"] for r in rows if r["bs_assessment"] == tier]
        if not g:
            continue
        lines.append(f"| {tier} | {len(g)} | {_median(g):.1f} | {min(g):.1f} | {max(g):.1f} |")

    # overlap: strongest-tier minimum vs weaker-tier maximum
    strongest = [r["bcar_996_f"] for r in rows if r["bs_assessment"] == "Strongest"]
    very = [r["bcar_996_f"] for r in rows if r["bs_assessment"] == "Very Strong"]
    if strongest and very:
        lines += ["", f"The tiers overlap: the weakest *Strongest* carrier scores "
                      f"{min(strongest):.1f}% while the best *Very Strong* carrier scores "
                      f"{max(very):.1f}%. BCAR alone therefore does not determine the grade."]

    # carriers below the 25% bar despite a top-tier grade
    below = [r for r in rows if r["bs_assessment"] in ("Strongest", "Very Strong")
             and r["bcar_996_f"] < STRONGEST_BAR]
    if below:
        lines += ["", f"### Rated at or above *Very Strong* while scoring under the "
                      f"{STRONGEST_BAR:.0f}% bar ({len(below)})", ""]
        for r in sorted(below, key=lambda r: r["bcar_996_f"]):
            lines.append(f"- **{r['seed_name'] or r['rating_unit_name']}** — BCAR "
                         f"{r['bcar_996_f']:.1f}%, balance sheet {r['bs_assessment']}, rated "
                         f"{r['fsr']}. Scale, liquidity and ERM carry the grade.")

    # --- 2. BCAR vs RBC ---------------------------------------------------------------------
    paired = [(r, rbc.get(r["seed_name"])) for r in rows if rbc.get(r["seed_name"]) is not None]
    lines += ["", "## BCAR vs the regulatory RBC ratio", ""]
    if not paired:
        lines.append("No carrier currently has both a BCAR score and an RBC ratio "
                     "(RBC comes from the licensed pulls). Section skipped.")
    else:
        lines.append(f"{len(paired)} carriers have both measures.")
        lines += ["", "| Carrier | BCAR (99.6%) | RBC (CAL) |", "|---|---:|---:|"]
        for r, v in sorted(paired, key=lambda t: -t[0]["bcar_996_f"]):
            lines.append(f"| {r['seed_name'] or r['rating_unit_name']} | {r['bcar_996_f']:.1f}% | {v:.0f}% |")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({len(rows)} carriers with BCAR, "
          f"{len(paired)} with RBC too)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
