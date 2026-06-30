"""Build the AM Best rating paper (.docx) for the ELT capital-appetite session.

Neutral, educational rewrite. Treats capital as one of two live levers (the coming RBC decline
is a real risk to the balance-sheet grade), teaches RBC and BCAR on their own terms, shows where
we sit versus peers, and lays out what realistically moves the rating with real examples.

Voice rules: plain language, no em-dashes, no decorative bolding, no "not X but Y" constructions.
Self-contained: builds its own figures and reads tool/data.json. Reuses the verified notching math.
Output: output/whitepaper/Wellabe_AMBest_Rating.docx
Run: python src/make_rating_paper.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import notching  # noqa: E402

FIG = ROOT / "output" / "whitepaper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "output" / "whitepaper" / "Wellabe_AMBest_Rating.docx"
D = json.load(open(ROOT / "tool" / "data.json"))["carriers"]

ACCENT = "#2E5A88"; INK = "#0B1C2C"; WELL = "#C0392B"; MUTE = "#5C6B78"
TIERCOL = {"Strongest": "#0F5C8C", "Very Strong": "#27A35A", "Strong": "#9AA0A6", "Adequate": "#C97B2B"}
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "axes.edgecolor": "#C9BFA8",
                     "axes.titlesize": 13, "axes.titleweight": "bold", "figure.dpi": 150})

FLOORS = {"Strongest": 530, "Very Strong": 375, "Strong": 275}


def Wc():
    return next(c for c in D if c.get("is_wellabe"))


# ============================================================ figures
def fig_bcar_history():
    yrs = ["2022", "2023", "2024", "2025"]; bcar = [73.4, 73.0, 71.2, 67.3]
    fig, ax = plt.subplots(figsize=(7.0, 3.5), constrained_layout=True)
    ax.bar(yrs, bcar, color=ACCENT, width=0.6, zorder=3)
    for x, v in zip(yrs, bcar):
        ax.text(x, v + 1.6, f"{v:.0f}%", ha="center", fontweight="bold", color=INK)
    ax.annotate("plan takes it\nlower from here", xy=(3.35, 40), xytext=(3.35, 58), color="#8A8A8A",
                fontsize=8.5, ha="center", va="top", arrowprops=dict(arrowstyle="-|>", color="#8A8A8A", lw=1.4))
    ax.axhspan(0, 25, color=WELL, alpha=0.08, zorder=0)
    ax.axhline(25, color=WELL, lw=1.4, ls="--", zorder=2)
    ax.text(3.4, 28, "25% is the line for the top tier", color=WELL, ha="right", fontsize=10)
    ax.set_ylim(0, 88); ax.set_ylabel("BCAR cushion at the 1-in-250 stress (%)")
    ax.set_title("BCAR over the four reviews we have: a wide cushion, drifting down")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "rp_bcar.png"); plt.close(fig)


def fig_rbc_path():
    yrs = [2025, 2026, 2027, 2028, 2029, 2030]
    rbc = [648, 585, 510, 445, 400, 420]   # illustrative path to the ~400% plan trough around 2029
    fig, ax = plt.subplots(figsize=(7.0, 3.8), constrained_layout=True)
    ax.axhspan(FLOORS["Strongest"], 720, color=TIERCOL["Strongest"], alpha=0.10)
    ax.axhspan(FLOORS["Very Strong"], FLOORS["Strongest"], color=TIERCOL["Very Strong"], alpha=0.10)
    ax.axhspan(FLOORS["Strong"], FLOORS["Very Strong"], color=TIERCOL["Strong"], alpha=0.12)
    for name, y in FLOORS.items():
        ax.axhline(y, color="#9AA0A6", ls=":", lw=1)
        ax.text(2030.2, y, f"  {name} floor ~{y}%", va="center", fontsize=8.5, color=MUTE)
    ax.plot(yrs, rbc, color=ACCENT, lw=2.2, marker="o", ms=5, zorder=4)
    ax.scatter([2025], [648], color=WELL, s=90, zorder=5)
    ax.annotate("today ~648%, Strongest", (2025, 648), xytext=(4, 8), textcoords="offset points",
                color=WELL, fontweight="bold", fontsize=9)
    ax.annotate("plan trough ~400%,\nin the Very Strong band", (2029, 400), xytext=(-2, -36),
                textcoords="offset points", color=INK, fontsize=9, ha="center")
    ax.set_ylim(250, 720); ax.set_xlim(2024.8, 2031.5)
    ax.set_ylabel("NAIC RBC ratio, CAL basis (%)")
    ax.set_title("Where the plan takes our RBC ratio (illustrative)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "rp_rbcpath.png"); plt.close(fig)


def _box_by_tier(ax, groups, key, gkey, log=False):
    for c in D:
        c["_g"] = c.get(gkey)
    data = [[c[key] for c in D if c.get("_g") == g and c.get(key) is not None] for g in groups]
    pos = list(range(len(groups)))
    bp = ax.boxplot(data, positions=pos, orientation="horizontal", widths=0.55, patch_artist=True,
                    showfliers=False, medianprops=dict(color=INK, lw=1.6),
                    whiskerprops=dict(color="#8A8A8A"), capprops=dict(color="#8A8A8A"))
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(TIERCOL.get(g, "#9AA0A6")); patch.set_alpha(0.35); patch.set_edgecolor("#8A8A8A")
    for i, ys in enumerate(data):
        ax.scatter(ys, [i] * len(ys), color=TIERCOL.get(groups[i], "#9AA0A6"), s=18, alpha=0.55,
                   zorder=3, edgecolor="white", lw=.4)
    ax.set_yticks(pos); ax.set_yticklabels(groups)
    if log:
        ax.set_xscale("log")
    return data


def fig_cap_tiers():
    order = ["Strongest", "Very Strong", "Strong", "Adequate"]
    fig, ax = plt.subplots(figsize=(7.0, 3.6), constrained_layout=True)
    _box_by_tier(ax, order, "rbc_cal_pct", "bs_assessment", log=True)
    w = Wc()
    ax.scatter([w["rbc_cal_pct"]], [0], marker="D", s=160, color=WELL, edgecolor=INK, lw=1.4, zorder=6)
    ax.annotate("Wellabe, ~648%", (w["rbc_cal_pct"], 0), xytext=(6, 15), textcoords="offset points",
                color=WELL, fontweight="bold", fontsize=9.5)
    ax.set_xticks([200, 300, 500, 1000, 2000]); ax.set_xticklabels(["200", "300", "500", "1,000", "2,000"])
    ax.set_xlabel("NAIC RBC ratio, CAL basis (%)")
    ax.set_title("Capital by balance-sheet tier across peers")
    ax.invert_yaxis(); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "rp_captiers.png"); plt.close(fig)


def fig_earn_tiers():
    order = ["Strong", "Adequate", "Marginal"]
    fig, ax = plt.subplots(figsize=(7.0, 3.6), constrained_layout=True)
    _box_by_tier(ax, order, "roe_5yr_mean", "op_assessment")
    w = Wc()
    ax.scatter([w["roe_5yr_mean"]], [1], marker="D", s=160, color=WELL, edgecolor=INK, lw=1.4, zorder=6)
    ax.annotate("Wellabe: losing money, held at Adequate", (w["roe_5yr_mean"], 1),
                xytext=(8, -30), textcoords="offset points", color=WELL, fontweight="bold", fontsize=9.5)
    for nm, lab in [("Pekin Life", "Pekin (A-)"), ("Government Personnel Mutual", "GPM (B++)")]:
        c = next((x for x in D if x["rating_unit_name"] == nm), None)
        if c and c.get("roe_5yr_mean") is not None:
            ax.annotate(lab, (c["roe_5yr_mean"], 2), xytext=(0, 10), textcoords="offset points",
                        ha="center", fontsize=9, color="#7A2418")
    ax.axvline(0, color="#C9BFA8", lw=1)
    ax.set_xlabel("Five-year average return on equity (%)")
    ax.set_title("Operating performance by tier across peers")
    ax.invert_yaxis(); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG / "rp_earntiers.png"); plt.close(fig)


def fig_ladder():
    fsr = ["A", "A-", "B++"]; xi = {f: i for i, f in enumerate(fsr)}
    rows = [
        ("Today", "A", ACCENT, "Strongest capital, Adequate operating"),
        ("Capital slips one tier (RBC near the trough)", "A-", "#27A35A", "one letter, like Globe Life or American Southern"),
        ("Operating slips to Marginal", "A-", "#27A35A", "one letter, the Strongest grade holds it"),
        ("Both slip together", "B++", WELL, "the real tail, like GPM today"),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.5), constrained_layout=True)
    for i, (lab, f, col, note) in enumerate(rows):
        ax.barh(i, xi[f] + 0.5, color=col, alpha=.85, zorder=3, height=0.6)
        ax.text(xi[f] + 0.58, i, f, va="center", fontweight="bold", color=INK, fontsize=12)
        ax.text(xi[f] + 0.95, i, note, va="center", color=MUTE, fontsize=8.5)
        ax.text(-0.08, i, lab, va="center", ha="right", fontsize=9.5)
    ax.set_xlim(0, 5.4); ax.set_yticks([]); ax.invert_yaxis()
    ax.set_xticks(range(len(fsr))); ax.set_xticklabels(fsr)
    ax.set_title("How far we could fall, and what each step takes")
    ax.set_xlabel("Financial strength rating")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    fig.savefig(FIG / "rp_ladder.png"); plt.close(fig)


def fig_msstress():
    fig = plt.figure(figsize=(8.4, 2.7))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.5, 0.91, "How Med Supp concentration would actually move us: through earnings",
            ha="center", fontsize=12.5, fontweight="bold", color=INK)
    chain = [(0.13, "#FBE9E7", WELL, "Concentrated\nMed Supp book"),
             (0.38, "#FBE9E7", WELL, "Shock: rate,\nreg, or competitor"),
             (0.63, "#EEF2F6", ACCENT, "Loss-ratio\nvolatility"),
             (0.88, "#EEF2F6", ACCENT, "Operating slips,\nrating to A-")]
    bw, bh, by = 0.205, 0.23, 0.50
    for i, (x, fc, ec, txt) in enumerate(chain):
        ax.add_patch(plt.Rectangle((x - bw / 2, by), bw, bh, fc=fc, ec=ec, lw=1.3))
        ax.text(x, by + bh / 2, txt, ha="center", va="center", fontsize=8.7, color=ec, fontweight="bold")
        if i < len(chain) - 1:
            ax.annotate("", xy=(chain[i + 1][0] - bw / 2 - 0.004, by + bh / 2),
                        xytext=(x + bw / 2 + 0.004, by + bh / 2),
                        arrowprops=dict(arrowstyle="-|>", color="#8A8A8A", lw=1.7))
    ax.text(0.5, 0.34, "Franchise grade holds at Neutral. Capital is touched only indirectly, through weaker earnings.",
            ha="center", fontsize=8.6, color=MUTE, style="italic")
    ax.text(0.5, 0.18, "Same shape as Pekin: a concentrated book, a shock, then a Negative outlook from earnings, not a franchise cut.",
            ha="center", fontsize=8.6, color=MUTE, style="italic")
    fig.savefig(FIG / "rp_msstress.png", dpi=150); plt.close(fig)


# ============================================================ docx helpers
def _cell_bg(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), hexc)
    tcPr.append(shd)


def part(doc, text):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = True; r.font.size = Pt(12.5)
    r.font.color.rgb = RGBColor.from_string(INK.lstrip("#"))
    p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(2)


def H(doc, text, before=12):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = True; r.font.size = Pt(13.5)
    r.font.color.rgb = RGBColor.from_string(ACCENT.lstrip("#"))
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(2)


def body(doc, text, size=10.5):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(6); return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet"); r = p.add_run(text); r.font.size = Pt(10.5); return p


def img(doc, name, caption):
    doc.add_picture(str(FIG / name), width=Inches(6.1))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = doc.add_paragraph(); r = c.add_run(caption); r.italic = True; r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string(MUTE.lstrip("#"))
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(10)


def table(doc, headers, rows, highlight=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    try:
        t.style = "Light Grid Accent 1"
    except Exception:
        pass
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string("FFFFFF"); _cell_bg(c, ACCENT.lstrip("#"))
    for row in rows:
        cells = t.add_row().cells
        hot = highlight and row[0] == highlight
        for j, val in enumerate(row):
            cells[j].text = ""
            r = cells[j].paragraphs[0].add_run(str(val)); r.font.size = Pt(9)
            if hot:
                r.bold = True; r.font.color.rgb = RGBColor.from_string(WELL.lstrip("#"))
                _cell_bg(cells[j], "FBE9E7")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ============================================================ peer table
CURATED = [
    "Guardian Life", "Physicians Mutual", "Mutual of Omaha", "Aflac",
    "Guarantee Trust Life", "National Guardian Life", "CNO — Bankers Life", "American National",
    "Globe Life", "American-Amicable / Trinity", "Wellabe Group",
    "National Western Life", "Assurity Life", "Pekin Life", "Funeral Directors Life",
    "Homesteaders Life", "Atlantic American — American Southern",
    "ManhattanLife — Assurance", "Government Personnel Mutual", "Investors Heritage",
    "ManhattanLife — Western United", "Continental General", "Sentinel Security Life",
]
FSR_ORDER = ["A++", "A+", "A", "A-", "B++", "B+", "B", "B-"]


def peer_rows():
    by = {c["rating_unit_name"]: c for c in D}
    out = []
    for nm in CURATED:
        c = by.get(nm)
        if not c:
            continue
        rbc = c.get("rbc_cal_pct")
        out.append([nm.replace("Wellabe Group", "Wellabe").replace(" — ", ", "),
                    c.get("fsr") or "n/a", c.get("bs_assessment") or "n/a",
                    c.get("op_assessment") or "n/a", c.get("bp_assessment") or "n/a",
                    c.get("erm_assessment") or "n/a",
                    f"{round(rbc):,}%" if rbc else "n/a"])
    out.sort(key=lambda r: (FSR_ORDER.index(r[1]) if r[1] in FSR_ORDER else 99,
                            -float(r[6].replace(",", "").rstrip("%")) if r[6] != "n/a" else 0))
    return out


# ============================================================ build
def build():
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(10.5)

    t = doc.add_paragraph(); r = t.add_run("Our AM Best Rating: How It Works, Where We Stand, and What Could Move It")
    r.bold = True; r.font.size = Pt(18); r.font.color.rgb = RGBColor.from_string(INK.lstrip("#"))
    s = doc.add_paragraph(); rs = s.add_run("Office of the Chief Actuary. ELT, internal and confidential.")
    rs.italic = True; rs.font.size = Pt(10); rs.font.color.rgb = RGBColor.from_string(MUTE.lstrip("#"))

    H(doc, "What this paper is for", before=10)
    body(doc, "One of the key components of our company-wide risk appetite is to maintain an AM Best rating of A- or "
              "better. The purpose here is to explain how our AM Best rating actually works, where we stand, and what "
              "would realistically move it, so we can talk about it from a shared and accurate footing. It is written "
              "to teach the mechanics rather than to argue a point of view. Two ideas tend to get tangled in these "
              "conversations, the regulator's capital ratio and Best's own capital model, and most of the confusion "
              "clears up once we keep them straight.")
    body(doc, "One thing to understand at the start, because the rest of the paper depends on it. Our plan draws our "
              "capital down over the next few years. The RBC ratio falls from around 648% as of 12/31/25 toward a "
              "trough near 400% around 2029 before it rebuilds, a trough that already assumes the planned surplus note "
              "and a C-3 Phase I reserve change. That decline is real, it is deliberate, and it is large enough that "
              "it could pressure our balance-sheet grade. So capital is not a settled strength we can set aside. It is "
              "one of the things that can move our rating, and it deserves a clear-eyed look.")

    # ---------- PART I
    part(doc, "Part I.  How the rating works")

    H(doc, "1.  What the rating is, and where it matters to us")
    body(doc, "The financial strength rating is AM Best's opinion of our ability to pay claims. It is a business "
              "asset, and it is worth being honest about where it helps us and where it matters less. We sell mostly "
              "through independent marketing organizations, independent agents, and preneed funeral homes. We do not "
              "sell through banks or broker-dealers, and we do not write the kind of long-duration annuity business "
              "where buyers screen hard on a minimum letter.")
    body(doc, "Because of that, the rating matters to us in specific places. It matters in preneed, where funeral-home "
              "programs place obligations that run for decades and prefer strong, stable carriers. It matters in "
              "reinsurance, where our counterparties price our rating into the business we assume and cede. It matters "
              "when we raise capital, including the surplus note we are working toward, where the rating affects "
              "whether we can place it and at what cost. In our agent Medicare Supplement and supplemental-health "
              "channels it matters less, because the product is standardized and backed by state guaranty funds, so "
              "agents place business on price, commission, and service more than on the letter.")

    H(doc, "2.  How AM Best builds the letter")
    body(doc, "The rating runs off published tables, so we can read our own rating and a competitor's the same way. "
              "The balance sheet sets a starting point, and the other three pieces move it up or down.")
    body(doc, "Step one. The balance-sheet grade sets a starting credit rating:")
    table(doc, ["Balance-sheet grade", "Starting point (ICR)", "Letter it implies"],
          [["Strongest", "a+ / a", "A"], ["Very Strong", "a / a-", "A / A-"],
           ["Strong", "a- / bbb+", "A- / B++"], ["Adequate", "bbb+ / bbb / bbb-", "B++ / B+"]],
          highlight="Strongest")
    body(doc, "Step two. Each of the other three pieces adds or removes notches:")
    table(doc, ["Building block", "How far it can move us", "Neutral, no-change grade"],
          [["Operating performance (earnings)", "up 2, down 3", "Adequate"],
           ["Business profile (franchise)", "up 2, down 2", "Neutral"],
           ["Risk management", "up 1, down 4", "Appropriate"]])
    body(doc, "Two things are worth noticing. The downside on each piece is larger than the upside, so it is easier "
              "to lose ground than to gain it. And the balance sheet only gets a carrier to the starting line. A "
              "company can open at A on capital and still finish lower if its operating performance and business profile are weak. As a "
              "worked example, a Strongest balance sheet opens at A. Hold the other three at no change and the carrier "
              "stays at A. Let two of them each slip a notch and the same well-capitalized company lands at B++.")

    H(doc, "3.  The two capital yardsticks: RBC and BCAR")
    body(doc, "This is the part most worth slowing down on, because two different measures get used for two different "
              "jobs, and they do not always agree.")
    body(doc, "The first is NAIC risk-based capital, which we report on the CAL basis and which runs around 648% for "
              "us today. The formula sets a regulatory floor. It compares our total adjusted capital to a control "
              "level the regulator calculates. The ladder below shows what happens as the ratio falls. The useful "
              "thing to understand is what this number is for. It is a floor and an early-warning gauge. Once a "
              "company is well above the floor it tells you the regulator is comfortable, and very little more. It "
              "does not rank healthy carriers against each other, and it is not the number AM Best uses to set a "
              "rating. Globe Life makes the point: it runs an RBC ratio around 316%, less than half of ours, and it "
              "is rated A, the same letter we hold.")
    table(doc, ["Regulatory level (CAL basis)", "Ratio", "What happens"],
          [["Company Action Level", "below 100%", "File a corrective plan"],
           ["Regulatory Action Level", "below 75%", "Regulator prescribes action"],
           ["Authorized Control Level", "below 50%", "Regulator may take control"],
           ["Mandatory Control Level", "below 35%", "Regulator must take control"]])
    body(doc, "The second measure is the one that actually drives the balance-sheet grade, and it is Best's own "
              "capital model, called BCAR. Best takes our real balance sheet and runs it through a series of bad "
              "years, up to roughly a 1-in-250-year loss, and asks how much capital is still standing afterward. A "
              "company graded Strongest has more than about 25% of its capital still to spare after that stress. BCAR "
              "captures things the RBC ratio does not, including asset risk, reserve adequacy, and catastrophe "
              "exposure, which is why a carrier can look strong on one measure and less so on the other. One more "
              "point that matters later: BCAR is a snapshot of today's balance sheet under stress. It is not a "
              "forecast. What looks ahead is Best's rating opinion and outlook, which carry its view of where we are "
              "headed.")
    body(doc, "So we hold two capital numbers in mind. The RBC ratio is the regulator's floor and the number our plan "
              "moves the most. BCAR is Best's stress test and the number that sets our grade. They can move together "
              "or apart, and the gap between them is the heart of the capital question for us.")

    # ---------- PART II
    part(doc, "Part II.  Where Wellabe stands")

    H(doc, "4.  Our rating today, and how we got to A")
    body(doc, "Best grades us Strongest on the balance sheet, Adequate on operating performance, Neutral on business "
              "profile, and Appropriate on risk management. The balance sheet opens us at A, the other three net to no "
              "change, and we land at A with a Stable outlook.")
    body(doc, "The thing shaping everything else is our recent operating performance. We have run losses for three "
              "straight years, and the losses have grown each year. Our accident-and-health combined ratio climbed "
              "every year through 2025, and surplus has come down since 2021.")
    table(doc, ["Year", "Net income", "Capital and surplus", "A&H combined ratio", "BCAR"],
          [["2021", "+$22M", "$630M", "95%", "n/a"], ["2022", "-$1M", "$615M", "99%", "73.4%"],
           ["2023", "-$21M", "$602M", "103%", "73.0%"], ["2024", "-$52M", "$560M", "109%", "71.2%"],
           ["2025", "-$71M", "$531M", "116%", "67.3%"]])
    body(doc, "We are still A and still Stable while running the largest losses in our history. The reason is that "
              "Best does not read these as ordinary losses. Statutory accounting makes us book the full cost of "
              "writing a new policy right away, so a record year of Medicare Supplement sales, with premium up 13% in "
              "2025, shows up as a loss today on business we expect to earn back over its life. Best is giving us "
              "credit for that, and it has said so in its rating drivers. It is a judgement, and judgements can "
              "change, which is why the next sections matter.")
    body(doc, "There is an early sign the trajectory is turning. Through 2026 to date the all-in accident-and-health "
              "combined ratio is running near 113%, down from 116% in 2025, which would be the first improvement in "
              "the series. If that holds, it is the clearest evidence we can put in front of Best at the next review "
              "that the combined ratio has passed its inflection point and the plan is playing out.")

    H(doc, "5.  Our capital, and where the plan takes it")
    body(doc, "Here is the core of the capital question. Both of our capital measures are coming down, and the plan "
              "intends them to continue down through about 2029.")
    body(doc, "BCAR has fallen from 73.4% at year-end 2022 to 67.3% at year-end 2025, a little over six points in "
              "three years, as losses draw down surplus. It is still far above the 25% line for Strongest, but the "
              "direction is steady and it will keep going while we fund growth, and likely faster than the recent "
              "pace once the surplus note adds lower-quality capital and losses continue.")
    img(doc, "rp_bcar.png", "Figure 1. BCAR over the four annual reviews we have. It sits well above the 25% bar but has trended down each year, and the plan takes it lower.")
    body(doc, "The RBC ratio moves more. It runs about 648% today and the plan carries it toward a trough near 400% "
              "around 2029 before it rebuilds. That matters because of where 400% sits. In our peer data, carriers "
              "graded Strongest tend to sit above roughly 530% on this basis, with the Very Strong band running from "
              "about 375% to 530%. A 400% ratio sits inside the Very Strong band, not the Strongest one.")
    img(doc, "rp_rbcpath.png", "Figure 2. An illustrative path for our RBC ratio to the planned trough. At ~400% it sits in the Very Strong band on the peer-floor read, below the Strongest floor. The exact path will depend on results and capital actions.")
    body(doc, "So the real question is straightforward. Does our balance-sheet grade stay Strongest through the "
              "trough, or does it slip to Very Strong. The evidence cuts both ways, and we should hold both halves. "
              "On one side, the RBC ratio at the trough lands in Very Strong territory on the peer read, which argues "
              "for a lower grade. On the other side, Best itself has said in its rating drivers that it expects us to "
              "maintain the Strongest assessment, and BCAR, the measure that drives the grade, has much more room "
              "than the RBC ratio suggests, so it may still compute Strongest at a 400% RBC level. It is also worth "
              "remembering that BCAR alone does not set the balance-sheet grade. Best weighs asset quality, reserve "
              "adequacy, financial flexibility, and the holding-company structure alongside it, so the grade is a "
              "broader judgement than any single capital number. We will not know where it lands until Best re-runs "
              "the analysis each year on our actual balance sheet. The prudent planning assumption is that a slip "
              "from Strongest to Very Strong is a real possibility at the trough, more so if asset risk keeps "
              "drifting up at the same time, which is a balance-sheet-quality factor Best watches and worth "
              "confirming against the current report.")

    H(doc, "6.  How we compare to peers")
    body(doc, "Reading the same four grades across the competitive set shows where the letters really come from. The "
              "table is sorted by rating, then by capital. The capital column and the rating do not move together.")
    table(doc, ["Carrier", "Rating", "Balance sheet", "Operating", "Business profile", "ERM", "RBC (CAL)"],
          peer_rows(), highlight="Wellabe")
    body(doc, "Two patterns stand out. First, capital does not sort the ratings. Globe Life holds our same A on a "
              "Strong balance sheet and a 316% RBC ratio, carried by its size and business profile. Guarantee Trust "
              "Life holds an A above 800% RBC. ManhattanLife sits at B++ with more reported capital than several A- "
              "carriers. What sorts the ratings is operating performance and business profile. Second, we stand out "
              "in two directions. We do very well on capital, holding one of only a handful of Strongest grades in "
              "the sample and an RBC ratio in the top quartile of the group. And we do poorly on return, with a "
              "five-year return on equity near the bottom of the whole group, held at Adequate where most A-rated "
              "peers are graded Strong. The typical A-rated carrier is the reverse of us, a Very Strong balance sheet "
              "paired with Strong operating performance. We have held our A with capital and a plan Best believes "
              "where others hold it with profits.")
    img(doc, "rp_captiers.png", "Figure 3. Capital by balance-sheet tier across peers. We sit high today, which is the cushion the plan now spends down.")
    body(doc, "That comparison is also the warning. The block we are about to draw down, capital, is the one we lean "
              "on hardest, and the operating-performance block we would fall back on is our weakest. We do not have a "
              "clean twin in the peer set. The carriers that share our soft-block grades and cluster at A- and B++ "
              "are mostly pure preneed groups without our Medicare Supplement diversification, such as National "
              "Guardian, Funeral Directors, and Homesteaders, or carriers smaller than us, such as ManhattanLife and "
              "Government Personnel Mutual. We are a relatively unusual mix: a multi-line senior-market carrier with "
              "Medicare Supplement as the core line, at a scale most of those specialists do not have.")

    # ---------- PART III
    part(doc, "Part III.  What realistically moves us")

    body(doc, "Of the four blocks, two can realistically move us: the balance sheet and operating performance. The "
              "other two, business profile and risk management, are slow to change and unlikely to move us in either "
              "direction. We take each in turn.")

    H(doc, "7.  Lever one: the balance sheet")
    body(doc, "If the RBC and BCAR decline costs us the Strongest grade, the math is clean. Strongest opens us at A. "
              "A grade of Very Strong, one tier down, opens at A-. A grade of Strong, two tiers down, also opens at "
              "A- on its strong end. So a slip in the balance-sheet grade, by one tier or two, most likely costs us "
              "one letter, from A to A-, as long as business profile stays Neutral and operating performance stays "
              "at Adequate.")
    body(doc, "Real carriers show A- is survivable on a weaker balance sheet. Globe Life runs a Strong balance sheet "
              "and holds an A on the strength of its business profile. American Southern, in the Atlantic American "
              "group, runs a Strong balance sheet at about 213% RBC, well below where our trough lands, with the "
              "same Neutral business profile we hold, and Best rates it A-. A weaker balance sheet does not, by "
              "itself, take a carrier below A-. To fall below A- on capital alone, the balance sheet would have to "
              "drop all the way to Adequate, which is far from where our plan goes.")

    H(doc, "8.  Lever two: operating performance")
    body(doc, "The second lever is operating performance, and Best is holding us at Adequate on a forecast: losses "
              "that crest and then ease as the Medicare Supplement block matures. As long as results track that "
              "forecast we stay at Adequate. If losses run well past it, the grade slips toward Marginal, and on its "
              "own that also costs us one letter, from A to A-, because our Strongest balance sheet cushions it.")
    img(doc, "rp_earntiers.png", "Figure 4. Operating performance by tier (five-year ROE). We run losses yet are held at Adequate, a judgement about the plan rather than this year's number.")
    body(doc, "Government Personnel Mutual shows what a Marginal grade looks like from a lower starting point. It runs "
              "a Very Strong balance sheet with Marginal operating performance and is rated B++. Pekin has the very "
              "same grades and holds A-, because the committee gave it a one-notch lift. Same labels, different "
              "letters, which is a reminder that within each grade there is a range and the committee places carriers "
              "inside it.")
    body(doc, "Two features make this lever easier to live with. We usually get warning, because a downgrade from A "
              "is almost always preceded by a move from Stable to a Negative outlook, which tends to give a year or "
              "more of lead time, and our outlook is Stable today. And the move is reversible, because the grade "
              "follows a trend, so a return to profit can win the letter back. The single number to watch is the "
              "combined ratio. It reached 116% in 2025 and is running near 113% in 2026 to date, which would be the "
              "first improvement in the series and the clearest sign that the turn Best is counting on has begun.")

    H(doc, "9.  Lever three: business profile")
    body(doc, "Business profile is Best's read of our franchise: scale, market position, product and geographic "
              "diversification, distribution, and pricing. Best grades us Neutral, and it is the slowest of the four "
              "blocks to change. We earn Neutral on genuine breadth. We are multi-line across the senior market, "
              "with Medicare Supplement, preneed, ancillary health, and life, across more than 40 states and several "
              "distribution channels, which sits above the single-line specialists in the peer set, many of whom are "
              "graded Limited. Moving up to Favorable would take a real step change, either much greater scale or a "
              "genuine expansion beyond the senior market. Adding another senior-market line helps earnings and helps "
              "hold Neutral, but it does not lift the grade. The realistic expectation is that business profile stays "
              "Neutral, so it neither moves us up nor, on its own, moves us down.")
    body(doc, "One question comes up often enough to address directly: does our Medicare Supplement state "
              "concentration threaten this grade. The honest answer is that it mostly does not. Best's business "
              "profile is driven by scale, position, and breadth, and geographic concentration rarely lowers a "
              "diversified carrier's grade on its own. HCSC writes Medicare Supplement in only a handful of states "
              "and is graded Favorable on the scale of its overall health franchise. Pekin Life is multi-line with "
              "Medicare Supplement in its book and operates in 22 states but heavily concentrated in Illinois, and it "
              "holds Neutral like us. Where our concentration would actually bite is operating performance: a "
              "regulatory, rate, or competitive shock to our top Medicare Supplement states would raise loss ratios "
              "and delay the turn the rating depends on. So the concentration is a reason the operating lever could "
              "slip more sharply, not a reason the business-profile grade would fall.")
    img(doc, "rp_msstress.png", "Figure 5. A shock to our concentrated Medicare Supplement book would move us through operating performance, the block already in play, rather than through the business-profile grade.")
    body(doc, "Pekin is the real-world template. Its concentration risk is Midwest property catastrophe, a different "
              "peril, but the shape is identical: a concentrated book, a shock in the form of severe storms, and a "
              "move to a Negative outlook in 2024 driven by earnings, since restored to Stable. The concentration "
              "acted through operating performance and the outlook, not through a business-profile downgrade.")

    H(doc, "10.  Lever four: risk management")
    body(doc, "Risk management is graded Appropriate, and it is effectively a fixed block for us. The grade rarely "
              "moves a rating, and the upside is essentially unavailable. In our sample of roughly 48 carriers, only "
              "three earned a grade above Appropriate, Aflac, Guardian, and New York Life, all far larger and more "
              "complex than we are. For a carrier of our size and profile the realistic outcome is Appropriate, with "
              "no notch up and, absent a real failure, no notch down.")
    body(doc, "So risk management will not lift us and is unlikely to move us. The risk on this side is not the grade "
              "itself. It is letting a preventable problem, a bad reinsurance treaty, a reserve that proves short, an "
              "investment that goes wrong, grow into something that shows up in capital or operating performance, "
              "which are the blocks Best actually downgrades. The grade is the label on how well we avoid that. The "
              "job is to keep it Appropriate and to execute.")

    H(doc, "11.  The two levers that move us, together")
    body(doc, "That leaves the two blocks that can move us, capital and operating performance. Each on its own costs "
              "one letter, to A-. Both together cost two, to B++. The math is direct: a Very Strong balance sheet "
              "with Marginal operating performance opens at bbb+, which is B++. That is exactly GPM today.")
    img(doc, "rp_ladder.png", "Figure 6. Each lever on its own costs one letter. B++ takes both at the same time.")
    body(doc, "The two are stressed in the same window. The plan draws capital to its trough around 2029, which is "
              "also when the operating turn is most under test, before Medicare Supplement operating performance is "
              "projected to turn positive in 2029. We also start from the bottom of Adequate on operating "
              "performance, so that block has little room to absorb a capital slip at the same time. The warning "
              "signs and the reversibility still apply, so this is a scenario to plan around rather than a base case. "
              "The table below is our own rough judgement for discussion, not model output.")
    table(doc, ["Path", "Rough odds", "What it looks like"],
          [["Plan holds", "about 50%", "Capital and operating performance track the plan, we stay A and Stable through 2030."],
           ["A scare, no downgrade", "about 25%", "Outlook goes Negative around 2028 or 2029, then back to Stable as operating performance turns and capital rebuilds."],
           ["A one-letter dip to A-", "about 20%", "The balance-sheet grade slips at the trough, or the operating turn comes late. Recoverable as results improve."],
           ["Below A- to B++", "about 5%", "Capital and operating performance slip together near the trough. The tail this paper is about."]])

    H(doc, "12.  What we watch, and what is in our control")
    bullet(doc, "The BCAR trajectory, because BCAR, not the RBC ratio, is the main input to the balance-sheet grade. The 2026 Best report will be especially telling: it will carry substantial losses and the new surplus note, which is lower-quality capital, so it gives us the first real read on what the trough does to BCAR and to the overall balance-sheet grade.")
    bullet(doc, "The combined ratio, the clearest sign of whether the operating turn is arriving. The move from 116% in 2025 toward 113% in 2026 is the first evidence we can show Best that the turn has begun.")
    bullet(doc, "Whether Best still believes the plan. Best's judgement that our growth turns to profit is what holds operating performance at Adequate today. That judgement is doing real work, and the more our results visibly track the plan we showed them, the more likely Best keeps it and the rating.")
    bullet(doc, "Capital actions and their effect on the grade. The surplus note raises capital and helps both the RBC ratio and BCAR, and Best treats access to it as financial flexibility. The trade-off is that it is slightly lower-quality capital than retained earnings and carries interest, a small offset on quality. We also have no debt outstanding, FHLB Des Moines capacity, and reinsurance options, all of which Best already counts toward the balance sheet.")
    bullet(doc, "The outlook, our earliest warning. A move from Stable to Negative is the signal that Best's view is shifting, and we would treat it as the point to act and to bring it to the board.")

    # ---------- summary
    part(doc, "Summary")
    body(doc, "The rating is built from four blocks, and capital sets the floor under the other three. We hold the "
              "top balance-sheet grade today, but our plan draws capital down toward a trough near 400% RBC around "
              "2029, and that decline could pressure the grade. Best has said it expects us to stay Strongest, and "
              "BCAR, the measure that drives the grade, has more room than the RBC ratio shows, so the grade may "
              "hold. Even so, a slip from Strongest to Very Strong is a real possibility we should plan around.")
    body(doc, "Two of the four blocks can realistically move us, capital and operating performance. Each on its own "
              "costs one letter, to A-. A balance-sheet slip lands us at A-, which is survivable on a weaker balance "
              "sheet, as Globe Life and American Southern show. An operating slip lands us at A- as well, and that "
              "move comes with warning and is reversible. The case that reaches B++ is both blocks slipping at once, "
              "and the plan draws capital to its trough in the same window the operating turn is most under test, "
              "with operating performance already at the bottom of Adequate. Business profile stays Neutral and risk "
              "management stays Appropriate, so neither lifts us nor, on its own, moves us down. The things in our "
              "control are showing Best the operating turn through the combined ratio, watching the BCAR trajectory, "
              "managing capital actions, keeping Best's confidence in the plan, and reading the outlook as the early "
              "signal it is.")

    note = doc.add_paragraph(); rn = note.add_run(
        "Sources and method. Wellabe's rating, grades, and financials come from the AM Best Credit Report for "
        "Wellabe Group, AMB #070369, effective May 2026, and prior reports. Peer figures come from a 50-carrier "
        "model built from public AM Best grades and S&P Capital IQ and SNL statutory data. RBC is on the CAL basis. "
        "The RBC and BCAR forward paths and the likelihood ranges are illustrative, drawn from the 2026 strategic "
        "plan and our own judgement for discussion, not AM Best output. Peer-relative figures are sample "
        "approximations, not AM Best's internal composites. Internal and confidential, for ELT use.")
    rn.italic = True; rn.font.size = Pt(8.5); rn.font.color.rgb = RGBColor.from_string("8A8A8A")
    note.paragraph_format.space_before = Pt(14)
    doc.save(OUT)


if __name__ == "__main__":
    fig_bcar_history(); fig_rbc_path(); fig_cap_tiers(); fig_earn_tiers(); fig_ladder(); fig_msstress()
    build()
    print("wrote " + str(OUT.relative_to(ROOT)))
