"""Generate the white-paper export pack from the same data the tool uses.

Produces in output/whitepaper/:
  - tables/notching_reconstruction.csv + .md   (the N-1 exhibit — REAL now: needs only the
                                                assessment labels + actual ICR, which we have)
  - tables/assessment_distribution.csv + .md    (how the sample spreads across each block)
  - findings.md                                 (prose findings, each tied to a figure number)

The balance-sheet / operating / business-profile *figures* (BS-2, OP-1, BP-1) depend on the
S&P financial pull; export those from the tool once data.json is populated. This script fills
in what is computable today so the paper's notching section can be drafted immediately.

Run: python src/whitepaper.py
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
import notching  # noqa: E402

ASSESS = ROOT / "data" / "assessments.csv"
OUT = ROOT / "output" / "whitepaper"
TBL = OUT / "tables"


def load_assessments() -> list[dict]:
    with ASSESS.open(newline="") as f:
        return list(csv.DictReader(f))


def notching_table(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if not r.get("bs_assessment") or not r.get("icr"):
            continue
        pred = notching.predict(r["bs_assessment"], r.get("op_assessment"),
                                r.get("bp_assessment"), r.get("erm_assessment"))
        if not pred.get("predicted_icr"):
            continue
        resid = notching.residual(pred["predicted_icr"], r["icr"])
        out.append({
            "rating_unit_name": r["rating_unit_name"],
            "bs": r["bs_assessment"], "op": r.get("op_assessment", ""),
            "bp": r.get("bp_assessment", ""), "erm": r.get("erm_assessment", ""),
            "baseline_icr": pred["baseline_icr"],
            "notch_total": pred["notches"]["total"],
            "predicted_icr": pred["predicted_icr"],
            "actual_icr": r["icr"],
            "residual_notches": resid,
        })
    return out


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def md_table(rows: list[dict], cols: list[str]) -> str:
    head = "| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
    body = "".join("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |\n" for r in rows)
    return head + body


def main():
    rows = load_assessments()
    nt = notching_table(rows)
    TBL.mkdir(parents=True, exist_ok=True)

    # ---- N-1 notching reconstruction ----
    write_csv(TBL / "notching_reconstruction.csv", nt)
    (TBL / "notching_reconstruction.md").write_text(
        md_table(nt, ["rating_unit_name", "bs", "op", "bp", "erm",
                      "baseline_icr", "notch_total", "predicted_icr", "actual_icr", "residual_notches"]))

    within1 = sum(1 for r in nt if r["residual_notches"] is not None and abs(r["residual_notches"]) <= 1)
    exact = sum(1 for r in nt if r["residual_notches"] == 0)
    n = len(nt)
    residuals = [r for r in nt if r["residual_notches"] is not None and abs(r["residual_notches"]) > 1]

    # ---- assessment distribution cross-tabs ----
    dist_rows = []
    for block, key, order in [
        ("Balance sheet", "bs", notching.BASELINE_ICR.keys()),
        ("Operating", "op", notching.OP_NOTCH.keys()),
        ("Business profile", "bp", notching.BP_NOTCH.keys()),
    ]:
        c = Counter(r[key] for r in nt if r[key])
        for tier in order:
            dist_rows.append({"block": block, "assessment": tier, "n_carriers": c.get(tier, 0)})
    write_csv(TBL / "assessment_distribution.csv", dist_rows)
    (TBL / "assessment_distribution.md").write_text(
        md_table(dist_rows, ["block", "assessment", "n_carriers"]))

    # ---- findings.md ----
    findings = f"""# AM Best Rating Decoder — Findings

*Generated from `data/assessments.csv` + `src/notching.py`. Figures BS-2 / OP-1 / BP-1 depend on
the S&P financial pull and export from the tool once `data.json` is populated; the notching
reconstruction (N-1) below is computed from the public assessment labels and is final.*

## N-1 — Notching reconstruction (the tie-it-together exhibit)

Rebuilding each carrier's Issuer Credit Rating from AM Best's **published** baseline-plus-notching
tables — balance-sheet assessment → baseline ICR, then operating / business-profile / ERM notches —
reconciles **{within1} of {n} carriers ({round(100*within1/n)}%) within a single notch** of their
actual ICR, with **{exact} exact**. The model uses representative midpoint notches within each
published range; the remaining spread is exactly where AM Best's committee judgment and the
comprehensive adjustment enter.

**Residuals worth reading (|actual − predicted| > 1 notch):** these are the carriers the mechanical
model misses, and they are the most instructive cases for the paper —
{", ".join(sorted(set(r["rating_unit_name"] for r in residuals))) or "none at this threshold"}.

> *Where Wellabe sits:* a Strongest balance sheet sets an `a` baseline; Adequate operating
> performance and Neutral business profile are no-change notches, so the model lands Wellabe at
> `a` / **A** — matching the actual rating. The interesting tension is operating performance:
> three straight years of new-business-strain losses, yet OP is held at Adequate, not Marginal.

## BS-1 / BS-2 — Balance sheet *(pending S&P financials)*
Thesis to confirm once RBC + asset-risk are loaded: capital alone does not set the tier. *Strongest*
balance sheets are observed across a wide RBC band; what separates carriers at equal RBC is
higher-risk asset leverage. Export BS-2 (RBC vs higher-risk leverage, Wellabe marked) from the tool.

## OP-1 / OP-2 — Operating performance *(pending S&P financials)*
Thesis: operating performance is graded peer-relative, and credited growth-strain carriers are held
at Adequate despite negative ROE. Wellabe and Physicians Mutual are the named cases. Export OP-1
(ROE by assessment, growth-strain flagged) from the tool.

## BP-1 — Business profile *(pending S&P financials)*
Thesis: *Favorable* requires scale **and** a genuine second risk type; *Neutral* is the ceiling for a
single-market specialist. GTL is *Limited* despite a Strongest balance sheet; Mutual of Omaha is
*Favorable* because it broke beyond the senior niche. Export BP-1 (assets vs HHI) from the tool.

## Method notes / guardrails
- Notch magnitudes are representative midpoints within AM Best's published ranges (OP +2/−3,
  BP +2/−2, ERM +1/−4); the reconstruction is explanatory, not a predictor of future actions.
- Every assessment label traces to a `source_url` in `data/assessments.csv`; unconfirmed values are
  blank (Americo and Security National block assessments; Everence is not publicly rated).
- Peer-relative operating metrics will be sample approximations (we do not have AM Best's composites).
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "findings.md").write_text(findings)

    print(f"Wrote white-paper pack to {OUT.relative_to(ROOT)}/")
    print(f"  N-1 notching reconstruction: {n} carriers, {within1} within 1 notch "
          f"({round(100*within1/n)}%), {exact} exact, {len(residuals)} residuals >1 notch")


if __name__ == "__main__":
    main()
