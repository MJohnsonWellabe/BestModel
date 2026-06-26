# AM Best Rating Decoder — Project Plan

**Owner:** Office of the Chief Actuary, Wellabe
**Purpose:** Reverse-engineer how AM Best translates financial reality into its four
building-block assessments and the final FSR, using public assessment labels as the
target and S&P Capital IQ / SNL statutory data as the inputs. Output feeds the AM Best
white paper.
**Scope note:** We model three of the four blocks — **balance sheet strength, operating
performance, business profile.** ERM is captured but **not** modeled (it is judgment-
and event-driven, with almost no public input signal).

---

## 0. The core idea (read first)

This is a supervised-learning problem with an unusually clean target. AM Best's four
**assessment labels are public** — every rating action press release states them:

- **Balance sheet:** Strongest / Very Strong / Strong / Adequate / Weak / Very Weak
- **Operating performance:** Strong / Adequate / Marginal / Weak
- **Business profile:** Favorable / Neutral / Limited / Very Limited
- **ERM:** Very Strong / Appropriate / Marginal / Weak *(capture, do not model)*

The **inputs** (RBC, capital quality, asset mix, 5-year earnings, lines of business,
scale, geography) are pullable from S&P. So we have known X and known Y and can
recover the function.

**One hard limit, stated up front so we don't chase it:** the **BCAR score itself is
NOT public** — it lives in the paid Best's Credit Reports. We therefore do **not** try
to map RBC → BCAR across the field. We map RBC + asset risk + capital quality → the
**balance-sheet-strength assessment** (the observable thing one level down from BCAR).
That is sufficient, because the balance-sheet assessment is what actually feeds the
rating. *(We do not have full Best's Credit Report access, so BCAR scores are out of
reach entirely — the whole project runs off the public assessment labels plus S&P
financials. That is by design, not a compromise: the assessment labels are exactly what
the rating is built from.)*

**Posture on the whole exercise:** the goal is **documented decision rules with stated
exceptions**, not a black-box classifier. AM Best forward-looks and applies committee
judgment; a deterministic model would be dishonest. We want statements like "Strongest
is observed down to ~X% RBC *provided* higher-risk leverage stays under ~Y%," with the
counter-examples named.

---

## 1. Deliverables (what Claude Code should produce)

**The interactive mobile tool is the primary deliverable.** Everything else exists to
feed it or to extract static exhibits from it for the paper.

1. **Single-file HTML explorer** (`/tool/index.html`) — the main surface. Mobile-first,
   GitHub-Pages-hostable, no build step (the format Wellabe uses for all browser tools).
   Loads the processed data, computes the core analytics **client-side in JS** (so it is
   fully self-contained on a phone), and renders every figure in §6 interactively with a
   "Where Wellabe sits" overlay on each. See §6.5 for the tool spec.
2. **Data-prep pipeline** (`/src`) that reads the filled S&P template, cleans it,
   engineers the derived metrics in §4, builds the peer composites, and emits a single
   **`data.json`** (the analysis frame) that the tool loads. The tool can also ingest the
   raw filled template directly and derive in-browser, so it works even before the
   pipeline is wired up.
3. **`/templates/sp_pull_template.xlsx`** — the data-entry workbook the analyst fills from
   S&P. (A starter version is provided; extend it from the dictionary in §4 / roster in §5.)
4. **Static export pack for the white paper** (`/output/whitepaper/`) — the tool (or the
   pipeline) exports each figure as PNG **and** SVG, each table as CSV **and** a Markdown
   snippet, plus a prose `findings.md`. This is generated *from the same computed frame*
   the tool uses, so the paper and the tool never disagree.

---

## 2. Repository structure

```
ambest-decoder/
├── PLAN.md                      # this file
├── README.md                    # quickstart + data-pull instructions for the analyst
├── data/
│   ├── raw/                     # S&P exports land here (gitignored)
│   ├── carriers_seed.csv        # the roster from §5 (rating units + stratification tags)
│   ├── variable_dictionary.csv  # the dictionary from §4 (field, defn, source, transform)
│   └── processed/               # cleaned, feature-engineered analysis frame
├── templates/
│   └── sp_pull_template.xlsx    # analyst-facing data-entry workbook
├── src/
│   ├── ingest.py                # read template/raw → tidy frame; validate against dictionary
│   ├── clean.py                 # units, nulls, dedupe to rating-unit level, date alignment
│   ├── features.py              # all derived metrics (HHI, ROE stats, leverage, flags)
│   ├── composite.py             # build L/H peer-composite benchmarks (see §4 note)
│   ├── analyze_balance_sheet.py
│   ├── analyze_operating.py
│   ├── analyze_business_profile.py
│   ├── notching.py              # baseline + block notches → predicted ICR, residuals
│   ├── emit_json.py             # write data.json (analysis frame) for the tool
│   └── charts.py                # OPTIONAL static figure export for the white paper
├── tool/
│   ├── index.html               # PRIMARY: interactive mobile explorer (loads data.json)
│   └── data.json                # emitted by the pipeline; tool can also ingest raw CSV
└── output/
    ├── figures/                 # PNG + SVG
    ├── tables/                  # CSV
    └── whitepaper/              # md snippets + findings.md
```

**Stack:** Python (pandas, numpy, scipy) for the data-prep pipeline that emits
`data.json`. **The tool itself is vanilla HTML/JS with Plotly**, computing the core
analytics (HHI, leverage, ROE stats, peer medians, cross-tabs, boxplots, the notching
reconstruction) **in-browser** so it runs standalone on a phone. The one heavy step —
a formal ordinal-logistic / decision-tree fit for feature importance — is **optional**,
run either in the Python pipeline (results baked into `data.json`) or via Pyodide in the
tool; the persuasive exhibits (boxplots, the RBC-vs-asset-risk scatter, cross-tabs,
notching) need none of it. No database — flat files only, matching the existing Wellabe
single-file-tool workflow.

---

## 3. The S&P pull format (the data contract)

The analyst pulls from S&P Capital IQ Pro (statutory data sourced from SNL). Because
exact CIQ field names and screen layouts drift, the contract is the **normalized CSV
schema** the pipeline ingests — the analyst maps S&P fields onto these column names in
the template, not the other way around.

**Grain:** one row per **AM Best rating unit** (group), as of a single aligned date
(**YE2025 statutory** + the rating in effect at that filing). Where a rating unit
contains several legal entities, pull the **lead/largest statutory entity** named in
the roster and note any material subs. RBC files at the legal-entity level; AM Best
assesses at the group level — record both the entity RBC and, where S&P gives it, the
group/consolidated figure.

**Pull workflow for the analyst:**
1. Screen S&P for the carriers in `carriers_seed.csv` (NAIC codes provided where known).
2. Export the financial data points in §4 to Excel.
3. Paste each carrier's assessment labels (FSR, ICR, three blocks, outlook, action date,
   source URL) into the **Assessment Capture** sheet — these come from the AM Best
   press release / S&P rating field, NOT from financials.
4. Save into `data/raw/`. The pipeline validates every row against the dictionary and
   flags missing/implausible values before analysis.

**Alignment rules (enforce in `clean.py`):**
- All financials YE2025 statutory unless noted; 5-year series = 2021–2025.
- All ratios on a consistent basis (RBC on **CAL** basis: TAC ÷ CAL RBC).
- Currency in $000s; percentages as decimals; years as text.
- One assessment snapshot per carrier, dated; if a rating changed mid-period, use the
  one in effect at YE2025 and record the action date so transition cases are visible.

---

## 4. What to pull from S&P — the variable dictionary

Grouped by the block each metric is meant to explain. Fields marked **[D]** are
**derived** by `features.py`, not pulled. Everything else is pulled from S&P/SNL
statutory pages (source hints given; analyst confirms exact CIQ field).

### 4.0 Identifiers & metadata
| field | definition / source |
|---|---|
| `amb_number` | AM Best rating-unit ID |
| `rating_unit_name` | group name as AM Best names it |
| `lead_entity` | legal entity whose statutory statement is pulled |
| `naic_code` | NAIC company code of lead entity |
| `domicile_state` | lead entity domicile |
| `ownership` | mutual / stock / MHC / fraternal / RRG |
| `ultimate_parent` | top of ownership chain |
| `data_as_of` | statutory statement date (YE2025) |
| `stratum` | sampling tag from roster (§5) — for QC, not modeling |

### 4.1 Rating outcomes (the targets, Y)
| field | definition / source |
|---|---|
| `fsr` | Financial Strength Rating (A++ … D) — AM Best release |
| `icr` | Long-Term Issuer Credit Rating (aaa … c) — AM Best release |
| `outlook` | stable / positive / negative |
| `under_review` | flag + implication (developing/negative/positive) |
| `bs_assessment` | Strongest … Very Weak |
| `op_assessment` | Strong / Adequate / Marginal / Weak |
| `bp_assessment` | Favorable / Neutral / Limited / Very Limited |
| `erm_assessment` | capture only — not modeled |
| `rating_action_date` | date of the action that set the above |
| `last_action_type` | affirm / upgrade / downgrade / outlook change / under review |
| `source_url` | AM Best press release or S&P rating record |

### 4.2 Balance-sheet block (X1)
**Capital adequacy**
| field | definition / source |
|---|---|
| `rbc_cal_pct` | TAC ÷ Company Action Level RBC — **primary** (S&P RBC page / Five-Year Hist.) |
| `tac_usd` | Total Adjusted Capital |
| `acl_rbc_usd` | Authorized Control Level RBC |
| `capital_surplus_usd` | capital & surplus |
| `avr_usd` | Asset Valuation Reserve (cushion context) |

**Capital quality**
| field | definition / source |
|---|---|
| `surplus_notes_usd` | surplus notes outstanding |
| `surplus_notes_pct` | **[D]** surplus notes ÷ (capital & surplus + surplus notes) |
| `reinsurance_leverage` | reinsurance recoverable / capital (counterparty reliance) |
| `modco_funds_withheld_usd` | modco / funds-withheld balances if material |
| `capital_contributions_5yr` | parent capital infusions, 5-yr (capital mobility) |

**Asset risk**
| field | definition / source |
|---|---|
| `higher_risk_leverage` | **[D]** (Sched BA + unaffiliated common stock + real estate + below-IG bonds) ÷ capital & surplus — **the key asset-risk metric** |
| `bonds_pct` | bonds ÷ total invested assets |
| `naic_class1_pct` | NAIC 1 bonds ÷ total bonds |
| `naic_class2_pct` | NAIC 2 bonds ÷ total bonds |
| `below_ig_pct` | NAIC 3–6 bonds ÷ total bonds |
| `schedule_ba_pct` | Schedule BA (alternatives/LP/PE) ÷ invested assets |
| `mortgage_pct` | mortgage loans ÷ invested assets |
| `cml_pct` | commercial mortgage subset ÷ invested assets |
| `real_estate_pct` | real estate ÷ invested assets |
| `affiliated_pct` | affiliated investments ÷ invested assets |
| `net_unrealized_usd` | net unrealized gain/(loss) on bonds (rate-driven drag) |
| `net_unrealized_pct_cap` | **[D]** net unrealized ÷ capital & surplus |
| `bond_avg_maturity` | weighted avg maturity / effective duration |
| `fhlb_advances_usd` | FHLB borrowings (liquidity/leverage) |

**Reserve adequacy**
| field | definition / source |
|---|---|
| `reserves_to_surplus` | **[D]** total reserves ÷ capital & surplus |
| `adverse_dev_3yr` | reserve strengthening / adverse development, last 3 yrs ($ + flag) |
| `aat_result` | asset adequacy / cash-flow testing result if disclosed (pass/shortfall) |

### 4.3 Operating-performance block (X2)
Pull each metric as a **5-year series (2021–2025)** unless noted; `features.py` derives
level, volatility, and trend, then `composite.py` rebenchmarks against peers.
| field | definition / source |
|---|---|
| `net_income_t … t4` | statutory net income, 5 yrs |
| `roe_t … t4` | return on equity, 5 yrs |
| `roa_t … t4` | return on assets, 5 yrs |
| `pretax_operating_income_t…t4` | pretax operating gain **ex realized capital gains** (strips one-time gains) |
| `ah_combined_ratio_t…t4` | A&H combined ratio, 5 yrs — **key for senior carriers** |
| `benefit_ratio_t…t4` | total benefits / premium (loss ratio) |
| `expense_ratio_t…t4` | expense / premium |
| `net_premium_t…t4` | net premium written, 5 yrs |
| `uw_gain_loss_t` | underwriting gain/(loss), current |
| `net_investment_income_t` | NII, current |
| `realized_gains_t` | realized capital gains, current (one-time reliance) |
| `ceded_premium_pct` | ceded ÷ direct premium |
| **[D]** `roe_5yr_mean`, `roe_5yr_std`, `roe_trend` | level / volatility / OLS slope of ROE |
| **[D]** `ah_cr_level`, `ah_cr_trend` | last value + slope of A&H combined ratio |
| **[D]** `earnings_mix` | NII ÷ (NII + UW gain) — investment-income reliance |
| **[D]** `oneoff_reliance` | realized gains ÷ pretax income |
| **[D]** `premium_cagr_5yr` | 5-yr premium growth |
| **[D]** `roe_vs_composite` | `roe_5yr_mean` minus L/H composite median (peer-relative) |
| **[D]** `growth_strain_flag` | negative recent ROE **and** high premium CAGR **and** OP held ≥ Adequate → carrier in a credited new-business-strain phase (the Wellabe / Physicians-Mutual bucket) |

### 4.4 Business-profile block (X3)
**Scale**
| field | definition / source |
|---|---|
| `total_assets_usd` | admitted assets |
| `total_premium_usd` | total net premium |
| `medsup_market_rank` | Med Sup market share / national rank if available |

**Diversification — premium by line** (pull each as $; `features.py` converts to %):
`prem_medsup`, `prem_hosp_indemnity`, `prem_other_ah`, `prem_ltc`, `prem_stc`,
`prem_life_term`, `prem_life_whole`, `prem_life_ul_iul`, `prem_annuity`,
`prem_preneed_final_expense`, `prem_group`, `prem_disability`, `prem_dental_vision`,
`prem_credit`, `prem_other`.
| field | definition / source |
|---|---|
| **[D]** `hhi_lines` | Herfindahl index on line-of-business % (concentration) |
| **[D]** `material_line_count` | count of lines ≥ 10% of premium |
| **[D]** `risk_type_mix` | morbidity % / mortality % / market-spread % (map lines→risk types) |

**Geography & distribution**
| field | definition / source |
|---|---|
| `states_licensed` | count of states licensed |
| `top_state_pct` | premium share of largest state |
| `top5_state_pct` | premium share of top 5 states |
| `distribution_channels` | list: independent-agent/IMO, career/captive, DTC/direct, worksite, BGA, bank/BD |
| **[D]** `channel_count` | number of material channels |
| `dtc_brand_flag` | meaningful direct-to-consumer brand (Y/N) |
| `parent_fsr` | parent/affiliate rating (franchise/support) |

> **Composite note (`composite.py`):** AM Best grades operating performance against its
> own L/H peer composites, which we cannot see. Approximate with **sample medians by
> product segment** (senior-health specialist / diversified L&H / preneed / supplemental
> worksite). Label every peer-relative metric as an approximation in the white paper.

---

## 5. The carrier roster (who to pull)

Pull **all** of the following as the seed (`carriers_seed.csv`). The point is **spread**,
not a clean set of healthy A-rated Med Sup carriers — those would cluster and teach
nothing. Stratify across FSR (B++→A++), across balance-sheet tiers (Strong→Strongest),
across business-profile tiers (Limited→Favorable), and **oversample recent transitions**
(upgrades/downgrades/under-review), which reveal what moved.

> Ratings/assessments shown are **best-known and must be confirmed at pull time** — that
> confirmation is part of the job. Tags: `[core]` direct Wellabe peer · `[transition]`
> recent rating action · `[anchor]` fortress benchmark · `[low]` lower-tier for range ·
> `[preneed]`. Lead entity given where known.

### 5.1 Senior health / Med Sup / supplemental — core comparators
- **Wellabe Group** — Medico Insurance Co / American Republic / Great Western `[core]` (the subject)
- **Physicians Mutual** — Physicians Mutual Ins Co / Physicians Life `[core][transition]` (A+, Strongest, ~1200% RBC, upgraded 11/2025)
- **Mutual of Omaha** — United of Omaha / United World Life `[core]` (A+, Very Strong / Strongest BCAR, ~423%)
- **Guarantee Trust Life** — GTL Ins Co `[core]` (A, Strongest, ~800%) — hospital indemnity + Med Sup + STC, closest product match
- **Aflac** — Continental American Ins Co / American Family Life of Columbus `[core][anchor]` (A+, Strongest)
- **Globe Life** — United American / Family Heritage / American Income / Liberty National `[core]` (A, Strong, ~316%)
- **CNO Financial** — Bankers Life & Casualty `[core]`; Washington National `[core]`; Colonial Penn `[core]`
- **Aetna / CVS** — Continental Life Ins Co of Brentwood `[core]`; American Continental Ins Co `[core]`
- **Cigna** — Loyal American Life `[core]`; American Retirement Life `[core]`; Cigna National Health `[core]`
- **Humana** — Humana Insurance Co `[core]`
- **UnitedHealthcare** — UnitedHealthcare Ins Co (AARP Med Sup) `[core][anchor]`
- **Combined Insurance (Chubb)** — Combined Ins Co of America `[core]`
- **Lumico (RGA)** — Lumico Life Ins Co `[core]`
- **Pekin Life** — Pekin Life Ins Co `[core]`
- **American National (Brookfield Re)** — Standard Life & Accident `[core]`; American National Ins Co `[core]`
- **Kemper** — Reserve National / Equitable National `[core]`
- **ManhattanLife** — ManhattanLife Assurance `[core][low]`; Western United Life `[low]`; Standard Life & Casualty; Family Life
- **New Era Life** — New Era Life / Philadelphia American `[core][low]`
- **Government Personnel Mutual** — GPM Health & Life `[core]`
- **Americo** — Americo Financial Life & Annuity `[core]`
- **Atlantic American** — Bankers Fidelity Life Group `[core][transition]` (A-, under review 6/2026)
- **Heartland National** `[low]`; **Sentinel Security Life** `[low]`; **Everence** `[core]`
- **Continental General** — `[low]` (LTC/supplemental, weaker — deliberate low-end variance)

### 5.2 Preneed / final expense (Wellabe's preneed line)
- **National Guardian Life (NGL)** `[preneed]` (A) · **Homesteaders Life** `[preneed]` (A-) ·
  **Funeral Directors Life (FDLIC)** `[preneed]` (A-) · **Forethought Life (Global Atlantic/KKR)** `[preneed]` ·
  **Security National Life** `[preneed]` · **Investors Heritage (Aquarian)** `[preneed]` ·
  **Trinity Life / American-Amicable** `[preneed][low]` · **Assurity Life** `[preneed]` (conservative mutual; likely Strongest — verify) ·
  **Liberty Bankers Life** `[core][low]`

### 5.3 Fortress anchors — Strongest "all the way down" (top of the RBC distribution)
Pull 4–6 to anchor the ceiling; they print very high RBC and prove that above the bar,
more capital buys nothing on the rating.
- **USAA Life** · **Thrivent** · **State Farm Life** · **Northwestern Mutual** ·
  **New York Life** · **MassMutual** · **Guardian Life** `[anchor]` (Guardian also writes some supplemental)

### 5.4 Deliberate downside / transition cases (high learning value)
- **American Southern (Atlantic American P&C sibling)** `[transition]` (downgraded 4/2026, BS Very Strong→Strong on reserves + account concentration)
- **Citizens Inc / CICA Life** `[low]` · **Kansas City Life** `[low]` · **National Western Life** ·
  **Penn Mutual** · **Lincoln Financial** (pressured large L&H — useful Very-Strong/Strong variance) ·
  any L/H carrier downgraded in the last 24 months that S&P surfaces.

**Target N:** ~100–130 rating units. If S&P returns clean data for fewer, prioritize
keeping the full spread across all three tiers and the transition cases over raw count.

---

## 6. The analyses (the actual learning)

For each, produce: the figure(s), the cross-tab table, and a 2–4 sentence plain-language
finding written to `output/whitepaper/findings.md`. **Always overlay a Wellabe marker.**

### 6.1 Balance-sheet block: RBC → assessment, and the asset-risk confound
- **Fig BS-1:** boxplot of `rbc_cal_pct` grouped by `bs_assessment`. Expect wide,
  overlapping bands (Strongest already spans ~400–1200%).
- **Fig BS-2 (the money chart):** scatter `rbc_cal_pct` (x) vs `higher_risk_leverage`
  (y), colored by `bs_assessment`, Wellabe marked. The thesis made visible: two carriers
  at equal RBC land in different tiers because of asset risk.
- **Model:** ordinal logistic / decision tree predicting `bs_assessment` from
  `rbc_cal_pct`, `higher_risk_leverage`, `surplus_notes_pct`, `below_ig_pct`,
  `net_unrealized_pct_cap`, `reserves_to_surplus`. Report feature importance + the
  decision thresholds the tree finds.
- **Output rule format:** "Strongest observed down to ~X% RBC provided higher-risk
  leverage < ~Y% and surplus notes < ~Z% of capital."

### 6.2 Operating-performance block: earnings → assessment (peer-relative)
- Build composites first (`composite.py`), then compute `roe_vs_composite` etc.
- **Fig OP-1:** boxplot `roe_vs_composite` by `op_assessment`.
- **Fig OP-2:** `ah_cr_level` and `ah_cr_trend` by `op_assessment`.
- **Critical:** highlight `growth_strain_flag` carriers separately — they're held at
  Adequate despite negative ROE (Wellabe, Physicians Mutual during strain). Their
  residuals ("rated better than current earnings justify") are their own finding and the
  bucket Wellabe lives in.
- **Output rule format:** "OP drops toward Marginal when 5-yr ROE trails the composite by
  ≥ N points with a negative trend — *unless* in a credited growth-strain phase, where
  AM Best holds Adequate pending the projected turn."

### 6.3 Business-profile block: lines/scale → assessment
- **Fig BP-1:** scatter `total_assets_usd` (log x) vs `hhi_lines` (y), colored by
  `bp_assessment`, sized by `material_line_count`, Wellabe marked.
- **Cross-tab:** `bp_assessment` vs (`risk_type_mix`, `channel_count`, `top5_state_pct`).
- **Named checks:** GTL is *Limited* business profile despite *Strongest* balance sheet
  (capital does nothing here); Mutual of Omaha is *Favorable* because it broke beyond the
  senior niche; Wellabe & Physicians Mutual are *Neutral* (solid but niche-bound).
- **Output rule format:** "Favorable requires assets > ~$N **and** a genuine second risk
  type beyond the core niche; Neutral is the ceiling for a single-market specialist
  regardless of how many products are added inside that market."

### 6.4 Notching reconstruction (ties it together)
- Map `bs_assessment` → baseline ICR via the published baseline table.
- Apply observed block assessments as notches via the published ranges.
- Predict ICR; compare to actual `icr`. Tabulate residuals.
- Most should reconcile within a notch; the misses expose the comprehensive adjustment
  and committee judgment. **Fig N-1:** predicted vs actual ICR with the residual carriers
  labeled. This is the single most persuasive exhibit for the white paper.

---

### 6.5 The interactive tool (`tool/index.html`) — primary deliverable
Mobile-first, single file, GitHub-Pages-hostable. Design notes:
- **Data in:** loads `data.json` from the pipeline by default; also accepts a dropped/
  pasted CSV of the filled template and derives metrics in-browser, so it works before
  the pipeline exists.
- **Layout:** one-column, touch-first, large tap targets. A sticky segmented control
  switches between four views: **Balance Sheet · Operating · Business Profile · Notching.**
  Each view is one screenful: the figure on top, a short auto-generated finding line, and
  collapsible detail. No side-by-side panels (they don't survive a phone screen).
- **Every view marks Wellabe** and lets you tap any point to read that carrier's row.
- **Filters:** a single bottom sheet with toggles for stratum, ownership, segment, and a
  "hide fortress anchors" switch (so the senior-specialist cloud isn't swamped by the
  A++ mutuals).
- **Figures:** BS-2 (RBC vs higher-risk-leverage, colored by tier) is the landing view —
  it's the most persuasive. Boxplots use jittered points so thin cells stay honest.
- **Export:** a button on each view emits that figure as SVG/PNG and its data as CSV into
  the white-paper pack, so the paper is assembled from exactly what's on screen.
- **Styling:** field-guide palette (ink `#0B1C2C`, accent `#2E5A88`); EB Garamond display
  / DM Sans body if loaded, system fallback otherwise.
- **No localStorage / sessionStorage** (unsupported in this artifact context); hold all
  state in JS memory for the session.

---

## 7. (BCAR from first principles — out of scope)
Reconstructing real BCAR scores would require Best's Credit Report access, which we do
not have. Not pursued. The balance-sheet *assessment* (§6.1) is the target instead, and
it is the thing that feeds the rating anyway.

## 8. White-paper integration
Every view in the tool can export to `output/whitepaper/`:
- figures as **PNG + SVG** (SVG so they scale in the Word/HTML paper),
- tables as **CSV + a Markdown snippet**,
- a running **`findings.md`** in prose, each finding tied to its figure number.
The paper's empirical section is assembled from these in order:
BS-1/BS-2 → OP-1/OP-2 → BP-1 → N-1, each with its finding and a "Where Wellabe sits"
sentence. Because the exhibits come straight out of the tool, the paper and the tool
never disagree.

## 9. Build order for Claude Code
1. Generate `data/variable_dictionary.csv` and `data/carriers_seed.csv` from §4–§5.
2. **Build `tool/index.html` first**, against a small synthetic/sample dataset, so the
   mobile UI and all four views (§6.5) are working and reviewable on a phone immediately.
3. Build `ingest.py` + `clean.py` + a validation report (missingness by field/carrier),
   then `features.py` + `composite.py`, emitting `data.json` for the tool.
4. **Pause for the analyst to pull S&P data into the template**, then regenerate `data.json`.
5. Wire the three analyses (§6.1–6.3) + notching (§6.4) into the tool's four views with
   live data; verify the Wellabe overlay on each.
6. Add the export buttons and assemble the white-paper output pack (§8).
7. (Optional) add the formal ordinal/tree fit for feature importance, in pipeline or Pyodide.

## 10. Guardrails
- Never invent a financial value or an assessment label; missing = blank, flagged by
  validation. Every assessment must trace to a `source_url`.
- Keep peer-relative metrics labeled as approximations (we don't have AM Best's composites).
- State sample sizes on every figure; with ~120 carriers, cells get thin — report counts.
- This is descriptive/explanatory, not predictive of future AM Best actions; say so.
