# AM Best Rating Decoder — Findings

*Generated from `data/assessments.csv` + `src/notching.py`. Figures BS-2 / OP-1 / BP-1 depend on
the S&P financial pull and export from the tool once `data.json` is populated; the notching
reconstruction (N-1) below is computed from the public assessment labels and is final.*

## N-1 — Notching reconstruction (the tie-it-together exhibit)

Rebuilding each carrier's Issuer Credit Rating from AM Best's **published** baseline-plus-notching
tables — balance-sheet assessment → baseline ICR, then operating / business-profile / ERM notches —
reconciles **45 of 52 carriers (87%) within a single notch** of their
actual ICR, with **20 exact**. The model uses representative midpoint notches within each
published range; the remaining spread is exactly where AM Best's committee judgment and the
comprehensive adjustment enter.

**Residuals worth reading (|actual − predicted| > 1 notch):** these are the carriers the mechanical
model misses, and they are the most instructive cases for the paper —
American-Amicable / Trinity, Cigna — American Retirement Life, Cigna — Loyal American, Cigna — National Health, Combined Insurance (Chubb), Lumico (RGA), USAA Life.

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
