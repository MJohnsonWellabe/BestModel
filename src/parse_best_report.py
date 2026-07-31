"""Extract structured data from AM Best credit-report PDFs.

AM Best reports are the only source for BCAR (Best's Capital Adequacy Ratio), the proprietary
capital-adequacy score that the S&P-derived financials cannot provide. This module reads each
report PDF and pulls:
  - identity: rating_unit_name, amb_number, effective_date
  - rating: fsr, icr, outlook, action
  - the four building-block assessments (from the Rating Rationale section, which is the
    reliable "Label: Value" form; the header block sometimes interleaves labels and values)
  - BCAR scores at the four VaR confidence levels (95.0 / 99.0 / 99.5 / 99.6) + model label

CLI:
  python src/parse_best_report.py [pdf_dir]     # default: data/best_reports_pdf
It writes data/bcar.csv (committed, report-sourced) + data/best_reports/<stem>.json (cache),
and prints a reconcile table cross-checking each report's rating/blocks against the seed
labels in seed_assessments.ROWS (CONFIRM / MISMATCH / NEW) plus AMB numbers to backfill.

The raw PDFs are licensed and gitignored (data/best_reports_pdf/); only the derived numbers
are committed. Requires pdfminer.six.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from pdfminer.high_level import extract_text

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "best_reports_pdf"
JSON_DIR = ROOT / "data" / "best_reports"
BCAR_CSV = ROOT / "data" / "bcar.csv"
BCAR_SCORES = ROOT / "data" / "bcar_scores.csv"  # the site input (rating_unit_name -> bcar_996)

# Recognized tier vocabularies, longest-first so "Very Strong" wins over "Strong".
# Rating tokens, longest-first so "A++" wins over "A+"/"A" and "aa+" over "aa"/"a".
FSR_TOKENS = ["A++", "A+", "A-", "A", "B++", "B+", "B-", "B", "C++", "C+", "C-", "C", "D"]
ICR_TOKENS = ["aaa", "aa+", "aa-", "aa", "a+", "a-", "a", "bbb+", "bbb-", "bbb",
              "bb+", "bb-", "bb", "b+", "b-", "b", "ccc+", "ccc-", "ccc", "cc", "c"]
FSR_SET, ICR_SET = set(FSR_TOKENS), set(ICR_TOKENS)

BSS_TIERS = ["Strongest", "Very Strong", "Strong", "Adequate", "Weak", "Very Weak"]
OP_TIERS = ["Very Strong", "Strong", "Adequate", "Marginal", "Weak", "Very Weak"]
BP_TIERS = ["Very Favorable", "Favorable", "Neutral", "Very Limited", "Limited"]
ERM_TIERS = ["Very Strong", "Appropriate", "Marginal", "Weak", "Very Weak"]
CONF_LEVELS = ["95.0", "99.0", "99.5", "99.6"]

CSV_COLS = ["seed_name", "rating_unit_name", "amb_number", "effective_date", "fsr", "icr",
            "outlook", "action", "bs_assessment", "op_assessment", "bp_assessment",
            "erm_assessment", "bcar_model", "bcar_95", "bcar_99", "bcar_995", "bcar_996",
            "source_file"]


def _first_tier(text: str, tiers: list[str]) -> str:
    """Return the recognized tier that begins `text` (tiers must be longest-first sorted)."""
    text = text.strip()
    for tier in sorted(tiers, key=len, reverse=True):
        if text.startswith(tier):
            return tier
    return ""


def _assessment(t: str, label: str, tiers: list[str]) -> str:
    """Read a building-block assessment from the 'Label: Value' Rating Rationale heading."""
    m = re.search(re.escape(label) + r":\s*([A-Za-z ]+)", t)
    return _first_tier(m.group(1), tiers) if m else ""


def _bcar(t: str) -> tuple[str, dict]:
    """Return (model_label, {conf: score}) from the BCAR Scores table."""
    i = t.find("Capital Adequacy Ratio (BCAR) Scores")
    scores: dict[str, str] = {}
    model = ""
    if i < 0:
        return model, scores
    region = t[i:i + 900]
    for conf in CONF_LEVELS:
        m = re.search(re.escape(conf) + r"\s*\n\s*(-?\d+(?:\.\d+)?)", region)
        if m:
            scores[conf] = m.group(1)
    mm = re.search(r"Best's Capital Adequacy Ratio Model\s*-\s*([^\n]+)", region)
    if mm:
        model = mm.group(1).strip()
    return model, scores


def parse_report(path: Path) -> dict:
    t = extract_text(str(path)) or ""

    def find(pat: str, flags=0) -> str:
        m = re.search(pat, t, flags)
        return m.group(1).strip() if m else ""

    # Rating letters sit in the header between "(ICR)" and "Balance Sheet Strength". The layout
    # varies a lot (FSR and ICR may be stacked with their descriptors, or listed back-to-back;
    # under-review carriers carry a trailing " u"), but each value always occupies its own line.
    # So scan the header line-by-line and take the first line that IS a rating token.
    start = t.find("(ICR)")
    end = t.find("Balance Sheet Strength")
    header = t[start:end] if (start >= 0 and end > start) else t[:2500]
    fsr = icr = ""
    for raw in header.splitlines():
        line = re.sub(r"\s+u$", "", raw.strip())  # drop the under-review flag
        if not fsr and line in FSR_SET:
            fsr = line
        elif not icr and line in ICR_SET:
            icr = line
        if fsr and icr:
            break
    outlook = find(r"(?:Outlook|Implication):\s*([A-Za-z]+)")
    action = find(r"Action:\s*([A-Za-z ]+?)\s*\n")
    eff = find(r"Best's Credit Rating Effective Date\s*\n\s*([A-Z][a-z]+ \d{1,2}, \d{4})")
    ru_name = find(r"Rating Unit:\s*([^|]+?)\s*\|")
    ru_amb = find(r"Rating Unit:[^|]*\|\s*AMB #:\s*(\d+)")

    model, scores = _bcar(t)
    return {
        "rating_unit_name": ru_name,
        "amb_number": ru_amb,
        "effective_date": eff,
        "fsr": fsr,
        "icr": icr,
        "outlook": outlook,
        "action": action,
        "bs_assessment": _assessment(t, "Balance Sheet Strength", BSS_TIERS),
        "op_assessment": _assessment(t, "Operating Performance", OP_TIERS),
        "bp_assessment": _assessment(t, "Business Profile", BP_TIERS),
        "erm_assessment": _assessment(t, "Enterprise Risk Management", ERM_TIERS),
        "bcar_model": model,
        "bcar_95": scores.get("95.0", ""),
        "bcar_99": scores.get("99.0", ""),
        "bcar_995": scores.get("99.5", ""),
        "bcar_996": scores.get("99.6", ""),
        "source_file": path.name,
    }


# --- Map a report's rating unit to the canonical seed_assessments.ROWS name -----------------
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# Rating-unit names that don't obviously match their seed key.
UNIT_ALIASES = {
    "iaamericanlifegroup": "American-Amicable / Trinity",
    "aetnahealthlifegroup": "Aetna/CVS — American Continental",
    "americannationalgroup": "American National",
    "aflacincorporated": "Aflac",
    "gpmlifegroup": "Government Personnel Mutual",
    "hcscmedicaresuppgroup": "Cigna — American Retirement Life",
}

# Several rating units cover more than one roster row (a group BCAR is shared across its
# members) and several files use abbreviations the rating-unit name can't resolve. The
# analyst's numbered filenames name the specific sub-entity, so match on the filename first.
# Keyed by a substring of the normalized filename (number prefix stripped).
FILE_HINTS = [
    ("continentallife", "Aetna/CVS — Continental Life"),
    ("americancontinental", "Aetna/CVS — American Continental"),
    ("nationalhealth", "Cigna — National Health"),
    ("loyalamerican", "Cigna — Loyal American"),
    ("americanretirement", "Cigna — American Retirement Life"),
    ("standardlife", "American National — Standard Life & Accident"),
    ("westernunited", "ManhattanLife — Western United"),
    ("manhattan", "ManhattanLife — Assurance"),
    ("reservenational", "Kemper — Reserve National"),
    ("bankersfidelity", "Atlantic American — Bankers Fidelity"),
    ("forethought", "Forethought (Global Atlantic)"),
    ("globalatlantic", "Forethought (Global Atlantic)"),
    ("ngl", "National Guardian Life"),
    ("gtl", "Guarantee Trust Life"),
    ("fdlic", "Funeral Directors Life"),
    ("uhc", "UnitedHealthcare"),
    ("gpm", "Government Personnel Mutual"),
    ("wellabe", "Wellabe Group"),
    ("sentinel", "Sentinel Security Life"),          # rating unit is "A-CAP Group"
    ("heartland", "Heartland National"),
    ("investorsheritage", "Investors Heritage"),
    ("philadelphiaamerican", "Philadelphia American"),
    ("newera", "New Era Life"),
    ("homesteaders", "Homesteaders Life"),
    ("naitonalwestern", "National Western Life"),    # filename typo in the source set
    ("nationalwestern", "National Western Life"),
    ("pekin", "Pekin Life"),
    ("globelife", "Globe Life"),
    ("humana", "Humana"),
    ("americo", "Americo"),
    ("assurity", "Assurity Life"),
    ("libertybankers", "Liberty Bankers"),
    ("continentalgeneral", "Continental General"),
    ("physiciansmutual", "Physicians Mutual"),
    ("mutualofomaha", "Mutual of Omaha"),
    ("newyorklife", "New York Life"),
    ("guardianlife", "Guardian Life"),
    ("lincolnfinancial", "Lincoln Financial"),
    ("usaalife", "USAA Life"),
    ("aflac", "Aflac"),
    ("americanamicable", "American-Amicable / Trinity"),
    ("colonialpenn", "CNO — Colonial Penn"),
    ("washingtonnational", "CNO — Washington National"),
    ("bankerslife", "CNO — Bankers Life"),
    ("combinedinsurance", "Combined Insurance (Chubb)"),
]


def match_seed(rating_unit_name: str, seed_names: list[str], source_file: str = "") -> str:
    fkey = _norm(re.sub(r"^\s*\d+\s*-?\s*", "", source_file))  # drop "12 - " prefix
    for token, name in FILE_HINTS:
        if token in fkey and name in seed_names:
            return name
    key = _norm(rating_unit_name)
    if key in UNIT_ALIASES:
        return UNIT_ALIASES[key]
    norm_map = {_norm(n): n for n in seed_names}
    if key in norm_map:
        return norm_map[key]
    # token-overlap fallback: most shared significant tokens
    toks = set(re.findall(r"[a-z0-9]+", rating_unit_name.lower())) - {"group", "life", "the",
                                                                       "insurance", "company", "co"}
    best, best_score = "", 0
    for n in seed_names:
        ntoks = set(re.findall(r"[a-z0-9]+", n.lower()))
        score = len(toks & ntoks)
        if score > best_score:
            best, best_score = n, score
    return best if best_score else ""


def _reconcile(parsed: list[dict]) -> None:
    """Print CONFIRM/MISMATCH/NEW vs the seed labels, and AMB numbers to backfill."""
    sys.path.insert(0, str(ROOT / "src"))
    import seed_assessments as sa
    seed = {r[0]: r for r in sa.ROWS}  # name -> tuple
    # tuple order after name: fsr, icr, outlook, uwr, bs, op, bp, erm, date, action, url
    print(f"\n{'CARRIER (seed match)':<38} {'FSR/ICR':<10} {'BLOCKS (bs/op/bp/erm)':<34} STATUS")
    print("-" * 100)
    for p in parsed:
        name = match_seed(p["rating_unit_name"], list(seed), p["source_file"])
        rep_blocks = (p["bs_assessment"], p["op_assessment"], p["bp_assessment"], p["erm_assessment"])
        rep_rating = f"{p['fsr']}/{p['icr']}"
        blk = "/".join(b or "?" for b in rep_blocks)
        if not name or name not in seed:
            print(f"{(p['rating_unit_name'])[:37]:<38} {rep_rating:<10} {blk[:33]:<34} NEW (no seed)")
            continue
        s = seed[name]
        seed_rating = f"{s[1]}/{s[2]}"
        seed_blocks = (s[5], s[6], s[7], s[8])
        diffs = []
        if rep_rating.lower() != seed_rating.lower():
            diffs.append(f"rating {seed_rating}->{rep_rating}")
        for lbl, rb, sb in zip(("bs", "op", "bp", "erm"), rep_blocks, seed_blocks):
            if rb and sb and rb != sb:
                diffs.append(f"{lbl} {sb}->{rb}")
        status = "CONFIRM" if not diffs else "MISMATCH: " + "; ".join(diffs)
        if not any(seed_blocks) and any(rep_blocks):
            status = "FILL (seed blocks blank)"
        print(f"{name[:37]:<38} {rep_rating:<10} {blk[:33]:<34} {status}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    from_cache = "--from-cache" in sys.argv  # rebuild CSVs from data/best_reports/*.json (fast)
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    if from_cache:
        parsed = [json.loads(p.read_text()) for p in sorted(JSON_DIR.glob("*.json"))]
        if not parsed:
            print(f"No cached JSON in {JSON_DIR}. Run without --from-cache first.")
            return
        print(f"rebuilding from {len(parsed)} cached reports (no PDF re-parse)")
    else:
        pdf_dir = Path(args[0]) if args else PDF_DIR
        pdfs = sorted(pdf_dir.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs in {pdf_dir}. Drop AM Best report PDFs there and re-run.")
            return
        parsed = []
        for pdf in pdfs:
            rec = parse_report(pdf)
            parsed.append(rec)
            (JSON_DIR / (pdf.stem + ".json")).write_text(json.dumps(rec, indent=2))

    sys.path.insert(0, str(ROOT / "src"))
    import seed_assessments as sa
    seed_names = [r[0] for r in sa.ROWS]

    BCAR_CSV.parent.mkdir(parents=True, exist_ok=True)
    scores: dict[str, str] = {}  # seed_name -> bcar_996 (the site input)
    with BCAR_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        for p in sorted(parsed, key=lambda r: r["rating_unit_name"]):
            row = dict(p)
            sn = match_seed(p["rating_unit_name"], seed_names, p["source_file"])
            row["seed_name"] = sn
            w.writerow({k: row.get(k, "") for k in CSV_COLS})
            if sn and p["bcar_996"]:
                scores[sn] = p["bcar_996"]
    have_bcar = sum(1 for p in parsed if p["bcar_996"])
    print(f"wrote {BCAR_CSV.relative_to(ROOT)} ({len(parsed)} reports; {have_bcar} with BCAR)")
    _write_scores(scores, seed_names)
    _reconcile(parsed)


def _write_scores(scores: dict[str, str], seed_names: list[str]) -> None:
    """Fill data/bcar_scores.csv (the site input) in place: preserve existing rows/order/notes,
    write the parsed bcar_996 where we have it, keep any prior value otherwise."""
    rows, seen = [], set()
    if BCAR_SCORES.exists():
        with BCAR_SCORES.open(newline="") as f:
            for r in csv.DictReader(f):
                name = (r.get("rating_unit_name") or "").strip()
                seen.add(name)
                rows.append({"rating_unit_name": name,
                             "bcar_996": scores.get(name, (r.get("bcar_996") or "").strip()),
                             "note": (r.get("note") or "").strip()})
    for name in seed_names:  # ensure every roster carrier has a row
        if name not in seen:
            rows.append({"rating_unit_name": name, "bcar_996": scores.get(name, ""), "note": ""})
            seen.add(name)
    with BCAR_SCORES.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rating_unit_name", "bcar_996", "note"])
        w.writeheader()
        w.writerows(rows)
    filled = sum(1 for r in rows if r["bcar_996"])
    unmatched = sorted(set(scores) - seen)
    print(f"wrote {BCAR_SCORES.relative_to(ROOT)} ({filled}/{len(rows)} carriers with BCAR 99.6)")
    if unmatched:
        print("  WARNING unmatched parsed carriers (not in roster):", unmatched)


if __name__ == "__main__":
    main()
