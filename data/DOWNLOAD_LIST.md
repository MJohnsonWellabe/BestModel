# S&P download checklist — 55 carriers

For **each** carrier below, pull the **"Life/Fraternal Financial Highlights"** export
(S&P Capital IQ Pro → company → Financial Highlights → Life/Fraternal · "Last Four Years & YTD" · $000)
and save the `.xlsx`. The lead entity is the legal company to pull. Then drop them all into the app's
**Input** tab (it parses them in-browser — no preloading needed) and/or send them here so I can verify
the parser handles every format variation.

> Naming: any filename is fine — the parser reads the company name from inside the sheet. If S&P lets
> you name the export, `RatingUnit_Highlights.xlsx` keeps the folder tidy.

| # | Rating unit | Lead entity to pull | Tag |
|---|---|---|---|
| 1 | Wellabe Group | Medico Insurance Company | core |
| 2 | Physicians Mutual | Physicians Mutual Insurance Co | core; transition |
| 3 | Mutual of Omaha | United of Omaha Life Insurance Co | core |
| 4 | Guarantee Trust Life | Guarantee Trust Life Insurance Co | core |
| 5 | Aflac | Continental American Insurance Co | core; anchor |
| 6 | Globe Life | United American Insurance Co | core |
| 7 | CNO — Bankers Life | Bankers Life & Casualty Co | core |
| 8 | CNO — Washington National | Washington National Insurance Co | core |
| 9 | CNO — Colonial Penn | Colonial Penn Life Insurance Co | core |
| 10 | Aetna/CVS — Continental Life | Continental Life Ins Co of Brentwood | core |
| 11 | Aetna/CVS — American Continental | American Continental Insurance Co | core |
| 12 | Cigna — Loyal American | Loyal American Life Insurance Co | core |
| 13 | Cigna — American Retirement Life | American Retirement Life Insurance Co | core |
| 14 | Cigna — National Health | Cigna National Health Insurance Co | core |
| 15 | Humana | Humana Insurance Co | core |
| 16 | UnitedHealthcare | UnitedHealthcare Insurance Co | core; anchor |
| 17 | Combined Insurance (Chubb) | Combined Insurance Co of America | core |
| 18 | Lumico (RGA) | Lumico Life Insurance Co | core |
| 19 | Pekin Life | Pekin Life Insurance Co | core |
| 20 | American National — Standard Life & Accident | Standard Life & Accident Insurance Co | core |
| 21 | American National | American National Insurance Co | core |
| 22 | Kemper — Reserve National | Reserve National Insurance Co | core |
| 23 | ManhattanLife — Assurance | ManhattanLife Assurance Co of America (now ManhattanLife Ins & Annuity) | core; low |
| 24 | ManhattanLife — Western United | Western United Life Assurance Co | low |
| 25 | New Era Life | New Era Life Insurance Co | core; low |
| 26 | Philadelphia American | Philadelphia American Life Insurance Co | low |
| 27 | Government Personnel Mutual | GPM Health & Life Insurance Co | core |
| 28 | Americo | Americo Financial Life & Annuity Ins Co | core |
| 29 | Atlantic American — Bankers Fidelity | Bankers Fidelity Life Insurance Co | core; transition |
| 30 | Atlantic American — American Southern | American Southern Insurance Co (P&C — may use a different template) | transition |
| 31 | Heartland National | Heartland National Life Insurance Co | low |
| 32 | Sentinel Security Life | Sentinel Security Life Insurance Co | low |
| 33 | Everence | Everence Association / Everence Ins | core |
| 34 | Continental General | Continental General Insurance Co | low |
| 35 | Liberty Bankers | Liberty Bankers Life Insurance Co | core; low |
| 36 | National Guardian Life | National Guardian Life Insurance Co | preneed |
| 37 | Homesteaders Life | Homesteaders Life Co | preneed |
| 38 | Funeral Directors Life | Funeral Directors Life Insurance Co | preneed |
| 39 | Forethought (Global Atlantic) | Forethought Life Insurance Co | preneed |
| 40 | Security National | Security National Life Insurance Co | preneed |
| 41 | Investors Heritage | Investors Heritage Life Insurance Co | preneed |
| 42 | American-Amicable / Trinity | Trinity Life Insurance Co | preneed; low |
| 43 | Assurity Life | Assurity Life Insurance Co | preneed |
| 44 | USAA Life | USAA Life Insurance Co | anchor |
| 45 | Thrivent | Thrivent Financial for Lutherans | anchor |
| 46 | State Farm Life | State Farm Life Insurance Co | anchor |
| 47 | Northwestern Mutual | Northwestern Mutual Life Insurance Co | anchor |
| 48 | New York Life | New York Life Insurance Co | anchor |
| 49 | MassMutual | Massachusetts Mutual Life Insurance Co | anchor |
| 50 | Guardian Life | Guardian Life Insurance Co of America | anchor |
| 51 | Citizens Inc — CICA | CICA Life Insurance Co of America | low |
| 52 | Kansas City Life | Kansas City Life Insurance Co | low |
| 53 | National Western Life | National Western Life Insurance Co | variance |
| 54 | Penn Mutual | Penn Mutual Life Insurance Co | variance |
| 55 | Lincoln Financial | Lincoln National Life Insurance Co | variance |

**Already pulled (samples in hand):** #3 Mutual of Omaha, #4 Guarantee Trust Life, and American
Republic (a Wellabe entity — for #1 pull **Medico** as the named lead, or send American Republic +
Great Western too and I'll handle the Wellabe group roll-up).

**Heads-up on format variation:** a few entities (American Southern = P&C; some Humana/UHC health
entities) may export on a different highlights template with different row labels. The in-browser
parser flags any rows it can't place; send me those and I'll extend the alias map so every format
digests cleanly.
