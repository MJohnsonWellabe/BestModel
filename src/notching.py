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

# Block assessment -> notches. No-change state is 0. Magnitudes are representative midpoints
# within each published range (OP +2/-3, BP +2/-2, ERM +1/-4).
OP_NOTCH = {"Strong": +1, "Adequate": 0, "Marginal": -2, "Weak": -3}
BP_NOTCH = {"Favorable": +1, "Neutral": 0, "Limited": -1, "Very Limited": -2}
ERM_NOTCH = {"Very Strong": +1, "Appropriate": 0, "Marginal": -2, "Weak": -4}

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


def _selftest():
    # Field guide worked example: Strongest + Adequate + Neutral + Appropriate -> a -> A
    r = predict("Strongest", "Adequate", "Neutral", "Appropriate")
    assert r["predicted_icr"] == "a", r
    assert r["predicted_fsr"] == "A", r
    # A downgrade pressure example: Strong BS, Marginal OP -> below baseline
    r2 = predict("Strong", "Marginal", "Neutral", "Appropriate")
    assert r2["baseline_icr"] == "bbb+" and r2["notches"]["total"] == -2, r2
    print("notching self-test passed:", r["baseline_icr"], "->", r["predicted_icr"], "->", r["predicted_fsr"])


if __name__ == "__main__":
    _selftest()
