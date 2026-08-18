from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "tmp" / "cat_pyq" / "classified_catalog.json"
OUTPUT_ROOT = ROOT / "output" / "pdf" / "CAT_2026_PYQ_SYSTEM"
SOURCE_URL = "https://online.2iim.com/CAT-question-paper/"

NAVY = colors.HexColor("#14213D")
BLUE = colors.HexColor("#2563EB")
TEAL = colors.HexColor("#0F766E")
ORANGE = colors.HexColor("#EA580C")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
LIGHT_GRAY = colors.HexColor("#F8FAFC")
MID_GRAY = colors.HexColor("#CBD5E1")
DARK_GRAY = colors.HexColor("#334155")


def register_fonts():
    candidates = [
        ("Aptos", Path("C:/Windows/Fonts/aptos.ttf")),
        ("Aptos-Bold", Path("C:/Windows/Fonts/aptos-bold.ttf")),
        ("Arial", Path("C:/Windows/Fonts/arial.ttf")),
        ("Arial-Bold", Path("C:/Windows/Fonts/arialbd.ttf")),
    ]
    for name, path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))
    if "Aptos" in pdfmetrics.getRegisteredFontNames():
        return "Aptos", "Aptos-Bold"
    if "Arial" in pdfmetrics.getRegisteredFontNames():
        return "Arial", "Arial-Bold"
    return "Helvetica", "Helvetica-Bold"


BODY_FONT, BOLD_FONT = register_fonts()


class IndexedDocTemplate(BaseDocTemplate):
    def __init__(self, filename, title, **kwargs):
        super().__init__(filename, **kwargs)
        self.document_title = title
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="content", frames=frame, onPage=self.draw_page)])

    def draw_page(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        if doc.page > 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, height - 12 * mm, width, 12 * mm, fill=1, stroke=0)
            canvas.setFont(BOLD_FONT, 8)
            canvas.setFillColor(colors.white)
            canvas.drawString(18 * mm, height - 8 * mm, self.document_title)
        canvas.setStrokeColor(MID_GRAY)
        canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
        canvas.setFont(BODY_FONT, 7)
        canvas.setFillColor(DARK_GRAY)
        canvas.drawString(18 * mm, 9 * mm, "CAT 2026 PYQ preparation system | Source-index edition")
        canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {doc.page}")
        canvas.saveState()
        canvas.setTitle(self.document_title)
        canvas.restoreState()
        canvas.restoreState()


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom", parent=styles["Title"], fontName=BOLD_FONT, fontSize=26,
            leading=30, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCustom", parent=styles["BodyText"], fontName=BODY_FONT,
            fontSize=11, leading=16, textColor=DARK_GRAY, spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "H1Custom", parent=styles["Heading1"], fontName=BOLD_FONT, fontSize=18,
            leading=22, textColor=NAVY, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2Custom", parent=styles["Heading2"], fontName=BOLD_FONT, fontSize=11,
            leading=14, textColor=TEAL, spaceBefore=7, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BodyCustom", parent=styles["BodyText"], fontName=BODY_FONT, fontSize=9,
            leading=13, textColor=DARK_GRAY, spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "SmallCustom", parent=styles["BodyText"], fontName=BODY_FONT, fontSize=7.3,
            leading=9, textColor=DARK_GRAY,
        ),
        "small_bold": ParagraphStyle(
            "SmallBold", parent=styles["BodyText"], fontName=BOLD_FONT, fontSize=7.3,
            leading=9, textColor=NAVY,
        ),
        "note": ParagraphStyle(
            "NoteCustom", parent=styles["BodyText"], fontName=BODY_FONT, fontSize=8.5,
            leading=12, textColor=DARK_GRAY, leftIndent=8, rightIndent=8,
        ),
        "center": ParagraphStyle(
            "CenterCustom", parent=styles["BodyText"], fontName=BOLD_FONT,
            fontSize=8, leading=10, alignment=TA_CENTER, textColor=NAVY,
        ),
    }


STYLES = build_styles()


def p(text, style="body"):
    return Paragraph(str(text), STYLES[style])


def section_name(section: str) -> str:
    return {"Quant": "Quantitative Aptitude", "DILR": "Data Interpretation and Logical Reasoning", "VARC": "VARC"}[section]


def output_path(section: str) -> Path:
    folder = {"Quant": "Quants", "DILR": "DILR", "VARC": "VARC"}[section]
    filename = {
        "Quant": "CAT_Quants_Topicwise_2017-2025.pdf",
        "DILR": "CAT_DILR_Topicwise_2017-2025.pdf",
        "VARC": "CAT_VARC_Topicwise_2017-2025.pdf",
    }[section]
    target = OUTPUT_ROOT / folder / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def summary_table(rows):
    topic_counts = Counter((row["subsection"], row["topic"]) for row in rows)
    data = [[p("Area", "small_bold"), p("Topic", "small_bold"), p("Questions", "small_bold")]]
    ranked_topics = sorted(
        topic_counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )
    for (subsection, topic), count in ranked_topics:
        data.append([p(xml_escape(subsection), "small"), p(xml_escape(topic), "small"), p(count, "center")])
    table = LongTable(data, colWidths=[41 * mm, 102 * mm, 25 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, MID_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def question_table(rows):
    header = [
        p("Slot", "small_bold"), p("Q", "small_bold"), p("Reference", "small_bold"),
        p("Difficulty*", "small_bold"), p("Question cue", "small_bold"), p("Source", "small_bold"),
    ]
    data = [header]
    for row in rows:
        link = row.get("question_url") or row.get("source_page")
        link_text = f'<link href="{link}" color="#2563EB"><u>Open</u></link>' if link else "Page"
        data.append([
            p(row["slot"], "center"),
            p(row["question_number"], "center"),
            p(xml_escape(row["question_id"]), "small"),
            p(xml_escape(row["archive_difficulty"]), "small"),
            p(row["question_cue"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), "small"),
            p(link_text, "center"),
        ])
    table = LongTable(
        data,
        colWidths=[12 * mm, 11 * mm, 37 * mm, 23 * mm, 76 * mm, 17 * mm],
        repeatRows=1,
        splitByRow=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, MID_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def build_pdf(section: str, catalog: list[dict]):
    rows = [row for row in catalog if row["section"] == section]
    target = output_path(section)
    title = f"CAT {section_name(section)} Topicwise PYQ Index (2017-2025)"
    doc = IndexedDocTemplate(
        str(target), title,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        author="CAT 2026 PYQ Preparation System",
        subject="Topicwise CAT previous-year question index",
    )

    years = sorted({row["year"] for row in rows})
    topic_counts = Counter((row["subsection"], row["topic"]) for row in rows)
    topics = [
        topic
        for topic, _count in sorted(
            topic_counts.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )
    ]
    review_count = sum(1 for row in rows if row.get("needs_review"))
    story = [
        Spacer(1, 18 * mm),
        p(xml_escape(title), "title"),
        p(
            f"A source-linked practice index covering {len(rows):,} questions across CAT {years[0]}-{years[-1]}. "
            f"Topics are ranked from most frequent to least frequent, then grouped by year and slot.",
            "subtitle",
        ),
    ]
    cards = Table([
        [p(f"<b>{len(rows):,}</b><br/>Questions", "center"),
         p(f"<b>{len(topics)}</b><br/>Topic groups", "center"),
         p(f"<b>{len(years)}</b><br/>Exam years", "center"),
         p(f"<b>{review_count:,}</b><br/>Review flags", "center")]
    ], colWidths=[42 * mm] * 4, rowHeights=[20 * mm])
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#93C5FD")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.extend([cards, Spacer(1, 8 * mm)])

    note = Table([[p(
        "How to use: open each linked question, solve it under a timer, and record the result in the companion workbook. "
        "Difficulty marked with an asterisk is derived from public archive attempt statistics when available; Unrated means no attempt statistic was available. "
        "Topic labels are a practical preparation taxonomy. Rows marked for review are broad or image-dependent classifications that should be checked while solving.",
        "note",
    )]], colWidths=[168 * mm])
    note.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#FDBA74")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        note,
        Spacer(1, 5 * mm),
        p(f'Source archive: <link href="{SOURCE_URL}" color="#2563EB"><u>{SOURCE_URL}</u></link>', "small"),
        PageBreak(),
        p("Priority topic map", "h1"),
        p("Topics are sorted by question frequency, highest first. Counts represent individual questions, not sets.", "body"),
        summary_table(rows),
    ])

    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[(row["subsection"], row["topic"])][row["year"]].append(row)

    for subsection, topic in topics:
        story.append(PageBreak())
        story.append(p(xml_escape(subsection.upper()), "h2"))
        story.append(p(xml_escape(topic), "h1"))
        topic_rows = [row for year_rows in grouped[(subsection, topic)].values() for row in year_rows]
        year_counts = Counter(row["year"] for row in topic_rows)
        count_text = " | ".join(f"{year}: {year_counts[year]}" for year in sorted(year_counts))
        story.append(p(f"{len(topic_rows)} questions | {count_text}", "body"))

        for year in sorted(grouped[(subsection, topic)]):
            year_rows = sorted(grouped[(subsection, topic)][year], key=lambda r: (r["slot"], r["question_number"]))
            story.append(p(f"CAT {year} - {len(year_rows)} questions", "h2"))
            story.append(question_table(year_rows))
            story.append(Spacer(1, 3 * mm))

    doc.build(story)
    print(target)


def main():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    for section in ["Quant", "DILR", "VARC"]:
        build_pdf(section, catalog)


if __name__ == "__main__":
    main()
