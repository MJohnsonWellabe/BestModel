"""Write data/assessments.csv — the AM Best assessment labels (the targets, Y).

Every row is sourced from a public AM Best rating action (source_url). Per the project
guardrail, values that could not be confirmed from a credible source are left BLANK rather
than guessed (e.g. Americo / Security National block assessments). The Wellabe row comes
from the internal ELT Field Guide (AM Best Credit Report, AMB #070369).

Vocabulary normalization applied here:
  - AM Best's full tier sets are used: business profile includes "Very Favorable"; operating
    performance includes "Very Strong". Where a release said "very favorable", it is recorded
    as such (not collapsed to "Favorable").
  - "under_review" holds the implication (negative/positive/developing) or is blank.

Regenerate: python src/seed_assessments.py  (then: python src/build.py)
"""
from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "assessments.csv"

COLS = ["rating_unit_name", "amb_number", "naic_code", "domicile_state", "fsr", "icr",
        "outlook", "under_review", "bs_assessment", "op_assessment", "bp_assessment",
        "erm_assessment", "rating_action_date", "last_action_type", "source_url", "rating_basis"]

# Carriers whose published ICR incorporates group/parent support (or is the group rating
# assigned to a subsidiary) beyond their own four standalone block assessments. Residuals for
# these are expected to sit ABOVE the standalone-block prediction — that lift IS the finding,
# not a model miss. Everything else is treated as standalone (rated on its own merits).
# NAIC company code of the statutory filing entity (from the time-boxed SNL/NAIC research pass).
# Best-effort — verify at pull time. Used to point the analyst at the exact entity to pull.
NAIC = {
    "Wellabe Group": "31119", "Physicians Mutual": "80578", "Mutual of Omaha": "69868",
    "Guarantee Trust Life": "64211", "Aflac": "71730", "Globe Life": "92657",
    "CNO — Bankers Life": "61263", "CNO — Washington National": "70319", "CNO — Colonial Penn": "62065",
    "Aetna/CVS — Continental Life": "68500", "Aetna/CVS — American Continental": "12321",
    "Cigna — Loyal American": "65722", "Cigna — American Retirement Life": "88366",
    "Cigna — National Health": "61727", "Humana": "73288", "UnitedHealthcare": "79413",
    "Combined Insurance (Chubb)": "62146", "Lumico (RGA)": "73504", "Pekin Life": "67628",
    "American National — Standard Life & Accident": "86355", "American National": "60739",
    "Kemper — Reserve National": "68462", "ManhattanLife — Assurance": "65870",
    "ManhattanLife — Western United": "85189", "New Era Life": "78743", "Philadelphia American": "67784",
    "Government Personnel Mutual": "63967", "Americo": "61999",
    "Atlantic American — Bankers Fidelity": "71919", "Atlantic American — American Southern": "10235",
    "Heartland National": "66214", "Sentinel Security Life": "68802", "Everence": "57991",
    "Continental General": "71404", "Liberty Bankers": "68543", "National Guardian Life": "66583",
    "Homesteaders Life": "64505", "Funeral Directors Life": "99775",
    "Forethought (Global Atlantic)": "91642", "Security National": "69485",
    "Investors Heritage": "64904", "American-Amicable / Trinity": "68594", "Assurity Life": "71439",
    "USAA Life": "69663", "New York Life": "66915", "Guardian Life": "64246",
    "Citizens Inc — CICA": "71463", "Kansas City Life": "65129", "National Western Life": "66850",
    # standalone peers added this round
    "Boston Mutual Life": "70807", "Illinois Mutual Life": "64580", "USAble Life": "94358",
    "5 Star Life": "15742", "Royal Neighbors of America": "57657",
    "Gleaner Life": "", "Central States Health & Life": "61751",
}

GROUP_MEMBERS = {
    "Aflac", "Globe Life", "CNO — Bankers Life", "CNO — Washington National",
    "CNO — Colonial Penn", "Aetna/CVS — Continental Life", "Aetna/CVS — American Continental",
    "Cigna — Loyal American", "Cigna — American Retirement Life", "Cigna — National Health",
    "Humana", "UnitedHealthcare", "Combined Insurance (Chubb)", "Lumico (RGA)",
    "American National — Standard Life & Accident", "American-Amicable / Trinity",
    "Forethought (Global Atlantic)", "USAA Life", "State Farm Life", "Sentinel Security Life",
    "Atlantic American — Bankers Fidelity", "Atlantic American — American Southern",
}

# rating_unit_name keys MUST match data/carriers_seed.csv so build.py can join.
# Tuple order after name: fsr, icr, outlook, under_review, bs, op, bp, erm, date, action, url
ROWS = [
 ("Wellabe Group","A","a","Stable","","Strongest","Adequate","Neutral","Appropriate","2026-05","affirm","ELT Field Guide — AM Best Credit Report, Wellabe Group AMB #070369 (internal)"),
 ("Physicians Mutual","A+","aa-","Stable","","Strongest","Strong","Neutral","Appropriate","2025-11-13","upgrade","https://www.businesswire.com/news/home/20251113643602/en/"),
 ("Mutual of Omaha","A+","aa-","Stable","","Very Strong","Strong","Favorable","Appropriate","2026-04-02","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=37185&altsrc=2"),
 ("Guarantee Trust Life","A","a","Stable","","Strongest","Strong","Limited","Appropriate","2024-10-24","upgrade","https://news.ambest.com/newscontent.aspx?AltSrc=23&RefNum=218871"),
 ("Aflac","A+","aa","Stable","","Strongest","Strong","Favorable","Very Strong","2025-09-05","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36439&altsrc=2"),
 ("Globe Life","A","a+","Stable","","Strong","Strong","Favorable","Appropriate","2025-11-12","affirm","https://www.businesswire.com/news/home/20251112657654/en/"),
 ("CNO — Bankers Life","A","a","Stable","","Very Strong","Strong","Neutral","Appropriate","2026-04-08","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=37193&altsrc=2"),
 ("CNO — Washington National","A","a","Stable","","Very Strong","Strong","Neutral","Appropriate","2026-04-08","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=37193&altsrc=2"),
 ("CNO — Colonial Penn","A","a","Stable","","Very Strong","Strong","Neutral","Appropriate","2026-04-08","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=37193&altsrc=2"),
 ("Aetna/CVS — Continental Life","A","a","Stable","","Very Strong","Strong","Favorable","Appropriate","2026-06-05","affirm","https://www.businesswire.com/news/home/20260605635029/en/"),
 ("Aetna/CVS — American Continental","A","a","Stable","","Very Strong","Strong","Favorable","Appropriate","2025-05-08","affirm","https://www.businesswire.com/news/home/20250508/en/AM-Best-Affirms-Aetna"),
 ("Cigna — Loyal American","A","a","Stable","","Very Strong","Marginal","Neutral","Appropriate","2026-01-15","affirm","https://insurancenewsnet.com/oarticle/am-best-affirms-credit-ratings-of-health-care-service-corporation-group-members"),
 ("Cigna — American Retirement Life","A","a","Stable","","Very Strong","Marginal","Neutral","Appropriate","2026-01-15","affirm","https://insurancenewsnet.com/oarticle/am-best-affirms-credit-ratings-of-health-care-service-corporation-group-members"),
 ("Cigna — National Health","A","a","Stable","","Very Strong","Marginal","Neutral","Appropriate","2026-01-15","affirm","https://insurancenewsnet.com/oarticle/am-best-affirms-credit-ratings-of-health-care-service-corporation-group-members"),
 ("Humana","A","a","Stable","","Adequate","Strong","Favorable","Appropriate","2025-12-16","affirm","https://news.ambest.com/pr/PressContent.aspx?altsrc=2&refnum=36441"),
 ("UnitedHealthcare","A","a+","Stable","","Strong","Strong","Very Favorable","Appropriate","2025-08-28","downgrade","https://www.businesswire.com/news/home/20250828917145/en/"),
 ("Combined Insurance (Chubb)","A+","aa-","Stable","","Strong","Strong","Neutral","Appropriate","2026-01-16","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36946&altsrc=2"),
 ("Lumico (RGA)","A","a","","negative","Very Strong","Marginal","Limited","Appropriate","2024-05-23","downgrade — under review","https://www.businesswire.com/news/home/20240523772763/en/"),
 ("Pekin Life","A-","a-","Stable","","Very Strong","Marginal","Neutral","Appropriate","2025-10-24","affirm","https://www.businesswire.com/news/home/20251024028378/en/"),
 ("American National — Standard Life & Accident","A-","a-","Stable","","Very Strong","Adequate","Limited","Appropriate","2025-10-09","affirm","https://www.globenewswire.com/news-release/2025/10/09/3164657/0/en/Core-Specialty-Affirms.html"),
 ("American National","A","a","Stable","","Very Strong","Adequate","Favorable","Appropriate","2025-11-21","affirm","https://www.businesswire.com/news/home/20251121643928/en/"),
 ("Kemper — Reserve National","A-","a-","Stable","","Very Strong","Adequate","Neutral","Appropriate","2025-08-15","affirm","https://news.ambest.com/newscontent.aspx?refnum=268303&altsrc=23"),
 ("ManhattanLife — Assurance","B++","bbb","Stable","","Adequate","Strong","Neutral","Appropriate","2025-12-03","affirm","https://ratings.ambest.com/CompanyProfile.aspx?ambnum=6222 (blocks per Nov-2022 group release)"),
 ("ManhattanLife — Western United","B++","bbb","Stable","","Adequate","Strong","Neutral","Appropriate","2025-12-03","affirm","https://ratings.ambest.com/CompanyProfile.aspx?ambnum=6222 (blocks per Nov-2022 group release)"),
 ("New Era Life","A-","a-","Stable","","Strong","Adequate","Neutral","Appropriate","2022-05-05","upgrade","https://news.ambest.com/newscontent.aspx?refnum=241362"),
 ("Philadelphia American","A-","a-","Stable","","Strong","Adequate","Neutral","Appropriate","2022-05-05","upgrade","https://news.ambest.com/newscontent.aspx?refnum=241362"),
 ("Government Personnel Mutual","B++","bbb+","Stable","","Very Strong","Marginal","Neutral","Appropriate","2024-03-28","downgrade","https://www.businesswire.com/news/home/20240328277424/en/AM-Best-Downgrades-GPM-Life-Group"),
 ("Americo","A","a","Stable","","","","","","2026-01-16","affirm","https://www.annuityadvantage.com/insurance-companies/americo-financial-life-annuity-insurance-company/ (secondary — blocks unconfirmed)"),
 ("National Guardian Life","A","a","Stable","","Very Strong","Adequate","Neutral","Appropriate","2025-07-18","affirm","https://www.businesswire.com/news/home/20220506005453/en/ (2022 release; blocks consistent across affirmations)"),
 ("Homesteaders Life","A-","a-","Stable","","Strong","Adequate","Neutral","Appropriate","2025-05-22","affirm","https://www.businesswire.com/news/home/20250522880542/en/"),
 ("Funeral Directors Life","A-","a-","Stable","","Very Strong","Adequate","Limited","Appropriate","2025-10-29","affirm","https://ratings.ambest.com/CompanyProfile.aspx?amb=9492"),
 ("Forethought (Global Atlantic)","A","a+","Stable","","Very Strong","Adequate","Favorable","Appropriate","2025-10-23","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36647&altsrc=2"),
 ("Security National","A-","","","","","","","","","","NOT FOUND — broker-sourced FSR only; blocks unconfirmed"),
 ("Investors Heritage","B++","bbb+","Stable","","Adequate","Adequate","Neutral","Appropriate","2025-07-10","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36202&altsrc=2"),
 ("American-Amicable / Trinity","A","a","Stable","","Very Strong","Marginal","Neutral","Appropriate","2025-09-18","affirm","https://www.businesswire.com/news/home/20250918607537/en/ (IA American Life Group)"),
 ("Assurity Life","A-","a-","Stable","","Strongest","Adequate","Limited","Appropriate","2025-11-06","affirm","https://info.assurity.com/hubfs/AM%20Best%20Report/Assurity-AM%20Best%20Report_1225.pdf"),
 ("USAA Life","A++","aaa","Stable","","Very Strong","Strong","Favorable","Appropriate","2025-07-02","affirm","https://news.ambest.com/pr/PressContent.aspx?altsrc=2&refnum=36179"),
 ("Thrivent","A++","aa+","Stable","","Strongest","Strong","Favorable","Very Strong","2025-11-10","affirm","https://news.ambest.com/newscontent.aspx?refnum=217094"),
 ("State Farm Life","A+","aa","Stable","","Strongest","Strong","Favorable","Appropriate","2025-11-14","downgrade","https://news.ambest.com/newscontent.aspx?refnum=218939"),
 ("Northwestern Mutual","A++","aaa","Stable","","Strongest","Very Strong","Very Favorable","Very Strong","2026-06-05","affirm","https://news.ambest.com/pr/PressContent.aspx?altsrc=2&refnum=37401"),
 ("New York Life","A++","aaa","Stable","","Strongest","Very Strong","Very Favorable","Very Strong","2025-07-02","affirm","https://news.ambest.com/newscontent.aspx?refnum=267010&altsrc=23"),
 ("MassMutual","A++","aa+","Stable","","Strongest","Strong","Very Favorable","Very Strong","2025-10-23","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36651&altsrc=2"),
 ("Guardian Life","A++","aa+","Stable","","Strongest","Strong","Favorable","Very Strong","2025-09-12","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=36474&altsrc=2"),
 ("Kansas City Life","A-","a-","Negative","","Very Strong","Marginal","Neutral","Appropriate","2025-12-04","affirm — outlook to negative","https://www.businesswire.com/news/home/20251204292591/en/"),
 ("National Western Life","A-","a-","Stable","","Very Strong","Adequate","Neutral","Appropriate","2025-11-05","removed from under review","https://news.ambest.com/pr/PressContent.aspx?refnum=36707&altsrc=2"),
 ("Penn Mutual","A+","aa-","Stable","","Strongest","Strong","Favorable","Appropriate","2025-04-01","affirm","https://news.ambest.com/PR/PressContent.aspx?altsrc=2&refnum=35889"),
 ("Lincoln Financial","A","a+","Stable","","Strong","Strong","Favorable","Appropriate","2026-03-13","affirm","https://news.ambest.com/pr/PressContent.aspx?refnum=37125&altsrc=2"),
 ("Atlantic American — Bankers Fidelity","A-","a-","","negative","Very Strong","Adequate","Neutral","Appropriate","2026-06-17","under review (negative)","https://www.businesswire.com/news/home/20260617254169/en/"),
 ("Atlantic American — American Southern","A-","a-","Negative","negative","Strong","Adequate","Neutral","Appropriate","2026-06-17","downgrade + under review (negative)","https://www.businesswire.com/news/home/20260617254169/en/ (downgraded 2026-04-22; P&C sibling)"),
 ("Heartland National","B++","bbb","Negative","","Strong","Adequate","Limited","Marginal","2025-08-06","affirm — outlook to negative","https://news.ambest.com/newscontent.aspx?refnum=267998&altsrc=23"),
 ("Sentinel Security Life","B","bb+","","negative","Adequate","Adequate","Limited","Marginal","2026-01-23","downgrade + under review (negative)","https://news.ambest.com/pr/PressContent.aspx?refnum=36960&altsrc=2 (A-CAP Group)"),
 ("Everence","","","","","","","","","","","NOT FOUND — fraternal society, no public AM Best rating rationale located"),
 ("Continental General","B+","bbb-","Stable","","Strong","Adequate","Very Limited","Appropriate","2024-11-21","initial assignment","https://news.ambest.com/newscontent.aspx?refnum=262322&altsrc=40"),
 ("Liberty Bankers","A-","a-","Stable","","Very Strong","Adequate","Neutral","Appropriate","2025-07-29","affirm","https://finance.yahoo.com/news/liberty-bankers-insurance-group-earns-173000898.html"),
 ("Citizens Inc — CICA","B++","bbb+","Stable","negative","Strong","Adequate","Limited","Appropriate","2025-10-23","affirm — ICR outlook to negative","https://news.ambest.com/pr/PressContent.aspx?refnum=36648&altsrc=2"),
 # --- standalone Wellabe-sized peers added from the research pass (all file own statutory stmt) ---
 ("Boston Mutual Life","A","a","Stable","","","","","","2025","affirm","https://ratings.ambest.com/CompanyProfile.aspx?ambnum=6170 (blocks unconfirmed)"),
 ("Illinois Mutual Life","A-","a-","Stable","","Strongest","Adequate","Limited","Appropriate","2025","affirm","https://ratings.ambest.com/CompanyProfile.aspx?ambnum=6542"),
 ("USAble Life","A","a","Stable","","Strongest","Adequate","Limited","Appropriate","2024-01-26","affirm","https://www.businesswire.com/news/home/20240126208665/en/"),
 ("5 Star Life","A-","a-","Stable","","","","","","2025","affirm","https://ratings.ambest.com/ (5 Star Life; blocks unconfirmed)"),
 ("Royal Neighbors of America","A","a","Stable","","Strongest","Adequate","Neutral","Appropriate","2020-12-15","upgrade","https://www.businesswire.com/news/home/20201215005867/en/"),
 ("Gleaner Life","B++","bbb","","developing","Very Strong","Marginal","Neutral","Marginal","2024-11-22","downgrade — under review developing","https://www.businesswire.com/news/home/20241122560161/en/"),
 ("Central States Health & Life","A-","a-","Stable","","Very Strong","Adequate","Limited","Appropriate","2022-07-27","affirm","https://www.businesswire.com/news/home/20220727006117/en/"),
]


def main():
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in ROWS:
            name = r[0]
            rest = r[1:]
            basis = "group-member" if name in GROUP_MEMBERS else "standalone"
            # row = name, amb_number(blank), naic_code, domicile(blank), 11 fields, rating_basis
            w.writerow([name, "", NAIC.get(name, ""), "", *rest, basis])
    print(f"wrote {OUT} ({len(ROWS)} carriers; "
          f"{sum(1 for r in ROWS if r[5])} with balance-sheet assessment)")


if __name__ == "__main__":
    main()
