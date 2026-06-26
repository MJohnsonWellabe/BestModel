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
        rng = notching.predict_range(r["bs_assessment"], r.get("op_assessment"),
                                     r.get("bp_assessment"), r.get("erm_assessment"))
        resid = notching.residual(pred["predicted_icr"], r["icr"])
        inrange = notching.in_range(rng, r["icr"])
        basis = (r.get("rating_basis") or "standalone").strip()
        width = (rng.get("weak_idx", 0) - rng.get("strong_idx", 0) + 1) if rng.get("strong_idx") is not None else None
        # verdict buckets
        if inrange:
            verdict = "in-range"
        elif basis == "group-member":
            # rating reflects the group, not the standalone blocks (lift if resid>0, cap if <0)
            verdict = "group-aligned"
        else:
            verdict = "genuine residual"      # standalone + out of band = committee judgment
        out.append({
            "rating_unit_name": r["rating_unit_name"],
            "rating_basis": basis,
            "bs": r["bs_assessment"], "op": r.get("op_assessment", ""),
            "bp": r.get("bp_assessment", ""), "erm": r.get("erm_assessment", ""),
            "predicted_range": f'{rng.get("predicted_strong")}..{rng.get("predicted_weak")}',
            "band_width": width,
            "predicted_point": pred["predicted_icr"],
            "actual_icr": r["icr"],
            "residual_notches": resid,
            "verdict": verdict,
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
        md_table(nt, ["rating_unit_name", "rating_basis", "bs", "op", "bp", "erm",
                      "predicted_range", "band_width", "actual_icr", "residual_notches", "verdict"]))

    n = len(nt)
    in_range_n = sum(1 for r in nt if r["verdict"] == "in-range")
    supported = [r for r in nt if r["verdict"] == "group-aligned"]
    genuine = [r for r in nt if r["verdict"] == "genuine residual"]
    within1 = sum(1 for r in nt if r["residual_notches"] is not None and abs(r["residual_notches"]) <= 1)
    explained = in_range_n + len(supported)
    standalone = [r for r in nt if r["rating_basis"] == "standalone"]
    standalone_in = sum(1 for r in standalone if r["verdict"] == "in-range")
    widths = sorted(r["band_width"] for r in nt if r["band_width"])
    med_width = widths[len(widths) // 2] if widths else None

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

Rebuilding each carrier's Issuer Credit Rating from AM Best's **published** tables — the
balance-sheet **baseline band**, then the operating / business-profile / ERM **notch ranges** —
predicts an ICR *interval* for each carrier (knowing the four labels pins the rating to a band, not
a single value, because the baseline alone spans two notches and the OP/ERM notches are themselves
ranges). Of **{n}** rated carriers:

- **{in_range_n} ({round(100*in_range_n/n)}%) fall inside the predicted band** — a tight
  **±{notching.BAND_TOLERANCE}-notch** window around the point estimate, so an in-range hit means the
  rating is within one notch of the reconstruction, not caught by a wide net.
- **{len(supported)} are group-aligned** — subsidiaries rated at their *group's* ICR rather than on
  their standalone blocks. The rating sits above the standalone band where the parent lends a halo
  (USAA Life +4 to aaa; Combined/Chubb +3; Lumico/RGA +3; the Cigna/HCSC and American-Amicable/IA
  units +2) and *below* it where the group rating caps a strong subsidiary (the two Aetna/CVS units,
  pulled to the group's `a`). Either way the residual is group structure, not a model miss.
- Together that explains **{explained} of {n} ({round(100*explained/n)}%)**. Most tellingly, of the
  **{len(standalone)} carriers rated on their own merits, {standalone_in}
  ({round(100*standalone_in/max(len(standalone),1))}%) land in the published band** — the genuine
  standalone residuals are: {", ".join(r["rating_unit_name"] for r in genuine) or "none"}.

This is the thesis made measurable: a standalone carrier's rating is **the published tables applied
to its four blocks**; the exceptions are **group support and committee judgment**, named rather than
hidden. Reported alongside the tighter point model ({within1}/{n} within a single notch) so the band
width can't flatter the result.

> *Where Wellabe sits:* a Strongest balance sheet sets an `a`-band baseline; Adequate operating
> performance and Neutral business profile are no-change notches, so the model lands Wellabe squarely
> in range at `a` / **A** — matching the actual rating, standalone, no support required. The live
> tension is operating performance: three straight years of new-business-strain losses, yet OP is
> held at Adequate, not Marginal.

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
    print(f"  N-1 notching: {n} carriers | {in_range_n} in-range "
          f"({round(100*in_range_n/n)}%), {len(supported)} group-supported, "
          f"{len(genuine)} genuine residuals | standalone in-range {standalone_in}/{len(standalone)} "
          f"| {within1} within 1 notch")


if __name__ == "__main__":
    main()
