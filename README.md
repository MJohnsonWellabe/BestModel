# AM Best Rating Decoder

Reverse-engineers how AM Best translates statutory financial reality into its assessment
blocks (**balance sheet · operating performance · business profile**) and the final FSR,
using public AM Best assessment labels as the target and S&P Capital IQ / SNL statutory data
as the inputs. Feeds the Office of the Chief Actuary's AM Best white paper.

> Full project spec: [`PLAN.md`](PLAN.md). Exact data-pull instructions: [`data/SP_PULL_SPEC.md`](data/SP_PULL_SPEC.md).
> Rating mechanics reference: [`docs/AMBest_ELT_FieldGuide_v41.docx`](docs/).

## What's here

| Path | What it is |
|---|---|
| `tool/index.html` | **Primary deliverable** — single-file, mobile-first interactive explorer (loads `tool/data.json`). |
| `src/` | Python data-prep pipeline: parse raw S&P pulls → derive metrics → emit `data.json`. |
| `templates/sp_pull_template.xlsx` | Analyst data-entry workbook (Read Me · Data Dictionary · Carrier Roster · Financial Pull). |
| `data/carriers_seed.csv` | Carrier roster + stratification tags (generated from the template). |
| `data/variable_dictionary.csv` | Field definitions + sources (generated from the template). |
| `data/SP_PULL_SPEC.md` | The exact, per-source list of what to pull from S&P. |
| `data/raw/` | Where raw S&P pulls land — **gitignored** (licensed S&P/SNL data stays local). |
| `output/whitepaper/` | Static export pack (figures, tables, `findings.md`) generated from the same frame the tool uses. |

## Quickstart

```bash
pip install -r requirements.txt          # openpyxl required; pandas/numpy/scipy optional
python src/make_seeds.py                  # regenerate seed CSVs from the template (if it changed)
python src/seed_assessments.py            # (re)write data/assessments.csv — the AM Best labels (Y)

# 1. Drop each carrier's raw S&P "Life/Fraternal Financial Highlights" export into data/raw/
python src/build.py                       # parse + derive + join labels + notch → tool/data.json
#    prints a missingness report (data/processed/missingness.csv) so you see coverage first

# 2. Open the tool (any static server; no build step). Ships with embedded demo data and
#    switches to the live data.json automatically once it carries enough rated carriers.
python -m http.server -d tool 8080        # → http://localhost:8080

# 3. White-paper export pack (notching reconstruction is real now; financial figures
#    export from the tool once data.json is populated):
python src/whitepaper.py                  # → output/whitepaper/{findings.md, tables/*}
```

> `tool/data.json` and `data/processed/missingness.csv` are **build artifacts** (gitignored —
> derived from licensed S&P data). Run `python src/build.py` to regenerate them locally.

## The data workflow (how to feed it)

1. **Pull from S&P** per [`data/SP_PULL_SPEC.md`](data/SP_PULL_SPEC.md). The Life/Fraternal
   Financial Highlights export is the backbone — the parser auto-extracts RBC, capital, asset
   quality, and the 5-year operating series from it. A short supplemental list covers asset-mix
   detail, line-of-business premium, and geography.
2. **Drop the files** into `data/raw/` (one per carrier; any filename — the parser keys off the
   carrier name inside the sheet and the roster).
3. **Run `python src/build.py`.** It parses every file, derives the §4 metrics, joins the
   assessment labels, validates against the dictionary, and rewrites `tool/data.json`. Missing or
   implausible values are reported, never invented.
4. **Refresh the tool / paper** — both read the regenerated `data.json`, so they never disagree.

## Guardrails

- Never invent a financial value or assessment label; missing = blank, surfaced by validation.
- Every assessment traces to a `source_url`.
- Peer-relative metrics are approximations (we don't have AM Best's internal composites) — labeled as such.
- Descriptive/explanatory, **not** predictive of future AM Best actions.
- `data/raw/` is gitignored: licensed S&P/SNL pulls must not be committed.
