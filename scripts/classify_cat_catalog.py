from __future__ import annotations

import csv
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "cat_pyq"


def norm(text: str) -> str:
    text = (text or "").lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"\\\(|\\\)|\\\[|\\\]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def short_cue(text: str, max_words: int = 12) -> str:
    words = re.sub(r"\s+", " ", text or "").strip().split()
    cue = " ".join(words[:max_words])
    if len(words) > max_words:
        cue += " ..."
    return cue


def difficulty(correct_pct):
    if correct_pct is None:
        return "Unrated"
    if correct_pct >= 0.55:
        return "Easy"
    if correct_pct >= 0.35:
        return "Moderate"
    return "Difficult"


def qa_topic(question: dict) -> tuple[str, str, bool]:
    title = norm(question.get("title", ""))
    text = norm(question.get("question", ""))
    combined = f"{title} {text}"

    # Specific arithmetic classifications take precedence over broad archive tags.
    if re.search(r"\b(simple|compound) interest\b|\bsi\s*&\s*ci\b|\binterest rate\b|\brate of interest\b", combined):
        return "Arithmetic", "Simple & Compound Interest", False
    if re.search(r"\bprofit\b|\bloss\b|\bdiscount\b|\bmarked price\b|\bselling price\b|\bcost price\b", combined):
        return "Arithmetic", "Profit, Loss & Discount", False
    if re.search(r"\bpercent(age)?\b|%", combined):
        return "Arithmetic", "Percentages", False
    if re.search(r"\bmixture\b|\balligation\b|\bdilut|\bmilk\b.*\bwater\b", combined):
        return "Arithmetic", "Mixtures & Alligation", False
    if re.search(r"\baverage\b|\bmean\b|weighted average", combined):
        return "Arithmetic", "Averages", False
    if re.search(r"\bratio\b|\bproportion\b|\bvariation\b", combined):
        return "Arithmetic", "Ratios, Proportion & Variation", False
    if re.search(r"pipes?\b|cistern|\btank\b.*\bfill|\bleak", combined):
        return "Arithmetic", "Pipes & Cisterns", False
    if re.search(r"\bwork\b.*\bdays?\b|\bjob\b.*\bdays?\b|work[,& ]+time|\bworkers?\b|working together|\bpaint\b.*\bdays?\b", combined):
        return "Arithmetic", "Time & Work", False
    if re.search(r"\brace\b|\btrain\b|\bspeed\b|\bdistance\b|\bjourney\b|\bkm\b|\bboat\b|\bstream\b|\bjogs?\b|\bwalk\b.*\btrack\b", combined):
        return "Arithmetic", "Time, Speed & Distance", False

    if re.search(r"\bprobabil", combined):
        return "Modern Math", "Probability", False
    if re.search(r"permutation|combination|combinatorics|\bways?\b.*(?:arrang|distribut)|\bselect(?:ed|ion)?\b.*\bways?\b|\bgroups? of\b.*\bdistinct\b|non-repeating digits", combined):
        return "Modern Math", "Permutations & Combinations", False
    if re.search(r"\bset theory\b|\bvenn\b", combined):
        return "Modern Math", "Set Theory", False

    if re.search(r"co-?ordinate geometry|coordinate geometry|\bcoordinates?\b|\bx-axis\b|\by-axis\b", combined):
        return "Geometry", "Coordinate Geometry", False
    if re.search(r"mensuration|\bvolume\b|surface area|\bcylinder\b|\bcone\b|\bsphere\b|\bcuboid\b", combined):
        return "Geometry", "Mensuration", False
    if re.search(r"trigonometry|\bsin\b|\bcos\b|\btan\b", combined):
        return "Geometry", "Trigonometry", False
    if re.search(r"\bcircle\b|\bchord\b|\btangent\b|\bdiameter\b|\bradius\b", combined):
        return "Geometry", "Circles", False
    if re.search(r"\btriangle\b|\bquadrilateral\b|\bpolygon\b|\bangle\b|\bgeometry\b|\brectangle\b|\bsquare\b|\btrape|\brhombus\b|\bhexagon\b|\bfencing\b", combined):
        return "Geometry", "Triangles, Quadrilaterals & Polygons", False

    if re.search(r"\bfraction\b|\bdecimal\b|\brational number", combined):
        return "Number System", "Fractions & Decimals", False

    if re.search(r"\bremainder\b|\bmod(?:ulo)?\b", combined):
        return "Number System", "Remainders", False
    if re.search(r"\bhcf\b|\blcm\b|greatest common|least common", combined):
        return "Number System", "HCF & LCM", False
    if re.search(r"\bdigit\b|\bbase\b.*\bnumber", combined):
        return "Number System", "Digits & Number Bases", False
    if re.search(r"\bfactorial\b|!\s*(?:is|=|\))", combined):
        return "Number System", "Factorials", False
    if re.search(r"number theory|\bdivisors?\b|\bfactors?\b|\bprime\b|\bintegers?\b|\bnatural numbers?\b|sum of (?:all )?(?:the )?digits|less than 5000 students", combined):
        return "Number System", "Factors, Divisibility & Integers", False

    if re.search(r"\bfunction\b|f\s*\(|g\s*\(", combined):
        return "Algebra", "Functions", False
    if re.search(r"\bsequence\b|\bseries\b|\bprogression\b|\bnth term\b|\barithmetic progression\b|\bgeometric progression\b|\ba\.p\b|\bg\.p\b|\ba\s*[_ ]?[nk123]\b|\bx\s*[_ ]?n\b", combined):
        return "Algebra", "Sequences & Series", False
    if re.search(r"\blogarithm|\blog\b|\bexponent|\bpowers?\b|\bsurds?\b|\^", combined):
        return "Algebra", "Logarithms, Exponents & Surds", False
    if re.search(r"\bpolynomial\b", combined):
        return "Algebra", "Polynomials", False
    if re.search(r"\binequalit|\bmaximum possible\b|\bminimum possible\b", combined):
        return "Algebra", "Inequalities & Optimization", False
    if re.search(r"\bquadratic\b|\blinear\b|\bequations?\b|\broots?\b|\balgebra\b|\breal numbers?\s+[xy]\b", combined):
        return "Algebra", "Linear & Quadratic Equations", False

    # Broad archive labels that cannot be split reliably without a manual content review.
    if "percents profits sici" in title:
        return "Arithmetic", "Percentages, Profit-Loss & Interest", True
    if "ratios mixtures averages" in title:
        return "Arithmetic", "Ratios, Mixtures & Averages", True
    if "linear quadratic" in title:
        return "Algebra", "Linear & Quadratic Equations", False
    if "logarithms exponents" in title:
        return "Algebra", "Logarithms, Exponents & Surds", False
    if "geometry" in title:
        return "Geometry", "General Geometry", True
    return "Other", "Mixed / Needs Review", True


def varc_topic(question: dict) -> tuple[str, str, bool]:
    text = norm(question.get("question", ""))
    context = norm(question.get("set_context", ""))
    year = int(question.get("year", 0))
    qnum = int(question.get("question_number", 0))

    if re.search(r"four of them can be put together|identify the odd sentence|out of context", text):
        return "Verbal Ability", "Odd Sentence Out", False
    if re.search(r"alternate summaries|best captures the essence|summary of the passage", text):
        return "Verbal Ability", "Para Summary", False
    if re.search(r"sentence that is missing|fit the blank|missing sentence|where would the sentence|would best fit", text):
        return "Verbal Ability", "Para Completion", False
    if re.search(r"jumbled up sentences|properly sequenced|correct sequence|coherent paragraph", text):
        return "Verbal Ability", "Para Jumbles", False

    # The 2017-2019 archive omits the instruction line for VA questions but
    # preserves the original stable block order.
    if year <= 2019 and qnum >= 25:
        if qnum <= 28:
            return "Verbal Ability", "Para Jumbles", False
        if qnum <= 31:
            return "Verbal Ability", "Para Summary", False
        return "Verbal Ability", "Odd Sentence Out", False

    if context or (year <= 2019 and qnum <= 24):
        if re.search(r"technology|software|computer|digital|science|scientific|research|internet|machine", context):
            theme = "RC - Science & Technology"
        elif re.search(r"economy|economic|market|business|trade|company|consumer|finance|capital", context):
            theme = "RC - Business & Economics"
        elif re.search(r"environment|climate|species|animal|ecology|geograph|agriculture|forest", context):
            theme = "RC - Environment & Geography"
        elif re.search(r"history|historical|ancient|colonial|empire|archaeolog", context):
            theme = "RC - History & Culture"
        elif re.search(r"art|literature|author|novel|music|language|poet|film|museum", context):
            theme = "RC - Arts, Literature & Language"
        elif re.search(r"philosoph|ethic|knowledge|truth|morality|epistem|metaphys", context):
            theme = "RC - Philosophy & Ideas"
        elif re.search(r"politic|government|law|legal|democracy|state|policy|rights", context):
            theme = "RC - Politics, Law & Public Policy"
        elif context:
            theme = "RC - Society, Psychology & Other"
        else:
            theme = "RC - General / Theme Review"
        return "Reading Comprehension", theme, not bool(context)

    return "Reading Comprehension", "RC - General / Theme Review", True


def dilr_set_key(question: dict) -> str:
    url = question.get("question_url", "")
    parsed = urllib.parse.urlparse(url)
    if "iim-cat-questions-answers.2iim.com" in parsed.netloc:
        parent = parsed.path.strip("/").split("/")[0]
        return f"{question['year']}-S{question['slot']}-{parent}"
    legacy = re.search(r"dilr-set(\d+)-\d+\.shtml", parsed.path, re.I)
    if legacy:
        return f"{question['year']}-S{question['slot']}-SET{legacy.group(1)}"
    return f"{question['year']}-S{question['slot']}-SET{question.get('set_number', 0)}"


def legacy_set_name(question: dict) -> str:
    context = (question.get("set_context") or "").strip()
    if context:
        return context
    path = urllib.parse.urlparse(question.get("question_url", "")).path.strip("/")
    if path:
        parent = path.split("/")[0]
        parent = re.sub(r"^DILR_CAT-\d{4}-\d+_", "", parent, flags=re.I)
        parent = re.sub(r"[_-]+", " ", parent)
        return parent.strip().title()
    return ""


def dilr_topic(set_questions: list[dict]) -> tuple[str, str, bool]:
    context = " ".join(legacy_set_name(q) for q in set_questions)
    question_text = " ".join(q.get("question", "") for q in set_questions)
    ctext = norm(context)
    qtext = norm(question_text)
    text = f"{ctext} {qtext}"

    # Archive-specific set names provide a more reliable signal than generic
    # words such as "scores" or "teams" in individual question stems.
    named_topics = [
        (r"airlines company|cars travel route|street intersection|schematic map of the metro|walkways|train travels from station|network with three parallel roads", "Logical Reasoning", "Routes & Networks"),
        (r"square layout|chessboard|n x n square matrix|nine boxes|rectangular houses", "Logical Reasoning", "Grid & Matrix Logic"),
        (r"eight friends|round table", "Logical Reasoning", "Circular Arrangements"),
        (r"tea tasting|dance competition", "Logical Reasoning", "Ordering & Ranking"),
        (r"job interview|three doctors|mt & et|security scan|humanities department|schedule of four employees|visa processing", "Logical Reasoning", "Scheduling & Timetables"),
        (r"game show|archery|rifle shooting|tournament|game of quiet|hi-lo", "Logical Reasoning", "Games & Tournaments"),
        (r"team project|dorms|electives|management electives|committees|supermarket|languages spoken", "Logical Reasoning", "Selection, Grouping & Distribution"),
        (r"letter coding|letter codes|three pouches", "Logical Reasoning", "Quant-Based Reasoning"),
        (r"satellites|students & proposals", "Data Interpretation", "Venn Diagrams & Set Data"),
        (r"written test|college accreditation|led tv sales|smartphones|vendor|crimes|rainfall|revenue & cost|rural kids survey|simple happiness index|assets|\bcet\b|petrol pumps|currency exchange", "Data Interpretation", "Tables & Matrix DI"),
        (r"fast food joint|funky pizzeria|products and companies|amusement park tickets|\batm\b|fun sports club", "Data Interpretation", "Caselet & Arithmetic DI"),
    ]
    for pattern, subsection, topic in named_topics:
        if re.search(pattern, ctext):
            return subsection, topic, False

    # Visual DI formats.
    if re.search(r"\bpie chart\b|\bpie-chart\b|pie[_ -]?chart", text):
        return "Data Interpretation", "Pie Charts", False
    if re.search(r"\bbar graph\b|\bbar chart\b|bar[_ -]?(?:graph|chart)", text):
        return "Data Interpretation", "Bar Graphs", False
    if re.search(r"\bline graph\b|\bline chart\b|line[_ -]?(?:graph|chart)", text):
        return "Data Interpretation", "Line Graphs", False
    if re.search(r"\bchart\b|\bgraph\b|\bplot\b|\bfigure\b", ctext):
        return "Data Interpretation", "Charts & Graphs (Type Review)", True
    if re.search(r"\bvenn\b|satellites|\bat least one\b.*\bboth\b", ctext):
        return "Data Interpretation", "Venn Diagrams & Set Data", False
    if re.search(r"\btable\b|tabular|matrix table", ctext):
        return "Data Interpretation", "Tables & Matrix DI", False
    # LR structures.
    if re.search(r"round table|circular|seated around|clockwise|anticlockwise", ctext):
        return "Logical Reasoning", "Circular Arrangements", False
    if re.search(r"\brow\b.*\bseat|linear arrangement|left of|right of|positions? in a line", ctext):
        return "Logical Reasoning", "Linear Arrangements", False
    if re.search(r"schedule|time table|timetable|time slot|appointment|interview|days? of the week|sessions?", ctext):
        return "Logical Reasoning", "Scheduling & Timetables", False
    if re.search(r"tournament|matches|teams?|round robin|league|chess|game|players?", ctext):
        return "Logical Reasoning", "Games & Tournaments", False
    if re.search(r"route|network|cities|flight|roads?|paths?|trains?|airlines", ctext):
        return "Logical Reasoning", "Routes & Networks", False
    if re.search(r"rank|ranking|ordered|ascending|descending|older|younger|taller|shorter", ctext):
        return "Logical Reasoning", "Ordering & Ranking", False
    if re.search(r"truth|lie|always tells|binary|yes/no|true or false", ctext):
        return "Logical Reasoning", "Binary Logic & Truth-Lie", False
    if re.search(r"grid|matrix|chessboard|cells?|rows? and columns?", ctext):
        return "Logical Reasoning", "Grid & Matrix Logic", False
    if re.search(r"group|committee|select|elective|assigned|allocation|distributed|distribution|dorm|rooms?|houses?", ctext):
        return "Logical Reasoning", "Selection, Grouping & Distribution", False

    # Generic data signals are deliberately checked after LR structures.
    if re.search(r"sales|revenue|profit|percentage|average|marks|scores?|survey|population|production|price|income|assets|ratings?", ctext):
        return "Data Interpretation", "Caselet & Arithmetic DI", False

    # Data-heavy sets after structural LR checks.
    if re.search(r"\btable\b|tabular|matrix table", qtext):
        return "Data Interpretation", "Tables & Matrix DI", False
    if re.search(r"sales|revenue|profit|percentage|average|marks|scores?|survey|population|production|price|income|assets|ratings?", qtext):
        return "Data Interpretation", "Caselet & Arithmetic DI", False

    if re.search(r"number|integer|equation|value|calculation", text):
        return "Logical Reasoning", "Quant-Based Reasoning", True
    return "Logical Reasoning", "Other Logic / Needs Review", True


def main():
    raw = json.loads((TMP / "raw_catalog.json").read_text(encoding="utf-8"))
    dilr_groups: dict[str, list[dict]] = defaultdict(list)
    for question in raw:
        if question["section"] == "DILR":
            dilr_groups[dilr_set_key(question)].append(question)

    dilr_labels = {key: dilr_topic(items) for key, items in dilr_groups.items()}
    output = []
    for question in raw:
        section = question["section"]
        review = False
        if section == "Quant":
            subsection, topic, review = qa_topic(question)
        elif section == "VARC":
            subsection, topic, review = varc_topic(question)
        else:
            subsection, topic, review = dilr_labels[dilr_set_key(question)]

        prefix = {"Quant": "QA", "DILR": "DILR", "VARC": "VARC"}[section]
        question_id = f"CAT{question['year']}-S{question['slot']}-{prefix}-Q{question['question_number']:02d}"
        set_label = ""
        if section == "DILR":
            set_label = legacy_set_name(question)
            if len(set_label) > 100:
                set_label = short_cue(set_label, 10)

        row = {
            "question_id": question_id,
            "section": section,
            "subsection": subsection,
            "topic": topic,
            "year": question["year"],
            "slot": question["slot"],
            "question_number": question["question_number"],
            "set_number": question.get("set_number", ""),
            "set_label": set_label,
            "archive_difficulty": difficulty(question.get("correct_pct")),
            "correct_pct": question.get("correct_pct"),
            "question_cue": short_cue(question.get("question", "")),
            "question_url": question.get("question_url", ""),
            "source_page": question.get("source_page", ""),
            "needs_review": review,
        }
        output.append(row)

    output.sort(key=lambda r: (r["section"], r["subsection"], r["topic"], r["year"], r["slot"], r["question_number"]))
    (TMP / "classified_catalog.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = list(output[0].keys())
    with (TMP / "classified_catalog.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    topic_counts = Counter((r["section"], r["subsection"], r["topic"]) for r in output)
    audit = {
        "total": len(output),
        "review_rows": sum(1 for r in output if r["needs_review"]),
        "review_pct": round(sum(1 for r in output if r["needs_review"]) / len(output), 4),
        "topics": [
            {"section": section, "subsection": subsection, "topic": topic, "count": count}
            for (section, subsection, topic), count in sorted(topic_counts.items())
        ],
    }
    (TMP / "classification_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
