from __future__ import annotations

import concurrent.futures
import csv
import html as html_lib
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp" / "cat_pyq"
BASE = "https://online.2iim.com/CAT-question-paper/"


def clean_text(value: str) -> str:
    value = html_lib.unescape(value or "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


class QuestionPageParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.in_ques_ol = False
        self.ques_ol_depth = 0
        self.outer_li_depth = 0
        self.current: dict | None = None
        self.questions: list[dict] = []
        self.current_preamble = ""
        self.capture: str | None = None
        self.capture_parts: list[str] = []
        self.p_direct = False
        self.p_question = False
        self.h4 = False
        self.a_href = ""
        self.span_classes: list[str] = []
        self.tooltip_parts: list[str] = []
        self.set_number = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())

        if tag == "ol" and not self.in_ques_ol and "ques" in classes:
            self.in_ques_ol = True
            self.ques_ol_depth = 1
            return

        if self.in_ques_ol and tag == "ol":
            self.ques_ol_depth += 1

        if not self.in_ques_ol:
            return

        if tag == "li":
            if self.outer_li_depth == 0 and self.ques_ol_depth == 1:
                self.outer_li_depth = 1
                self.current = {
                    "title": "",
                    "qid": "",
                    "question": "",
                    "question_url": "",
                    "correct_pct": None,
                    "incorrect_pct": None,
                    "unattempted_pct": None,
                    "set_number": self.set_number,
                    "set_context": self.current_preamble,
                }
            elif self.outer_li_depth > 0:
                self.outer_li_depth += 1

        if tag == "p":
            if self.outer_li_depth == 0 and self.ques_ol_depth == 1:
                self.capture = "p_direct"
                self.capture_parts = []
                self.p_direct = True
            elif self.current is not None and not self.current.get("question"):
                self.capture = "p_question"
                self.capture_parts = []
                self.p_question = True

        if tag == "img" and self.capture == "p_direct":
            image_hint = " ".join(filter(None, [attrs.get("alt", ""), attrs.get("src", ""), attrs.get("data-src", "")]))
            if image_hint:
                self.capture_parts.append(image_hint)

        if tag == "h4" and self.current is not None:
            self.capture = "h4"
            self.capture_parts = []
            self.h4 = True

        if tag == "a" and self.current is not None:
            self.a_href = attrs.get("href", "")
            is_local_question = re.search(
                r"(?:(?:quant|quants|dilr|varc|verbal)-question-\d+|dilr-set\d+-\d+)\.shtml",
                self.a_href,
                re.I,
            )
            is_legacy_dilr = (
                "iim-cat-questions-answers.2iim.com" in self.a_href
                and self.a_href.lower().endswith(".shtml")
            )
            if is_local_question or is_legacy_dilr:
                self.current["question_url"] = urllib.parse.urljoin(self.page_url, self.a_href)

        if tag == "span" and self.current is not None:
            self.span_classes.append(attrs.get("class", ""))
            if "tooltiptext" in classes:
                self.capture = "tooltip"
                self.tooltip_parts = []

    def handle_endtag(self, tag):
        if not self.in_ques_ol:
            return

        if tag == "p" and self.capture in {"p_direct", "p_question"}:
            value = clean_text(" ".join(self.capture_parts))
            if self.capture == "p_direct" and value:
                self.current_preamble = value
                self.set_number += 1
            elif self.capture == "p_question" and self.current is not None:
                self.current["question"] = value
            self.capture = None
            self.capture_parts = []
            self.p_direct = False
            self.p_question = False

        if tag == "h4" and self.h4:
            if self.current is not None:
                self.current["title"] = clean_text(" ".join(self.capture_parts))
            self.capture = None
            self.capture_parts = []
            self.h4 = False

        if tag == "span" and self.capture == "tooltip":
            value = clean_text(" ".join(self.tooltip_parts))
            if self.current is not None and "Correct:" in value:
                for field, label in [
                    ("correct_pct", "Correct"),
                    ("incorrect_pct", "Incorrect"),
                    ("unattempted_pct", "Unattempted"),
                ]:
                    match = re.search(rf"{label}:\s*([0-9.]+)%", value, re.I)
                    if match:
                        self.current[field] = float(match.group(1)) / 100.0
            self.capture = None
            self.tooltip_parts = []
            if self.span_classes:
                self.span_classes.pop()

        if tag == "li" and self.outer_li_depth > 0:
            self.outer_li_depth -= 1
            if self.outer_li_depth == 0 and self.current is not None:
                if self.current.get("question_url") or self.current.get("qid"):
                    self.questions.append(self.current)
                self.current = None

        if tag == "ol":
            self.ques_ol_depth -= 1
            if self.ques_ol_depth == 0:
                self.in_ques_ol = False

    def handle_data(self, data):
        if self.capture in {"p_direct", "p_question", "h4"}:
            self.capture_parts.append(data)
        elif self.capture == "tooltip":
            self.tooltip_parts.append(data)

    def handle_comment(self, data):
        if self.current is None:
            return
        match = re.search(r"QID:\s*([A-Za-z0-9_-]+)", data)
        if match:
            self.current["qid"] = match.group(1)


def page_urls():
    rows = []
    for year in range(2017, 2026):
        max_slot = 2 if year <= 2019 else 3
        for slot in range(1, max_slot + 1):
            for section, slug in [("Quant", "Quant"), ("DILR", "DILR"), ("VARC", "VARC")]:
                url = f"{BASE}CAT-{year}-Question-Paper-Slot-{slot}-{slug}/"
                rows.append((year, slot, section, url))
    return rows


def fetch_page(row):
    year, slot, section, url = row
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; CAT-PYQ-Indexer/1.0; educational-use)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read().decode("utf-8", errors="replace")
            body = re.sub(
                r'(<ol class="ques ques1">\s*)<ol class="ques ques1">',
                r"\1",
                body,
                count=1,
                flags=re.I,
            )
            parser = QuestionPageParser(url)
            parser.feed(body)
            questions = parser.questions
            set_titles = {
                int(number): clean_text(re.sub(r"<[^>]+>", " ", title))
                for number, title in re.findall(
                    r"<h3[^>]*>\s*(?:<b>)?\s*Set\s*(\d+)\s*:\s*(.*?)(?:</b>)?\s*</h3>",
                    body,
                    flags=re.I | re.S,
                )
            }
            for index, question in enumerate(questions, start=1):
                legacy_set = re.search(r"dilr-set(\d+)-\d+\.shtml", question.get("question_url", ""), re.I)
                if legacy_set:
                    question["set_number"] = int(legacy_set.group(1))
                    question["set_context"] = set_titles.get(int(legacy_set.group(1)), "")
                elif section == "DILR" and year == 2019:
                    inferred_set = (index - 1) // 4 + 1
                    question["set_number"] = inferred_set
                    question["set_context"] = set_titles.get(inferred_set, question.get("set_context", ""))
                question.update(
                    {
                        "year": year,
                        "slot": slot,
                        "section": section,
                        "question_number": index,
                        "source_page": url,
                    }
                )
            return {"page": row, "questions": questions, "error": None}
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1.5 * (attempt + 1))
    return {"page": row, "questions": [], "error": last_error}


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(fetch_page, page_urls()):
            results.append(result)
            year, slot, section, _ = result["page"]
            print(f"{year} S{slot} {section}: {len(result['questions'])} questions")

    errors = [result for result in results if result["error"]]
    questions = [question for result in results for question in result["questions"]]
    questions.sort(key=lambda q: (q["section"], q["year"], q["slot"], q["question_number"]))

    with (TMP / "raw_catalog.json").open("w", encoding="utf-8") as handle:
        json.dump(questions, handle, ensure_ascii=False, indent=2)

    fields = [
        "section", "year", "slot", "question_number", "qid", "title", "set_number",
        "question_url", "source_page", "correct_pct", "incorrect_pct", "unattempted_pct",
        "question", "set_context",
    ]
    with (TMP / "raw_catalog.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: q.get(field) for field in fields} for q in questions)

    quant_titles = Counter(q["title"] for q in questions if q["section"] == "Quant")
    with (TMP / "quant_title_counts.txt").open("w", encoding="utf-8") as handle:
        for title, count in sorted(quant_titles.items()):
            handle.write(f"{count:3d} | {title}\n")

    summary = {
        "total_questions": len(questions),
        "pages": len(results),
        "errors": [
            {"year": r["page"][0], "slot": r["page"][1], "section": r["page"][2], "error": r["error"]}
            for r in errors
        ],
        "counts_by_section": dict(Counter(q["section"] for q in questions)),
        "counts_by_year": dict(Counter(str(q["year"]) for q in questions)),
    }
    (TMP / "crawl_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
