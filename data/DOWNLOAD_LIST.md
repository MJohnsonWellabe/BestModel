# S&P pulls — what's LEFT to download

Pull the **Life/Fraternal Financial Highlights** export ($000, "Last Four Years & YTD") for each
entity below, then drop them into the app's **＋ Data** tab. Look each up on SNL by the **exact filing
entity** given — that's the statutory filer, which is what was tripping up the wrong-sub lookups.

## ✅ Already loaded (no action)
GTL · Mutual of Omaha · Assurity · American Southern · Continental General · Funeral Directors ·
National Guardian · Lumico · Security National · New York Life · Guardian · Lincoln · USAA Life ·
ManhattanLife (The Manhattan Life Ins Co) · Aflac · CNO (Bankers Life, Washington National,
Colonial Penn) · Aetna (Continental Life of Brentwood, American Continental) · Cigna/HCSC (Loyal
American, American Retirement Life) · Humana · UnitedHealthcare · Combined · Western United ·
American National · Pekin.

## ⚠️ Re-pull (wrong entity last time)
| Rating unit | Pull THIS exact entity |
|---|---|
| Wellabe Group | **Medico Insurance Company** (you sent American Republic — also send **Great Western Insurance Company** so I can roll up the group) |
| Atlantic American — Bankers Fidelity | **Bankers Fidelity Life Insurance Company** (you sent the tiny "Bankers Fidelity Assurance Company") |

## ⬜ Still to pull — existing roster (exact SNL filing entity)
| Rating unit | Filing entity to look up |
|---|---|
| Physicians Mutual | Physicians Mutual Insurance Company *(and Physicians Life Insurance Company)* |
| Globe Life | United American Insurance Company |
| Cigna — National Health | HealthSpring National Health Insurance Company *(renamed; verify it files)* |
| American National — Standard L&A | Standard Life and Accident Insurance Company |
| Kemper — Reserve National | Reserve National Insurance Company |
| New Era Life | New Era Life Insurance Company |
| Philadelphia American | Philadelphia American Life Insurance Company |
| Government Personnel Mutual | Government Personnel Mutual Life Insurance Company |
| Americo | Americo Financial Life and Annuity Insurance Company |
| Heartland National | Heartland National Life Insurance Company |
| Sentinel Security Life | Sentinel Security Life Insurance Company |
| Liberty Bankers | Liberty Bankers Life Insurance Company |
| Homesteaders Life | Homesteaders Life Company |
| Forethought (Global Atlantic) | Forethought Life Insurance Company |
| Investors Heritage | Investors Heritage Life Insurance Company |
| American-Amicable / Trinity | American-Amicable Life Insurance Company of Texas *(or Trinity Life Insurance Company)* |
| Citizens Inc — CICA | CICA Life Insurance Company of America |
| Kansas City Life | Kansas City Life Insurance Company |
| National Western Life | National Western Life Insurance Company |
| Everence | Everence Insurance Company *(fraternal — may not file a standard blank; could come back thin)* |

## ⏸️ Giants — de-prioritized (skip unless you want them; the ones already loaded stay)
Skipping per "fewer giant carriers": **Thrivent, State Farm Life, Northwestern Mutual, MassMutual,
Penn Mutual.** *(New York Life, Guardian, USAA, Lincoln, American National are already loaded — keeping them, all info is good info.)*

## ➕ Standalone peers to ADD — researched (NAIC confirmed; all file their own statutory stmt)
These came back **standalone** (independent — won't distort the group-support analysis) and are
now in the roster. Pull each (Life/Fraternal Highlights) by NAIC:

| Peer | Filing entity | NAIC | AM Best |
|---|---|---|---|
| Boston Mutual Life | Boston Mutual Life Insurance Company | 70807 | A |
| Illinois Mutual Life | Illinois Mutual Life Insurance Company | 64580 | A- (Strongest/Adequate/Limited) |
| USAble Life | USAble Life | 94358 | A (Strongest/Adequate/Limited) |
| 5 Star Life | 5 Star Life Insurance Company | 15742 | A- |
| Royal Neighbors of America | Royal Neighbors of America | 57657 | A (Strongest/Adequate/Neutral) |
| Gleaner Life | Gleaner Life Insurance Society | *verify* | B++ (under review developing) |
| Central States Health & Life | Central States Health & Life Co of Omaha | 61751 | A- (Very Strong/Adequate/Limited) |

**Researched but turned out GROUP-owned (skip — would add group-support noise):** Gerber Life
(Western & Southern), Trustmark, Cincinnati Life (Cincinnati Financial), Texas Life (Wilton Re),
Companion Life SC (BCBS-SC), Pan-American Life, Standard Security Life NY (Delphi/Tokio Marine).

> Full NAIC + filing-entity table for the **entire** roster is now in `data/assessments.csv`
> (and baked into the tool's `carriers.js`), so every pull can be matched to the exact SNL entity.
> NAIC codes are from a time-boxed research pass — verify if a pull comes back empty.
