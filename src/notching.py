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
    "Strong": "bbb+",      # range a- / bbb+
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
# The point model above collapses each published band to one value, which makes the rating
# look "wrong" whenever AM Best sits at the high end of a band. The honest model is an
# interval: the baseline is a 2-notch band, and OP/ERM notches are themselves ranges. A
# prediction "hits" when the actual ICR falls inside the interval. (BP maps cleanly to a
# single integer, so its range is a point.)
BASELINE_BAND = {   # (stronger end, weaker end) of the published baseline ICR band
    "Strongest": ("a+", "a"), "Very Strong": ("a", "a-"), "Strong": ("a-", "bbb+"),
    "Adequate": ("bbb+", "bbb-"), "Weak": ("bb+", "bb-"), "Very Weak": ("b+", "b-"),
}
OP_BAND =  {"Very Strong": (1, 2), "Strong": (1, 2), "Adequate": (0, 0),
            "Marginal": (-2, -1), "Weak": (-3, -2), "Very Weak": (-3, -3)}
BP_BAND =  {"Very Favorable": (2, 2), "Favorable": (1, 1), "Neutral": (0, 0),
            "Limited": (-1, -1), "Very Limited": (-2, -2)}
ERM_BAND = {"Very Strong": (1, 1), "Appropriate": (0, 0), "Marginal": (-2, -1),
            "Weak": (-4, -3), "Very Weak": (-4, -4)}

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
    """Return the predicted ICR **interval** from the published baseline + notch bands.

    A carrier's standalone rating should fall inside this interval; where the actual ICR sits
    above it, the lift is coming from outside the four blocks (group/parent support or the
    comprehensive adjustment), not from the model being wrong.
    """
    band = BASELINE_BAND.get((bs or "").strip())
    if band is None:
        return {"predicted_strong": None, "predicted_weak": None, "note": f"unknown bs: {bs!r}"}
    hi_idx, lo_idx = ICR_INDEX[band[0]], ICR_INDEX[band[1]]  # hi=stronger(lower idx)
    op_b = OP_BAND.get((op or "").strip(), (0, 0))
    bp_b = BP_BAND.get((bp or "").strip(), (0, 0))
    erm_b = ERM_BAND.get((erm or "").strip(), (0, 0))
    max_up = op_b[1] + bp_b[1] + erm_b[1]   # most positive notches
    min_up = op_b[0] + bp_b[0] + erm_b[0]   # most negative notches
    strong_idx = _clamp(hi_idx - max_up)    # strongest plausible ICR (lowest index)
    weak_idx = _clamp(lo_idx - min_up)      # weakest plausible ICR (highest index)
    lo, hi = min(strong_idx, weak_idx), max(strong_idx, weak_idx)
    return {"predicted_strong": ICR_SCALE[lo], "predicted_weak": ICR_SCALE[hi],
            "strong_idx": lo, "weak_idx": hi}


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
    # A downgrade pressure example: Strong BS, Marginal OP -> below baseline
    r2 = predict("Strong", "Marginal", "Neutral", "Appropriate")
    assert r2["baseline_icr"] == "bbb+" and r2["notches"]["total"] == -1, r2
    # Range model: Physicians Mutual (Strongest/Strong/Neutral/Appropriate) actual aa- should be
    # in-range once we allow the high-Strongest baseline + Strong=+2 ceiling.
    rg = predict_range("Strongest", "Strong", "Neutral", "Appropriate")  # -> aa .. a+
    assert in_range(rg, "aa-") is True, rg        # actual rating, inside the interval
    assert in_range(rg, "a") is False, rg         # one below the band (would need a drag)
    assert in_range(rg, "aa+") is False, rg       # above the achievable ceiling
    print("notching self-test passed:", r["predicted_icr"], "| range PhysMut:",
          rg["predicted_strong"], "..", rg["predicted_weak"])


if __name__ == "__main__":
    _selftest()
