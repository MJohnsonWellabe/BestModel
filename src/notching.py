"""AM Best baseline + notching reconstruction (PLAN.md §6.4).

Encodes the published tables from the ELT Field Guide:
  - balance-sheet assessment -> baseline ICR        (Table: "Combined balance-sheet ...")
  - building-block notch ranges                      (Table: OP +2/-3, BP +2/-2, ERM +1/-4)
  - ICR -> FSR letter                                (Table: "ICR / FSR")

Given a carrier's four assessments it predicts the ICR/FSR; comparing to the actual rating
exposes where committee judgment / the comprehensive adjustment moved the result. The notch
*magnitudes* within each range are representative midpoints (AM Best does not publish the
exact value it applies), so predictions are expected to reconcile within ~a notch — the
residuals are the finding, not an error.
"""
from __future__ import annotations

# Ordinal ICR scale (lower number = stronger).
ICR_SCALE = [
    "aaa", "aa+", "aa", "aa-", "a+", "a", "a-",
    "bbb+", "bbb", "bbb-", "bb+", "bb", "bb-",
    "b+", "b", "b-", "ccc+", "ccc", "ccc-", "cc", "c",
]
ICR_INDEX = {v: i for i, v in enumerate(ICR_SCALE)}

# Balance-sheet assessment -> baseline ICR. The guide's worked example (Strongest + all
# no-change -> a -> A) fixes Strongest at the lower end of its a+/a range, so we take the
# lower/conservative bound of each published range as the baseline.
BASELINE_ICR = {
    "Strongest": "a",      # range a+ / a
    "Very Strong": "a-",   # range a  / a-
    "Strong": "a-",        # range a- / bbb+ — empirical median (standalone) is a-, not the low end
    "Adequate": "bbb",     # range bbb+ / bbb / bbb-
    "Weak": "bb",          # range bb+ / bb / bb-
    "Very Weak": "b-",     # below the table
}

# Block assessment -> notches. No-change state is 0. AM Best's full BCRM tier sets are used
# (the ELT field guide compressed them); the published ranges fit the fuller tiers exactly:
#   Operating performance  +2 .. -3   (Very Strong / Strong / Adequate / Marginal / Weak / Very Weak)
#   Business profile        +2 .. -2   (Very Favorable / Favorable / Neutral / Limited / Very Limited)
#   ERM                     +1 .. -4   (Very Strong / Appropriate / Marginal / Weak / Very Weak)
# Magnitudes within a range are representative midpoints (AM Best applies committee judgment).
OP_NOTCH = {"Very Strong": +2, "Strong": +1, "Adequate": 0, "Marginal": -1, "Weak": -2, "Very Weak": -3}
BP_NOTCH = {"Very Favorable": +2, "Favorable": +1, "Neutral": 0, "Limited": -1, "Very Limited": -2}
ERM_NOTCH = {"Very Strong": +1, "Appropriate": 0, "Marginal": -1, "Weak": -3, "Very Weak": -4}

# ---- Range model -------------------------------------------------------------------------
# The reconstruction is a point estimate (baseline + notches) plus a TIGHT +/-1 notch tolerance
# for committee judgment within the published ranges. A carrier "hits" when its actual ICR lands
# inside that one-notch band. Kept deliberately tight (not a wide baseline band) so an in-range
# result is a real prediction, not a net that catches everything.
BAND_TOLERANCE = 1  # notches above/below the point estimate

# ICR -> FSR letter (published map; extended below the guide's table for completeness).
ICR_TO_FSR = {
    "aaa": "A++", "aa+": "A++", "aa": "A+", "aa-": "A+",
    "a+": "A", "a": "A", "a-": "A-",
    "bbb+": "B++", "bbb": "B++", "bbb-": "B+",
    "bb+": "B", "bb": "B", "bb-": "B-",
    "b+": "C++", "b": "C+", "b-": "C+",
    "ccc+": "C", "ccc": "C", "ccc-": "C", "cc": "C-", "c": "D",
}


def _clamp(i: int) -> int:
    return max(0, min(len(ICR_SCALE) - 1, i))


def predict(bs: str, op: str, bp: str, erm: str) -> dict:
    """Return predicted ICR + FSR and the notch breakdown. Unknown labels -> 0 notch."""
    base = BASELINE_ICR.get((bs or "").strip())
    if base is None:
        return {"baseline_icr": None, "predicted_icr": None, "predicted_fsr": None,
                "notches": None, "note": f"unknown balance-sheet assessment: {bs!r}"}
    n_op = OP_NOTCH.get((op or "").strip(), 0)
    n_bp = BP_NOTCH.get((bp or "").strip(), 0)
    n_erm = ERM_NOTCH.get((erm or "").strip(), 0)
    total = n_op + n_bp + n_erm
    # notches that *subtract* move down the scale (higher index); add moves up (lower index).
    pred_idx = _clamp(ICR_INDEX[base] - total)
    pred_icr = ICR_SCALE[pred_idx]
    return {
        "baseline_icr": base,
        "notches": {"operating": n_op, "business_profile": n_bp, "erm": n_erm, "total": total},
        "predicted_icr": pred_icr,
        "predicted_fsr": ICR_TO_FSR.get(pred_icr),
    }


def residual(predicted_icr: str | None, actual_icr: str | None) -> int | None:
    """Signed notch difference actual - predicted (positive = actual stronger than model)."""
    if not predicted_icr or not actual_icr:
        return None
    a = ICR_INDEX.get(actual_icr.strip().lower())
    p = ICR_INDEX.get(predicted_icr.strip().lower())
    if a is None or p is None:
        return None
    return p - a  # smaller index = stronger; positive means actual is stronger


def predict_range(bs: str, op: str, bp: str, erm: str) -> dict:
    """Return a tight predicted ICR interval = point estimate +/- BAND_TOLERANCE notches.

    A standalone carrier's actual rating should fall inside this one-notch band; where the actual
    sits outside it, the difference is group/parent support or a committee adjustment, not the
    four blocks. `predicted_point` is the center; `strong_idx`/`weak_idx` bound the band.
    """
    p = predict(bs, op, bp, erm)
    if not p.get("predicted_icr"):
        return {"predicted_strong": None, "predicted_weak": None, "predicted_point": None,
                "note": p.get("note")}
    idx = ICR_INDEX[p["predicted_icr"]]
    strong_idx = _clamp(idx - BAND_TOLERANCE)   # stronger end (lower index)
    weak_idx = _clamp(idx + BAND_TOLERANCE)     # weaker end (higher index)
    return {"predicted_point": p["predicted_icr"],
            "predicted_strong": ICR_SCALE[strong_idx], "predicted_weak": ICR_SCALE[weak_idx],
            "strong_idx": strong_idx, "weak_idx": weak_idx}


def in_range(rng: dict, actual_icr: str | None) -> bool | None:
    """True if the actual ICR falls within the predicted interval from predict_range()."""
    if not actual_icr or rng.get("strong_idx") is None:
        return None
    a = ICR_INDEX.get(actual_icr.strip().lower())
    if a is None:
        return None
    return rng["strong_idx"] <= a <= rng["weak_idx"]


def _selftest():
    # Field guide worked example: Strongest + Adequate + Neutral + Appropriate -> a -> A
    r = predict("Strongest", "Adequate", "Neutral", "Appropriate")
    assert r["predicted_icr"] == "a", r
    assert r["predicted_fsr"] == "A", r
    # Strong BS, all no-change -> a- -> A- (matches e.g. Atlantic American at 212% RBC)
    assert predict("Strong", "Adequate", "Neutral", "Appropriate")["predicted_fsr"] == "A-"
    r2 = predict("Strong", "Marginal", "Neutral", "Appropriate")
    assert r2["baseline_icr"] == "a-" and r2["notches"]["total"] == -1, r2
    # Range model: Physicians Mutual (Strongest/Strong/Neutral/Appropriate) actual aa- should be
    # in-range once we allow the high-Strongest baseline + Strong=+2 ceiling.
    # Range model is point +/-1 notch. Physicians Mutual point = a+, band aa- .. a.
    rg = predict_range("Strongest", "Strong", "Neutral", "Appropriate")
    assert rg["predicted_point"] == "a+", rg
    assert in_range(rg, "aa-") is True, rg        # actual rating, top of the +/-1 band
    assert in_range(rg, "a") is True, rg          # bottom of the band
    assert in_range(rg, "aa") is False, rg        # two notches up -> outside (real lift needed)
    assert in_range(rg, "a-") is False, rg        # two notches down -> outside
    print("notching self-test passed:", r["predicted_icr"], "| PhysMut band:",
          rg["predicted_strong"], "..", rg["predicted_weak"])


if __name__ == "__main__":
    _selftest()
