"""Turn a parsed RawPull into the normalized analysis record used by the tool.

Implements the derived metrics from PLAN.md §4 that are computable from the Highlights
export. Where a metric needs data the export doesn't carry (Schedule BA, real estate,
geography, granular line-of-business premium), the field is emitted as None and flagged in
`_missing` so the build's missingness report can surface it — never invented.

Key conversions (validated against known values in the plan):
  - rbc_cal_pct = rbc_acl_ratio / 2     (export ratio is TAC/ACL; CAL = 2 x ACL)
  - ah_combined_ratio = benefit_ratio + expense_ratio + commission_ratio   (latest year)
"""
from __future__ import annotations

from statistics import mean, pstdev

from parse_sp_pull import RawPull

# Fields the Highlights export cannot supply; populated only when a supplemental pull or
# research fill is merged in. Listed so the report distinguishes "absent because not pulled"
# from "absent because the carrier file was malformed".
SUPPLEMENTAL_FIELDS = [
    "schedule_ba_pct", "real_estate_pct", "mortgage_pct", "net_unrealized_pct_cap",
    "hhi_lines", "material_line_count", "states_licensed", "top_state_pct",
    "top5_state_pct", "channel_count", "medsup_market_rank",
]


def _latest(series: dict[int, float] | None):
    if not series:
        return None
    return series[max(series)]


def _series_list(series: dict[int, float] | None) -> list[float]:
    if not series:
        return []
    return [series[y] for y in sorted(series)]


def _ols_slope(values: list[float]) -> float | None:
    """Simple OLS slope of values vs. their index (trend direction)."""
    n = len(values)
    if n < 2:
        return None
    xs = list(range(n))
    xbar, ybar = mean(xs), mean(values)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, values)) / denom


def _cagr(series: dict[int, float] | None) -> float | None:
    if not series or len(series) < 2:
        return None
    yrs = sorted(series)
    first, last = series[yrs[0]], series[yrs[-1]]
    if first is None or first <= 0 or last is None or last <= 0:
        return None
    span = yrs[-1] - yrs[0]
    return (last / first) ** (1 / span) - 1 if span else None


def build_record(pull: RawPull, roster: dict | None = None) -> dict:
    s = pull.series
    rec: dict = {}
    missing: list[str] = []

    # ---- identity (roster overrides/augments the parsed name) ----
    roster = roster or {}
    rec["rating_unit_name"] = roster.get("rating_unit_name") or pull.name
    rec["lead_entity"] = roster.get("lead_entity") or pull.name
    rec["entity_key"] = pull.entity_key
    rec["stratum"] = roster.get("stratum", "")
    rec["ownership"] = roster.get("ownership", "")
    rec["source_file"] = pull.source_file
    rec["years"] = pull.years

    # ---- balance sheet ----
    rbc_ratio = _latest(s.get("rbc_acl_ratio"))
    rec["rbc_cal_pct"] = round(rbc_ratio / 2, 1) if rbc_ratio is not None else None
    rec["tac_usd"] = _latest(s.get("tac_usd"))
    rec["acl_rbc_usd"] = _latest(s.get("acl_rbc_usd"))
    cs = _latest(s.get("capital_surplus_usd"))
    rec["capital_surplus_usd"] = cs
    inv = _latest(s.get("total_invested_assets_usd"))
    rec["total_invested_assets_usd"] = inv
    sn = _latest(s.get("surplus_notes_usd"))
    rec["surplus_notes_usd"] = sn
    rec["surplus_notes_pct"] = (
        round(100 * sn / (cs + sn), 2) if (sn and cs and (cs + sn)) else (0.0 if sn == 0 else None)
    )
    rec["avr_usd"] = _latest(s.get("avr_usd"))
    tot_res = _latest(s.get("total_reserves_usd"))
    rec["total_reserves_usd"] = tot_res
    rec["reserves_to_surplus"] = round(tot_res / cs, 2) if (tot_res and cs) else None

    rec["below_ig_pct"] = _latest(s.get("below_ig_pct"))
    rec["common_stock_pct"] = _latest(s.get("common_stock_pct"))
    rec["bonds_pct"] = _latest(s.get("bonds_pct"))
    rec["affiliated_pct"] = _latest(s.get("affiliated_pct"))
    rec["bond_avg_quality"] = _latest(s.get("bond_avg_quality"))

    # higher-risk leverage — PARTIAL: (below-IG bonds + unaffiliated common stock) / C&S.
    # Full version adds Schedule BA + real estate once the supplemental pull is merged.
    hrl_partial = None
    if cs and inv:
        below_ig_usd = 0.0
        if rec["below_ig_pct"] is not None and rec["bonds_pct"] is not None:
            below_ig_usd = (rec["below_ig_pct"] / 100) * (rec["bonds_pct"] / 100) * inv
        common_usd = (rec["common_stock_pct"] / 100) * inv if rec["common_stock_pct"] is not None else 0.0
        hrl_partial = round(100 * (below_ig_usd + common_usd) / cs, 1)
    rec["higher_risk_leverage_partial"] = hrl_partial
    rec["higher_risk_leverage_complete"] = False  # becomes True when Sched BA / RE merged

    # reinsurance leverage proxy: ceded reserve credits / C&S
    rc = (_latest(s.get("reins_credit_life_ga")) or 0) + (_latest(s.get("reins_credit_ah")) or 0)
    rec["reinsurance_leverage"] = round(100 * rc / cs, 1) if (rc and cs) else None

    # ---- operating performance ----
    roe = _series_list(s.get("roe"))
    rec["roe_series"] = {y: s["roe"][y] for y in sorted(s.get("roe", {}))} if "roe" in s else {}
    rec["roe_5yr_mean"] = round(mean(roe), 2) if roe else None
    rec["roe_5yr_std"] = round(pstdev(roe), 2) if len(roe) > 1 else None
    rec["roe_trend"] = round(_ols_slope(roe), 3) if _ols_slope(roe) is not None else None
    rec["roe_latest"] = _latest(s.get("roe"))

    br, er, cr = _latest(s.get("benefit_ratio")), _latest(s.get("expense_ratio")), _latest(s.get("commission_ratio"))
    rec["benefit_ratio_latest"] = br
    rec["expense_ratio_latest"] = er
    rec["commission_ratio_latest"] = cr
    if any(x is not None for x in (br, er, cr)):
        rec["ah_combined_ratio"] = round(sum(x for x in (br, er, cr) if x is not None), 1)
    else:  # health/P&C template gives a direct combined ratio instead of the three components
        rec["ah_combined_ratio"] = _latest(s.get("combined_ratio_direct"))
    cr_series = _series_list(s.get("benefit_ratio"))
    rec["ah_cr_trend"] = round(_ols_slope(cr_series), 3) if _ols_slope(cr_series) is not None else None

    rec["net_income_series"] = {y: s["net_income"][y] for y in sorted(s.get("net_income", {}))} if "net_income" in s else {}
    rec["premium_cagr_5yr"] = round(_cagr(s.get("total_premium")) or 0, 4) if s.get("total_premium") else None
    rec["total_premium_usd"] = _latest(s.get("total_premium"))
    nii = _latest(s.get("net_investment_income"))
    rg = _latest(s.get("realized_gains"))
    pti = _latest(s.get("pretax_op_income"))
    rec["oneoff_reliance"] = round(rg / pti, 3) if (rg is not None and pti) else None

    # ---- business profile (coarse, from segment mix — granular LOB needs supplemental) ----
    seg = {
        "ah": _latest(s.get("seg_ah")),
        "ind_life": _latest(s.get("seg_individual_life")),
        "grp_life": _latest(s.get("seg_group_life")),
        "ind_annuity": _latest(s.get("seg_individual_annuity")),
        "grp_annuity": _latest(s.get("seg_group_annuity")),
    }
    rec["segment_mix_pct"] = {k: v for k, v in seg.items() if v is not None}
    vals = [v for v in seg.values() if v is not None and v > 0]
    rec["hhi_segments"] = round(sum((v / 100) ** 2 for v in vals), 3) if vals else None
    rec["material_segment_count"] = sum(1 for v in vals if v >= 10)
    # risk-type mix: A&H -> morbidity, life -> mortality, annuity -> market/spread
    rec["risk_type_mix"] = {
        "morbidity": seg["ah"],
        "mortality": round((seg["ind_life"] or 0) + (seg["grp_life"] or 0), 2),
        "market_spread": round((seg["ind_annuity"] or 0) + (seg["grp_annuity"] or 0), 2),
    }

    rec["total_assets_usd"] = _latest(s.get("total_assets_usd"))

    # ---- flag what's genuinely absent ----
    for fld in SUPPLEMENTAL_FIELDS:
        rec.setdefault(fld, None)
        if rec.get(fld) is None:
            missing.append(fld)
    for core in ("rbc_cal_pct", "capital_surplus_usd", "roe_5yr_mean", "total_assets_usd"):
        if rec.get(core) is None:
            missing.append(core)
    rec["_missing"] = sorted(set(missing))
    return rec
