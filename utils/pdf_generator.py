import io
import re
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import Flowable

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0f172a")
NAVY_LIGHT = colors.HexColor("#1e293b")
INDIGO     = colors.HexColor("#6366f1")
INDIGO_LIGHT = colors.HexColor("#818cf8")
GREEN      = colors.HexColor("#22c55e")
AMBER      = colors.HexColor("#f59e0b")
SLATE      = colors.HexColor("#64748b")
SLATE_LIGHT= colors.HexColor("#94a3b8")
WHITE      = colors.HexColor("#f1f5f9")
BODY_TEXT  = colors.HexColor("#334155")
PAGE_BG    = colors.HexColor("#ffffff")

SECTION_ACCENTS = [INDIGO, GREEN, AMBER, colors.HexColor("#06b6d4"),
                   colors.HexColor("#ec4899"), colors.HexColor("#8b5cf6"), AMBER]


# ── Coloured left-border block ─────────────────────────────────────────────────
class ColorBar(Flowable):
    def __init__(self, color, width, height):
        super().__init__()
        self.color = color
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


# ── Style sheet ────────────────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Normal"],
            fontSize=30, textColor=WHITE, fontName="Helvetica-Bold",
            leading=36, spaceAfter=8, alignment=TA_LEFT,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub", parent=base["Normal"],
            fontSize=13, textColor=INDIGO_LIGHT, fontName="Helvetica",
            spaceAfter=4, alignment=TA_LEFT,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["Normal"],
            fontSize=10, textColor=SLATE_LIGHT, fontName="Helvetica",
            spaceAfter=2, alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", parent=base["Normal"],
            fontSize=15, textColor=NAVY, fontName="Helvetica-Bold",
            spaceBefore=4, spaceAfter=4, leading=18,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Normal"],
            fontSize=12, textColor=INDIGO, fontName="Helvetica-Bold",
            spaceBefore=10, spaceAfter=3, leading=15,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Normal"],
            fontSize=11, textColor=colors.HexColor("#1e293b"), fontName="Helvetica-Bold",
            spaceBefore=7, spaceAfter=2, leading=14,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=10, textColor=BODY_TEXT, fontName="Helvetica",
            spaceAfter=5, leading=16, alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["Normal"],
            fontSize=10, textColor=BODY_TEXT, fontName="Helvetica",
            spaceAfter=3, leading=15, leftIndent=16, firstLineIndent=-10,
        ),
        "bullet2": ParagraphStyle(
            "Bullet2", parent=base["Normal"],
            fontSize=9.5, textColor=SLATE, fontName="Helvetica",
            spaceAfter=2, leading=14, leftIndent=30, firstLineIndent=-10,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel", parent=base["Normal"],
            fontSize=9, textColor=SLATE_LIGHT, fontName="Helvetica",
            spaceAfter=1, alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue", parent=base["Normal"],
            fontSize=15, textColor=INDIGO, fontName="Helvetica-Bold",
            spaceAfter=2, alignment=TA_CENTER, leading=18,
        ),
        "toc_item": ParagraphStyle(
            "TocItem", parent=base["Normal"],
            fontSize=10.5, textColor=NAVY, fontName="Helvetica",
            spaceAfter=5, leading=14,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontSize=8, textColor=SLATE, fontName="Helvetica",
            alignment=TA_CENTER,
        ),
    }


# ── Markdown → ReportLab paragraphs ──────────────────────────────────────────
def _md_inline(text: str) -> str:
    """Convert inline markdown (**bold**, *italic*, `code`) to ReportLab XML."""
    # escape existing XML chars first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # bold+italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # inline code
    text = re.sub(r'`(.+?)`', r'<font name="Courier" size="9" color="#6366f1">\1</font>', text)
    return text


def _parse_markdown(content: str, styles: dict) -> list:
    """Parse markdown text into a list of ReportLab flowables."""
    flowables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # blank line
        if not stripped:
            flowables.append(Spacer(1, 3 * mm))
            i += 1
            continue

        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = _md_inline(stripped[2:].strip())
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        # H2
        if stripped.startswith("## ") and not stripped.startswith("### "):
            text = _md_inline(stripped[3:].strip())
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            text = _md_inline(stripped[4:].strip())
            flowables.append(Paragraph(text, styles["h3"]))
            i += 1
            continue

        # H4
        if stripped.startswith("#### "):
            text = _md_inline(stripped[5:].strip())
            flowables.append(Paragraph(f"<b>{text}</b>", styles["body"]))
            i += 1
            continue

        # table row (| ... |)
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            # filter out separator rows (| --- |)
            rows = [r for r in table_lines if not re.match(r'^\|[\s\-|:]+\|$', r)]
            if rows:
                data = []
                for row in rows:
                    cells = [c.strip() for c in row.strip("|").split("|")]
                    data.append(cells)
                if data:
                    col_count = max(len(r) for r in data)
                    # pad rows
                    data = [r + [''] * (col_count - len(r)) for r in data]
                    col_w = (17 * cm) / col_count
                    tbl = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
                    tbl.setStyle(TableStyle([
                        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
                        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
                        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                        ("FONTSIZE",      (0, 0), (-1, 0),  9),
                        ("FONTSIZE",      (0, 1), (-1, -1), 9),
                        ("TEXTCOLOR",     (0, 1), (-1, -1), BODY_TEXT),
                        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
                        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING",    (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
                    ]))
                    flowables.append(Spacer(1, 2 * mm))
                    flowables.append(tbl)
                    flowables.append(Spacer(1, 2 * mm))
            continue

        # bullet (-, *, •) — depth 1
        if re.match(r'^[-*•]\s', stripped):
            text = _md_inline(stripped[2:].strip())
            flowables.append(Paragraph(f"<font color='#6366f1'>▸</font>  {text}", styles["bullet"]))
            i += 1
            continue

        # bullet depth 2 (indented with spaces/tabs)
        if re.match(r'^  +[-*•]\s', raw) or re.match(r'^\t[-*•]\s', raw):
            inner = re.sub(r'^[\s\t]+[-*•]\s', '', raw)
            text = _md_inline(inner.strip())
            flowables.append(Paragraph(f"<font color='#94a3b8'>◦</font>  {text}", styles["bullet2"]))
            i += 1
            continue

        # numbered list
        if re.match(r'^\d+\.\s', stripped):
            num = re.match(r'^(\d+)\.\s', stripped).group(1)
            text = _md_inline(stripped[len(num)+2:].strip())
            flowables.append(Paragraph(f"<font color='#6366f1'><b>{num}.</b></font>  {text}", styles["bullet"]))
            i += 1
            continue

        # horizontal rule
        if re.match(r'^---+$', stripped):
            flowables.append(Spacer(1, 2 * mm))
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # normal paragraph
        text = _md_inline(stripped)
        flowables.append(Paragraph(text, styles["body"]))
        i += 1

    return flowables


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover(story, styles, metrics: dict):
    # dark navy background via a wide table
    cover_data = [[""]]
    cover_tbl = Table(cover_data, colWidths=[17 * cm], rowHeights=[6 * cm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
    ]))

    story.append(Spacer(1, 0.5 * cm))

    # header block
    header_inner = [
        [Paragraph("ProductIQ", ParagraphStyle("CI", fontName="Helvetica-Bold", fontSize=32,
                                                textColor=WHITE, leading=36, spaceAfter=4))],
        [Paragraph("AI-Powered Product Strategy Report", ParagraphStyle("CS", fontName="Helvetica",
                                                                         fontSize=14, textColor=INDIGO_LIGHT, spaceAfter=6))],
        [Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y  %H:%M')}",
                   ParagraphStyle("CD", fontName="Helvetica", fontSize=10, textColor=SLATE_LIGHT, spaceAfter=2))],
    ]
    header_tbl = Table(header_inner, colWidths=[17 * cm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 24),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 24),
        ("LINEBELOW", (0, -1), (-1, -1), 3, INDIGO),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.6 * cm))

    # metrics grid on cover
    if metrics:
        items = list(metrics.items())
        chunk = 4
        for row_start in range(0, min(len(items), 8), chunk):
            row_items = items[row_start:row_start + chunk]
            cells = []
            for k, v in row_items:
                cell = [
                    Paragraph(str(v), styles["metric_value"]),
                    Paragraph(str(k),  styles["metric_label"]),
                ]
                cells.append(cell)
            # pad to chunk width
            while len(cells) < chunk:
                cells.append([Paragraph("", styles["metric_value"]), Paragraph("", styles["metric_label"])])

            col_w = 17 * cm / chunk
            mt = Table([cells], colWidths=[col_w] * chunk)
            mt.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LINEABOVE",     (0, 0), (-1, 0),  2, INDIGO),
            ]))
            story.append(mt)
            story.append(Spacer(1, 0.3 * cm))

    story.append(Spacer(1, 0.5 * cm))

    # table of contents
    TOC = [
        "1. Customer Insights Report",
        "2. Market Research Summary",
        "3. SWOT Analysis",
        "4. Feature Prioritization",
        "5. Product Opportunity Assessment",
        "6. Strategic Action Plan & Roadmap",
        "7. Executive Summary",
    ]
    toc_data = [[Paragraph("<b>Contents</b>", ParagraphStyle("TH", fontName="Helvetica-Bold",
                                                               fontSize=11, textColor=WHITE))]]
    for item in TOC:
        toc_data.append([Paragraph(f"  {item}", styles["toc_item"])])

    toc_tbl = Table(toc_data, colWidths=[17 * cm])
    row_bgs = [NAVY] + [colors.HexColor("#f8fafc") if i % 2 == 0 else colors.white for i in range(len(TOC))]
    toc_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0),  NAVY),
        *[("BACKGROUND",  (0, i+1), (0, i+1), row_bgs[i+1]) for i in range(len(TOC))],
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(toc_tbl)
    story.append(PageBreak())


# ── Section header bar ────────────────────────────────────────────────────────
def _section_header(story, number: str, title: str, accent: colors.Color, styles: dict):
    header_data = [[
        Paragraph(f"<font color='#ffffff'><b>{number}</b></font>",
                  ParagraphStyle("SN", fontName="Helvetica-Bold", fontSize=18,
                                 textColor=WHITE, alignment=TA_CENTER, leading=22)),
        Paragraph(f"<font color='#ffffff'><b>{title}</b></font>",
                  ParagraphStyle("ST", fontName="Helvetica-Bold", fontSize=14,
                                 textColor=WHITE, leading=18, spaceAfter=0)),
    ]]
    tbl = Table(header_data, colWidths=[1.2 * cm, 15.8 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), accent),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, 0),   10),
        ("LEFTPADDING",   (1, 0), (1, 0),   12),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(tbl)
    story.append(Spacer(1, 0.3 * cm))


# ── Page template with footer ─────────────────────────────────────────────────
def _on_page(canvas, doc, styles):
    canvas.saveState()
    w, h = A4
    # footer line
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.3*cm, w-2*cm, 1.3*cm)
    # left footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SLATE)
    canvas.drawString(2*cm, 0.9*cm, "ProductIQ — AI-Powered Product Strategy Assistant")
    # right footer (page number)
    canvas.drawRightString(w-2*cm, 0.9*cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Main entry point ──────────────────────────────────────────────────────────
def generate_report(insights: dict) -> bytes:
    buffer = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="ProductIQ Strategy Report",
        author="ProductIQ AI",
    )

    story = []

    # ── Cover ──────────────────────────────────────────────────────────────────
    _cover(story, styles, insights.get("key_metrics", {}))

    # ── Content sections ───────────────────────────────────────────────────────
    SECTIONS = [
        ("customer_insights",       "01", "Customer Insights Report"),
        ("market_research",         "02", "Market Research Summary"),
        ("swot_analysis",           "03", "SWOT Analysis"),
        ("feature_prioritization",  "04", "Feature Prioritization"),
        ("opportunity_assessment",  "05", "Product Opportunity Assessment"),
        ("strategy_recommendations","06", "Strategic Action Plan & Roadmap"),
        ("executive_summary",       "07", "Executive Summary"),
    ]

    for idx, (key, num, title) in enumerate(SECTIONS):
        content = insights.get(key, "")
        if not content:
            continue

        accent = SECTION_ACCENTS[idx % len(SECTION_ACCENTS)]
        _section_header(story, num, title, accent, styles)

        flowables = _parse_markdown(content, styles)
        story.extend(flowables)
        story.append(PageBreak())

    # ── Back page ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * cm))
    end_data = [[
        Paragraph("End of Report", ParagraphStyle("EP", fontName="Helvetica-Bold",
                                                   fontSize=18, textColor=WHITE,
                                                   alignment=TA_CENTER, leading=22)),
        Paragraph("This report was generated by ProductIQ — AI-Powered Product Strategy Assistant.",
                  ParagraphStyle("ES", fontName="Helvetica", fontSize=10,
                                 textColor=INDIGO_LIGHT, alignment=TA_CENTER, leading=14)),
    ]]
    end_tbl = Table([[end_data[0][0]], [end_data[0][1]]], colWidths=[17 * cm])
    end_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(end_tbl)

    doc.build(
        story,
        onFirstPage=lambda c, d: _on_page(c, d, styles),
        onLaterPages=lambda c, d: _on_page(c, d, styles),
    )
    buffer.seek(0)
    return buffer.read()
