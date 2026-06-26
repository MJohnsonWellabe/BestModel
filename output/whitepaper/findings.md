# AM Best Rating Decoder — Findings

*Generated from `data/assessments.csv` + `src/notching.py`. Figures BS-2 / OP-1 / BP-1 depend on
the S&P financial pull and export from the tool once `data.json` is populated; the notching
reconstruction (N-1) below is computed from the public assessment labels and is final.*

## N-1 — Notching reconstruction (the tie-it-together exhibit)

Rebuilding each carrier's Issuer Credit Rating from AM Best's **published** tables — the
balance-sheet **baseline band**, then the operating / business-profile / ERM **notch ranges** —
predicts an ICR *interval* for each carrier (knowing the four labels pins the rating to a band, not
a single value, because the baseline alone spans two notches and the OP/ERM notches are themselves
ranges). Of **52** rated carriers:

- **43 (83%) fall inside the predicted interval** — the model
  reproduces them from the four labels alone (median band width 3 notches; the band is the
  honest object here — knowing the labels brackets the rating, it doesn't pin it to one value).
- **9 are group-aligned** — subsidiaries rated at their *group's* ICR rather than on
  their standalone blocks. The rating sits above the standalone band where the parent lends a halo
  (USAA Life +4 to aaa; Combined/Chubb +3; Lumico/RGA +3; the Cigna/HCSC and American-Amicable/IA
  units +2) and *below* it where the group rating caps a strong subsidiary (the two Aetna/CVS units,
  pulled to the group's `a`). Either way the residual is group structure, not a model miss.
- Together that explains **52 of 52 (100%)**. Most tellingly, of the
  **30 carriers rated on their own merits, 30
  (100%) land in the published band** — the genuine
  standalone residuals are: none.

This is the thesis made measurable: a standalone carrier's rating is **the published tables applied
to its four blocks**; the exceptions are **group support and committee judgment**, named rather than
hidden. Reported alongside the tighter point model (45/52 within a single notch) so the band
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
