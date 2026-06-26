# S&P / SNL Pull Spec — exactly what to export per carrier

This is the precise data-pull list. **Good news from the sample pulls:** the single
**"Life/Fraternal Financial Highlights"** export you already generate (like the GTL / Mutual of
Omaha / American Republic samples) is the *backbone* and the pipeline auto-extracts ~36 metrics
from it — including RBC, capital, asset quality, and the full 5-year operating series. Your manual
work is therefore small: drop that one export per carrier, plus a short supplemental list below for
the handful of fields it doesn't carry.

> **Workflow:** export the Highlights workbook per carrier → save into `data/raw/` (any filename) →
> run `python src/build.py`. The build's missingness report (`data/processed/missingness.csv`) tells
> you exactly which supplemental fields are still blank for each carrier, so you can pull only what's
> actually missing rather than everything.

---

## A. The backbone — "Life/Fraternal Financial Highlights" export (auto-parsed)

Pull this for **every** carrier (S&P Capital IQ Pro → company → Financial Highlights → Life/Fraternal,
"Last Four Years & YTD", $000). The parser reads these rows automatically — **you do not map them**:

| Model field | Source row in the export | Notes |
|---|---|---|
| `tac_usd` | RBC - Total Adjusted Capital | |
| `acl_rbc_usd` | ACL Risk Based Capital | |
| `rbc_cal_pct` *(derived)* | Risk Based Capital Ratio(TAC/ACL RBC) | **export ratio is TAC/ACL; pipeline divides by 2** to put it on the CAL basis Wellabe reports |
| `capital_surplus_usd` | Capital and Surplus | |
| `surplus_notes_usd` | Surplus Notes | |
| `avr_usd` | Asset Valuation Reserve | |
| `total_invested_assets_usd` | Total Cash and Investments | |
| `total_assets_usd` | Total Assets | |
| `total_reserves_usd` | Total Policy Reserves | |
| `below_ig_pct` | Bonds Rated 3-6 / Total Bonds | NAIC 3–6 share |
| `common_stock_pct` | Unaff. Common Stocks / Unaff. Investments | |
| `bonds_pct` | Unaff. Bonds / Unaff. Investments | |
| `affiliated_pct` | Affiliated Investments / Total Investments | |
| `bond_avg_quality` | Bond Average Asset Quality (1-6) (#) | |
| `roe_2022..2025` | Return on Average Equity | 5-yr series (export gives 4 yrs + YTD) |
| `roa_2022..2025` | Return on Average Assets | |
| `benefit_ratio` | Benefit Ratio (Premiums) | |
| `expense_ratio` | Expense Ratio (Premiums) | |
| `commission_ratio` | Commission Ratio | feeds A&H combined |
| `ah_combined_ratio` *(derived)* | = Benefit + Expense + Commission ratio | A&H combined approximation |
| `net_income_*` | Net Income | series |
| `pretax_op_income_*` | Pre-tax Operating Income | series |
| `net_investment_income` | Net Investment Income | |
| `realized_gains` | Net Realized Capital Gains (Losses) | one-off reliance |
| `total_premium_usd` | Premiums, Consideration & Deposits | |
| `premium_cagr_5yr` *(derived)* | from the premium series | growth-strain input |
| segment mix % | Individual Life / Group Life / Individual & Group Annuities / Accident & Health | coarse risk-type mix |
| `reinsurance_leverage` *(derived)* | Reinsurance Ceded - Reserve Credits Taken (Life GA + A&H) ÷ C&S | proxy |

**Watch-outs (the "format varies" cases):** P&C-sibling or pure-health entities (e.g. American
Southern, some Humana/UHC entities) may export on a different highlights template with different row
labels. The parser flags any unrecognized rows; if a backbone field comes up blank for such a carrier,
send me the odd row label and I'll add it to the alias map in `src/parse_sp_pull.py`.

---

## B. Supplemental pulls — only for fields the Highlights export omits

Pull these **once per carrier** where you want the full-fidelity analysis. Each is optional; the tool
degrades gracefully and labels partial metrics.

### B1. Asset-mix detail → completes `higher_risk_leverage` (the headline chart's Y-axis)
The Highlights export gives below-IG bonds and common stock but **not** Schedule BA, real estate, or
mortgages. Pull from the **SNL Statutory Investment / Asset Allocation** screen (or Schedule summary):
| Model field | What to pull |
|---|---|
| `schedule_ba_pct` | Schedule BA (alternatives/LP/PE) ÷ total invested assets |
| `real_estate_pct` | Real estate ÷ invested assets |
| `mortgage_pct` | Mortgage loans ÷ invested assets (note CML subset if available) |
| `net_unrealized_usd` | Net unrealized gain/(loss) on bonds (rate drag) |

> With these, the pipeline upgrades `higher_risk_leverage_partial` → the full
> `(Sched BA + unaff common stock + real estate + below-IG bonds) ÷ C&S` metric.

### B2. Line-of-business premium $ → business-profile diversification (HHI)
The Highlights export gives only Life/Annuity/A&H segment %. For the concentration analysis pull
**direct or net premium by line** (SNL Product/Line-of-Business screen), in $000:
`prem_medsup, prem_hosp_indemnity, prem_other_ah, prem_ltc, prem_stc, prem_life_term,
prem_life_whole, prem_life_ul_iul, prem_annuity, prem_preneed_final_expense, prem_group,
prem_disability, prem_dental_vision, prem_credit, prem_other`.
→ pipeline derives `hhi_lines`, `material_line_count`, refined `risk_type_mix`.

### B3. Geography & distribution → business-profile reach
Not in S&P financials. Pull what S&P/SNL surfaces; I will research the rest:
`states_licensed, top_state_pct, top5_state_pct, medsup_market_rank` (SNL market-share screen),
`distribution_channels, dtc_brand_flag` (I can fill these from public sources).

---

## C. Assessment labels (the targets, Y) — **I research these, not you**

FSR, ICR, the three block assessments, ERM, outlook, action date, and source URL come from the AM Best
rating-action press releases, not S&P. I populate `data/assessments.csv` with a `source_url` per row
(guardrail: every label traces to a source; unconfirmed = blank). You only need to confirm/override any
you have better knowledge of.

---

## Field reference
Full definitions and source hints for all 83 fields: `data/variable_dictionary.csv`
(and the **Data Dictionary** sheet in `templates/sp_pull_template.xlsx`).
