"""
generate_report.py
Generates the CheckinMe AI Profile Generator — Prompt Engineering Research Report as a
professional PDF using ReportLab Platypus.

Usage:
    /opt/anaconda3/bin/python3 generate_report.py
Output:
    PROMPT_ENGINEERING_REPORT.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime, os

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
NAVY      = colors.HexColor("#1E3A5F")
BLUE      = colors.HexColor("#2563EB")
GREEN     = colors.HexColor("#16A34A")
AMBER     = colors.HexColor("#D97706")
LIGHTGREY = colors.HexColor("#F3F4F6")
MIDGREY   = colors.HexColor("#9CA3AF")
DARKGREY  = colors.HexColor("#1F2937")
RULERED   = colors.HexColor("#E5E7EB")
WHITE     = colors.white

PAGE_W, PAGE_H = A4
MARGIN_L = MARGIN_R = 2.2 * cm
MARGIN_T = MARGIN_B = 2.4 * cm

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "PROMPT_ENGINEERING_REPORT.pdf")

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def build_styles():
    base = getSampleStyleSheet()

    def _s(name, **kw):
        return ParagraphStyle(name, **kw)

    styles = {
        # ---- Cover ----
        "cover_title": _s("cover_title",
            fontName="Helvetica-Bold", fontSize=26, leading=32,
            textColor=WHITE, alignment=TA_LEFT, spaceAfter=6),
        "cover_subtitle": _s("cover_subtitle",
            fontName="Helvetica", fontSize=13, leading=18,
            textColor=colors.HexColor("#CBD5E1"), alignment=TA_LEFT, spaceAfter=4),
        "cover_meta": _s("cover_meta",
            fontName="Helvetica", fontSize=9, leading=14,
            textColor=colors.HexColor("#94A3B8"), alignment=TA_LEFT),

        # ---- Section headings ----
        "h1": _s("h1",
            fontName="Helvetica-Bold", fontSize=16, leading=22,
            textColor=NAVY, spaceBefore=18, spaceAfter=6),
        "h2": _s("h2",
            fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=BLUE, spaceBefore=14, spaceAfter=4),
        "h3": _s("h3",
            fontName="Helvetica-BoldOblique", fontSize=10, leading=14,
            textColor=DARKGREY, spaceBefore=10, spaceAfter=3),

        # ---- Body text ----
        "body": _s("body",
            fontName="Helvetica", fontSize=9.5, leading=14.5,
            textColor=DARKGREY, alignment=TA_JUSTIFY, spaceAfter=6),
        "body_left": _s("body_left",
            fontName="Helvetica", fontSize=9.5, leading=14.5,
            textColor=DARKGREY, alignment=TA_LEFT, spaceAfter=4),
        "bullet": _s("bullet",
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=DARKGREY, leftIndent=14, firstLineIndent=0,
            spaceAfter=3),
        "caption": _s("caption",
            fontName="Helvetica-Oblique", fontSize=8, leading=11,
            textColor=MIDGREY, alignment=TA_CENTER, spaceAfter=6),

        # ---- Code ----
        "code": _s("code",
            fontName="Courier", fontSize=8, leading=12,
            textColor=colors.HexColor("#374151"),
            backColor=colors.HexColor("#F9FAFB"),
            leftIndent=10, rightIndent=10,
            spaceBefore=4, spaceAfter=4),

        # ---- Table ----
        "tbl_head": _s("tbl_head",
            fontName="Helvetica-Bold", fontSize=8.5, leading=11,
            textColor=WHITE, alignment=TA_LEFT),
        "tbl_cell": _s("tbl_cell",
            fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=DARKGREY, alignment=TA_LEFT),
        "tbl_cell_center": _s("tbl_cell_center",
            fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=DARKGREY, alignment=TA_CENTER),

        # ---- Verdict / callout ----
        "callout": _s("callout",
            fontName="Helvetica-Bold", fontSize=9.5, leading=14,
            textColor=NAVY, leftIndent=12, rightIndent=12,
            spaceBefore=6, spaceAfter=6),

        # ---- TOC ----
        "toc": _s("toc",
            fontName="Helvetica", fontSize=9.5, leading=15,
            textColor=DARKGREY, leftIndent=0, spaceAfter=1),
        "toc_sub": _s("toc_sub",
            fontName="Helvetica", fontSize=9, leading=14,
            textColor=MIDGREY, leftIndent=14, spaceAfter=1),

        # ---- Footer ----
        "footer": _s("footer",
            fontName="Helvetica", fontSize=7.5, leading=10,
            textColor=MIDGREY, alignment=TA_CENTER),
    }
    return styles


# ---------------------------------------------------------------------------
# Page templates (header / footer)
# ---------------------------------------------------------------------------

class ReportCanvas:
    """Mixin that draws the running header and footer on every page."""

    def __init__(self, project, report_date):
        self.project = project
        self.report_date = report_date

    def __call__(self, canvas, doc):
        canvas.saveState()
        page_num = doc.page

        if page_num == 1:          # cover page — no header/footer
            canvas.restoreState()
            return

        # Top rule
        canvas.setStrokeColor(RULERED)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 6*mm,
                    PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 6*mm)

        # Header text
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MIDGREY)
        canvas.drawString(MARGIN_L, PAGE_H - MARGIN_T + 8*mm, self.project)
        canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 8*mm,
                               "Prompt Engineering Research Report")

        # Bottom rule
        canvas.line(MARGIN_L, MARGIN_B - 4*mm,
                    PAGE_W - MARGIN_R, MARGIN_B - 4*mm)

        # Footer text
        canvas.drawString(MARGIN_L, MARGIN_B - 8*mm, self.report_date)
        canvas.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 8*mm,
                               f"Page {page_num}")

        canvas.restoreState()


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def rule(story, colour=RULERED, thickness=0.5, space=4):
    story.append(Spacer(1, space))
    story.append(HRFlowable(width="100%", thickness=thickness,
                             color=colour, spaceAfter=space))


def h1(story, text, styles):
    rule(story, NAVY, 1.5, 2)
    story.append(Paragraph(text, styles["h1"]))


def h2(story, text, styles):
    story.append(Paragraph(text, styles["h2"]))


def h3(story, text, styles):
    story.append(Paragraph(text, styles["h3"]))


def body(story, text, styles, align="justify"):
    st = styles["body"] if align == "justify" else styles["body_left"]
    story.append(Paragraph(text, st))


def bullet(story, items, styles, symbol="•"):
    for item in items:
        story.append(Paragraph(f"{symbol}  {item}", styles["bullet"]))


def code_block(story, text, styles):
    # Split into lines to preserve formatting
    lines = text.strip().split("\n")
    for line in lines:
        story.append(Paragraph(line.replace(" ", "&nbsp;") if line.strip() else "&nbsp;",
                                styles["code"]))
    story.append(Spacer(1, 4))


def metric_table(story, headers, rows, styles, col_widths=None):
    avail_w = PAGE_W - MARGIN_L - MARGIN_R
    if col_widths is None:
        col_widths = [avail_w / len(headers)] * len(headers)

    tbl_data = [[Paragraph(h, styles["tbl_head"]) for h in headers]]
    for row in rows:
        tbl_data.append([Paragraph(str(c), styles["tbl_cell"]) for c in row])

    tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUND",(0, 1), (-1, -1), [LIGHTGREY, WHITE]),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
        ("LEADING",      (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUND",(0, 1), (-1, -1), [LIGHTGREY, WHITE]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))


def callout_box(story, text, styles, colour=LIGHTGREY, border=BLUE):
    """A highlighted callout / info box."""
    inner = [[Paragraph(text, styles["callout"])]]
    tbl = Table(inner, colWidths=[PAGE_W - MARGIN_L - MARGIN_R])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colour),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LINEAFTER",    (0, 0), (0, -1), 3, border),
        ("BOX",          (0, 0), (-1, -1), 0.5, colors.HexColor("#DBEAFE")),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def build_cover(story, styles):
    # Full-bleed navy background via a table spanning the page
    avail_w = PAGE_W - MARGIN_L - MARGIN_R
    avail_h = PAGE_H - MARGIN_T - MARGIN_B

    # Top colour block
    header_block = Table(
        [[Paragraph("", styles["cover_title"])]],
        colWidths=[avail_w], rowHeights=[0.3*cm],
    )
    header_block.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), NAVY)]))
    story.append(header_block)
    story.append(Spacer(1, 0))

    cover_content = [
        [
            Paragraph("AI Profile Generator", styles["cover_title"]),
        ],
        [
            Paragraph("Prompt Engineering Research Report", styles["cover_subtitle"]),
        ],
        [Paragraph("&nbsp;", styles["cover_meta"])],
        [Paragraph("Project: CheckinMe", styles["cover_meta"])],
        [Paragraph("Model: Google Gemini 2.5 Flash Image (configurable)", styles["cover_meta"])],
        [Paragraph("Scope: Prompt design, comparative benchmarking &amp; tooling", styles["cover_meta"])],
        [Paragraph(f"Date: {datetime.date.today().strftime('%d %B %Y')} (rev. 2)", styles["cover_meta"])],
        [Paragraph("Status: Directive + Prohibitions variant adopted into production", styles["cover_meta"])],
    ]
    cover_tbl = Table(cover_content, colWidths=[avail_w],
                      rowHeights=[None]*len(cover_content))
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",  (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
        ("TOPPADDING",   (0,0), (0, 0), 30),
        ("BOTTOMPADDING",(0,-1),(-1,-1), 30),
        ("TOPPADDING",   (0,1), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-2), 2),
    ]))
    story.append(cover_tbl)

    # Decorative accent strip
    accent = Table([[""]], colWidths=[avail_w], rowHeights=[6])
    accent.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), GREEN)]))
    story.append(accent)
    story.append(Spacer(1, 16))

    # Abstract / one-liner
    callout_box(story,
        "This report documents a structured prompt engineering initiative to improve "
        "face identity preservation, skin tone fidelity, image sharpness, and background "
        "uniformity in AI-generated professional headshots. Four prompt versions are designed, "
        "benchmarked, and compared against a seven-metric quantitative framework. As of this "
        "revision (rev. 2), the Directive + Prohibitions variant (formerly experimental v3) "
        "has been adopted as the live production prompt.",
        styles)

    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Table of Contents
# ---------------------------------------------------------------------------

def build_toc(story, styles):
    h1(story, "Table of Contents", styles)
    story.append(Spacer(1, 6))

    toc_items = [
        ("1.", "Executive Summary", False),
        ("2.", "Project Context", False),
        ("  2.1", "System Overview", True),
        ("  2.2", "Outfit Catalogue", True),
        ("3.", "Problem Statement", False),
        ("  3.1", "Primary Failure Mode: Identity Drift", True),
        ("  3.2", "Secondary Failure Modes", True),
        ("  3.3", "Structural Weaknesses in the Legacy Production Prompt", True),
        ("4.", "Technical Architecture", False),
        ("  4.1", "Production Service (AiProfileGenerateService.php)", True),
        ("  4.2", "Benchmarking Application (benchmark_app.py)", True),
        ("  4.3", "Model URL Architecture", True),
        ("5.", "Evaluation Methodology", False),
        ("  5.1", "Quantitative Metrics", True),
        ("  5.2", "Face Detection", True),
        ("  5.3", "Qualitative Assessment", True),
        ("  5.4", "Final Combined Score", True),
        ("6.", "Prompt Engineering Analysis", False),
        ("  6.1", "Design Philosophy", True),
        ("  6.2", "Legacy Production Prompt (Retired Baseline)", True),
        ("  6.3", "Experimental v1 — Photographer Role", True),
        ("  6.4", "Experimental v2 — Step-by-Step Identity", True),
        ("  6.5", "Experimental v3 — Directive + Prohibitions", True),
        ("  6.6", "Prompt Comparison Summary", True),
        ("  6.7", "Current Production Prompt — Type, Pros & Cons", True),
        ("7.", "Benchmarking Tool Design", False),
        ("8.", "Results", False),
        ("9.", "Recommendations", False),
        ("10.", "Appendix — Full Prompt Texts", False),
    ]

    for num, title, is_sub in toc_items:
        style = styles["toc_sub"] if is_sub else styles["toc"]
        story.append(Paragraph(f"<b>{num}</b>  {title}", style))

    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Section 1: Executive Summary
# ---------------------------------------------------------------------------

def build_executive_summary(story, styles):
    h1(story, "1. Executive Summary", styles)

    body(story,
        "CheckinMe's AI Profile Generator uses Google Gemini to transform a user-supplied "
        "reference photograph into a set of professional headshots with varied attire. "
        "The primary quality requirement — and the most common failure mode — is "
        "<b>face identity preservation</b>: the generated image must be recognisably the "
        "same person as in the input photo.", styles)

    body(story,
        "This report documents a structured prompt engineering effort to improve generation "
        "quality across four measurable dimensions: face structural similarity, skin tone "
        "fidelity, image sharpness, and background uniformity. Four prompt versions were "
        "designed (one production baseline and three experimental variants), and a "
        "Python/Streamlit benchmarking application was built to evaluate them against a "
        "seven-metric quantitative framework augmented by human qualitative assessment.", styles)

    h2(story, "Key Contributions", styles)
    bullet(story, [
        "Identification of three structural weaknesses in the production prompt.",
        "Design of three experimental prompt variants, each addressing a different "
        "hypothesis about model instruction following.",
        "A reproducible benchmarking tool supporting side-by-side visual comparison, "
        "automated metric computation, and human rating capture.",
        "A configurable model selector enabling cross-model comparisons without code changes.",
        "A live prompt editor allowing real-time prompt modifications and A/B testing "
        "directly in the Streamlit UI.",
    ], styles)

    callout_box(story,
        "<b>Outcome (rev. 2):</b> The Directive + Prohibitions variant (formerly experimental "
        "v3) has been adopted as the production prompt. It pairs strong positive identity "
        "anchoring with an explicit negative-constraint block and a modular, sectioned layout. "
        "See section 6.7 for the prompt-engineering classification and a pros/cons assessment.",
        styles, colour=LIGHTGREY, border=GREEN)


# ---------------------------------------------------------------------------
# Section 2: Project Context
# ---------------------------------------------------------------------------

def build_project_context(story, styles):
    h1(story, "2. Project Context", styles)

    h2(story, "2.1  System Overview", styles)
    body(story,
        "The production generation pipeline is implemented in "
        "<font name='Courier'>AiProfileGenerateService.php</font> (Laravel). "
        "When a user requests headshots, the service:", styles)
    bullet(story, [
        "Accepts a reference image path, gender, quantity (limit), and rotation offset.",
        "Selects 'limit' outfit descriptions from a pool of 16 per gender, applying "
        "the offset as a circular rotation.",
        "Constructs one text prompt per outfit.",
        "Calls the Gemini multimodal endpoint "
        "(gemini-2.5-flash-image:generateContent) with the prompt and "
        "the base64-encoded reference image.",
        "Extracts the inlineData.data field from the API response and "
        "returns it as a base64 PNG.",
    ], styles)

    body(story,
        "In non-production environments the service short-circuits and returns random "
        "existing media URLs to avoid API cost during development.", styles)

    h2(story, "2.2  Outfit Catalogue", styles)
    metric_table(story,
        ["Gender", "Pool Size", "Style Range"],
        [
            ["Male",   "16",
             "Black/navy/charcoal/grey suits with varied shirt and tie combinations"],
            ["Female", "16",
             "Black/navy/grey/dark blazers over white and light-coloured blouses"],
        ],
        styles,
        col_widths=[2.5*cm, 2.5*cm, 12.5*cm],
    )
    body(story,
        "All outfits are conservative corporate styles deliberately selected to minimise "
        "the risk of anatomical distortion at the neckline, a known failure mode of AI "
        "portrait generators.", styles)


# ---------------------------------------------------------------------------
# Section 3: Problem Statement
# ---------------------------------------------------------------------------

def build_problem_statement(story, styles):
    h1(story, "3. Problem Statement", styles)

    h2(story, "3.1  Primary Failure Mode: Identity Drift", styles)
    body(story,
        "When a generative vision model is instructed to re-dress a subject, it faces a "
        "fundamental tension: it must synthesise new clothing while holding the face "
        "constant. Without sufficiently strong identity anchoring instructions, "
        "models tend to:", styles)
    bullet(story, [
        "Smooth or 'beautify' skin texture, altering the perceived person.",
        "Shift skin tone slightly warm or cool depending on the chosen outfit's colour temperature.",
        "Subtly reshape the nose, jaw, or eye area to fit a 'professional' archetype.",
        "Alter hair style or colour.",
    ], styles)
    body(story,
        "The combined effect is a headshot that looks professional but is not recognisably "
        "the same individual — a product failure.", styles)

    h2(story, "3.2  Secondary Failure Modes", styles)
    metric_table(story,
        ["Failure Mode", "Visible Symptom", "Affected Metric"],
        [
            ["Skin tone drift",
             "Complexion appears lighter/darker or different undertone",
             "Skin Tone Match (20%)"],
            ["Over-smoothing",
             "Skin looks plastic or AI-generated",
             "Face SSIM (25%), Face Sharpness (20%)"],
            ["Framing errors",
             "Head cropped, or too much torso shown",
             "Framing Quality (10%)"],
            ["Background noise",
             "Gradient, texture, or vignette at corners",
             "Background Uniformity (15%)"],
            ["Anatomical distortion",
             "Floating collar, misaligned neck",
             "Qualitative — Clothing Quality"],
        ],
        styles,
        col_widths=[4*cm, 7*cm, 6.5*cm],
    )

    h2(story, "3.3  Structural Weaknesses in the Legacy Production Prompt", styles)
    callout_box(story,
        "<b>Resolved in current production (rev. 2).</b> The three issues below were identified "
        "in the legacy production prompt (Appendix E). All three are addressed by the current "
        "Directive + Prohibitions production prompt (Appendix A): identity is anchored "
        "immediately after the outfit clause, skin colour and undertone are named explicitly "
        "and reinforced by a prohibition, and the background block requires consistency from "
        "centre to all four edges of the frame. This section is retained to document the "
        "original rationale.",
        styles, colour=LIGHTGREY, border=GREEN)
    body(story,
        "Analysis of the legacy <font name='Courier'>build_production_prompt()</font> revealed "
        "three structural issues:", styles)

    h3(story, "Issue 1 — Late identity anchoring", styles)
    body(story,
        "The production prompt opens with outfit instruction "
        "(<i>Generate a portrait of a professional [gender] [outfit]</i>) before stating "
        "face preservation requirements. This ordering implicitly signals that the primary "
        "task is outfit generation, with identity preservation as a constraint. Multimodal "
        "LLMs tend to weight earlier instructions more heavily during synthesis.", styles)

    h3(story, "Issue 2 — Absent skin tone instruction", styles)
    body(story,
        "The phrase 'Do not alter facial structure, skin texture, or expression' does not "
        "mention skin colour or undertone explicitly. Skin tone shift is measured at 20% "
        "of the quantitative score, making this a high-impact omission.", styles)

    h3(story, "Issue 3 — Ambiguous background specification", styles)
    body(story,
        "'A soft, solid, professional ID card style background' is semantically "
        "underspecified. The benchmark measures background uniformity by sampling pixel "
        "variance in the four image corners. Any gradient or subtle texture that extends "
        "to the corners penalises the score; the production prompt does not instruct the "
        "model to maintain consistency to the image edges.", styles)


# ---------------------------------------------------------------------------
# Section 4: Technical Architecture
# ---------------------------------------------------------------------------

def build_architecture(story, styles):
    h1(story, "4. Technical Architecture", styles)

    h2(story, "4.1  Production Service (AiProfileGenerateService.php)", styles)
    code_block(story, """User request
    │
    ├── getPrompts(gender, limit, offset, aspectRatio)
    │       ├── Selects outfits from $outfits[gender]
    │       ├── Applies circular offset rotation
    │       └── Assembles: $commonIntro + $style + $commonFeatures
    │                      + $framingFix + $neckFix + $imageQuality
    │
    └── foreach $prompts as $prompt
            └── POST /v1beta/models/gemini-2.5-flash-image:generateContent
                    ├── parts[0]: text prompt
                    └── parts[1]: inline_data (base64 PNG/JPEG)
                    → returns base64 image → stored / returned to controller""", styles)

    h2(story, "4.2  Benchmarking Application (benchmark_app.py)", styles)
    code_block(story, """Streamlit UI
    │
    ├── Sidebar
    │       ├── Gemini API Key
    │       ├── Model selector (dynamic URL construction)
    │       ├── Gender / Outfit builder / Background selector
    │       └── Experimental prompt version selector (v1 / v2 / v3)
    │
    ├── Prompt Editor (main area)
    │       ├── Production text area — editable, reset button, live char count
    │       └── Experimental text area — editable, reset button, live char count
    │               Auto-reloads when version/outfit/background changes (fingerprint)
    │
    ├── Generate & Compare (button)
    │       └── ThreadPoolExecutor(max_workers=2)
    │               ├── call_gemini_api(prod_prompt, gemini_url)
    │               └── call_gemini_api(exp_prompt, gemini_url)
    │
    ├── Side-by-Side Image Comparison
    │
    ├── Quantitative Metrics  ─  bm.compute_all() → 8 scores
    │
    └── Qualitative Rating Panel (5 criteria × 1–5 stars)
            └── Final = 60% Quantitative + 40% Qualitative""", styles)

    h2(story, "4.3  Model URL Architecture", styles)
    body(story,
        "The Gemini model endpoint follows the pattern:", styles)
    code_block(story,
        "https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent",
        styles)
    body(story,
        "The model ID was previously hardcoded as the module-level constant "
        "<font name='Courier'>GEMINI_URL</font>. It is now constructed dynamically from "
        "a sidebar selectbox, enabling cross-model comparison (e.g., "
        "<font name='Courier'>gemini-2.5-flash-image</font> vs "
        "<font name='Courier'>gemini-2.0-flash-exp-image-generation</font>) without "
        "modifying source code. A custom model ID text input is also available for "
        "unreleased or preview models.", styles)


# ---------------------------------------------------------------------------
# Section 5: Evaluation Methodology
# ---------------------------------------------------------------------------

def build_methodology(story, styles):
    h1(story, "5. Evaluation Methodology", styles)

    h2(story, "5.1  Quantitative Metrics", styles)
    body(story,
        "All metrics produce scores on a 0–100 scale, combined into an "
        "<b>Overall Quantitative Score</b> via a fixed weighted average.", styles)

    metric_table(story,
        ["Metric", "Weight", "Library", "Primary Failure Detected"],
        [
            ["Face SSIM",            "25%", "scikit-image",
             "Identity drift — structural (SSIM on 96×96 face crop)"],
            ["Skin Tone Match",      "20%", "numpy",
             "Skin colour / undertone shift (R+G histogram correlation)"],
            ["Face Sharpness",       "20%", "opencv",
             "Blur, over-smoothing (Laplacian variance, threshold 1500)"],
            ["Background Uniformity","15%", "numpy",
             "Gradients, textures, vignettes (corner std dev)"],
            ["Framing Quality",      "10%", "opencv",
             "Zoom too close or too far (face/image height ratio)"],
            ["Face Centering",       " 5%", "opencv",
             "Off-centre composition (horizontal centroid offset)"],
            ["Exposure Quality",     " 5%", "numpy",
             "Over/underexposure (mean luminance vs 90–175 range)"],
        ],
        styles,
        col_widths=[3.8*cm, 1.5*cm, 2.5*cm, 9.7*cm],
    )

    callout_box(story,
        "Overall Quantitative Score = "
        "SSIM×0.25 + Skin×0.20 + Sharp×0.20 + BG×0.15 + Framing×0.10 + "
        "Centering×0.05 + Exposure×0.05",
        styles)

    h2(story, "5.2  Face Detection", styles)
    body(story,
        "Pre-processing for SSIM, Skin Tone, Sharpness, Framing, and Centering depends "
        "on locating the face. The implementation uses OpenCV's Haar cascade "
        "(<font name='Courier'>haarcascade_frontalface_default.xml</font>) with "
        "<font name='Courier'>scaleFactor=1.1</font>, "
        "<font name='Courier'>minNeighbors=5</font>, "
        "<font name='Courier'>minSize=(40,40)</font>. "
        "If detection fails, affected metrics return a neutral score of 50 "
        "(or 0 for Framing/Centering).", styles)

    h2(story, "5.3  Qualitative Assessment", styles)
    metric_table(story,
        ["Criterion", "Question"],
        [
            ["Face Resemblance",
             "Does the face look exactly like the person in the reference photo?"],
            ["Professional Look",
             "Does the overall image look like a professional headshot?"],
            ["Clothing Quality",
             "Does the clothing look natural, well-fitted, and realistic?"],
            ["Background Quality",
             "Is the background clean, solid, and professional?"],
            ["Overall Preference",
             "Overall, how satisfied are you with this image?"],
        ],
        styles,
        col_widths=[4*cm, 13.5*cm],
    )
    code_block(story, "Qualitative Score = (mean star rating / 5) × 100", styles)

    h2(story, "5.4  Final Combined Score", styles)
    code_block(story,
        "Final = 0.60 × Quantitative_Overall + 0.40 × Qualitative_Average", styles)
    metric_table(story,
        ["Condition", "Verdict"],
        [
            ["|Exp − Prod| < 2", "Tie"],
            ["Exp − Prod ≥ 2",   "Experimental wins"],
            ["Prod − Exp ≥ 2",   "Production wins"],
        ],
        styles,
        col_widths=[5*cm, 12.5*cm],
    )


# ---------------------------------------------------------------------------
# Section 6: Prompt Engineering
# ---------------------------------------------------------------------------

def build_prompt_engineering(story, styles):
    h1(story, "6. Prompt Engineering Analysis", styles)

    h2(story, "6.1  Design Philosophy", styles)
    body(story,
        "Each experimental version tests a distinct hypothesis about how Gemini "
        "processes multimodal instructions:", styles)
    metric_table(story,
        ["Version", "Hypothesis", "Status"],
        [
            ["Legacy Production",
             "Baseline: implicit identity constraint appended after outfit instruction.",
             "Retired"],
            ["v1 — Photographer Role",
             "Assigning a domain expert persona improves instruction compliance for "
             "professional outputs.",
             "Experimental"],
            ["v2 — Step-by-Step Identity",
             "Sequential processing steps with explicit metric-aligned sub-instructions "
             "improve targeted output quality.",
             "Experimental"],
            ["v3 — Directive + Prohibitions",
             "Explicit negative constraints (✗ DO NOT) are more reliably honoured "
             "than equivalent positive instructions.",
             "Adopted to production"],
        ],
        styles,
        col_widths=[3.6*cm, 10.6*cm, 3.3*cm],
    )

    # ---- Production ----
    h2(story, "6.2  Legacy Production Prompt (Retired Baseline)", styles)
    body(story,
        "<i>This was the production prompt at rev. 1. It has since been replaced by the "
        "Directive + Prohibitions structure (section 6.5 and 6.7). Full text in Appendix E.</i>",
        styles)
    metric_table(story,
        ["Attribute", "Value"],
        [
            ["Approximate length", "~430 characters / ~75 words"],
            ["Instruction order",  "Outfit → Identity → Framing → Anatomy → Quality"],
            ["Skin tone mentioned", "No"],
            ["Hair preservation",  "No"],
            ["Background edge spec", "No"],
            ["Negative prohibitions", "No"],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story, "<b>Strengths:</b> Concise, low token overhead, includes neck/anatomy "
        "fix and framing instruction.", styles)
    body(story, "<b>Weaknesses:</b> Outfit is the first clause — identity anchoring is "
        "secondary. No explicit skin tone, hair, age, or ethnic feature preservation. "
        "Background described as 'ID card style' — semantically ambiguous for corner "
        "uniformity. All instructions are positive; no negation list.", styles)

    # ---- v1 ----
    h2(story, "6.3  Experimental v1 — Photographer Role", styles)
    metric_table(story,
        ["Attribute", "Value"],
        [
            ["Approximate length",  "~900 characters / ~160 words"],
            ["Role assignment",     "You are a professional portrait photographer"],
            ["Identity before outfit", "Yes"],
            ["Skin tone named",     "Partially (within identity bullet)"],
            ["Hair preservation",   "Yes"],
            ["Negative prohibitions", "No"],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story,
        "<b>Key structural change:</b> Assigns a domain expert role before any task "
        "specification. Role-prompting in LLM literature shifts model behaviour toward "
        "domain-appropriate defaults. Identity block now precedes outfit instruction.", styles)
    body(story,
        "<b>Remaining gaps:</b> Skin tone and undertone not called out by name. "
        "Background uniformity to image edges not explicitly required. "
        "No negative prohibition block.", styles)

    # ---- v2 ----
    h2(story, "6.4  Experimental v2 — Step-by-Step Identity", styles)
    metric_table(story,
        ["Attribute", "Value"],
        [
            ["Approximate length",   "~1,150 characters / ~200 words"],
            ["Structure",            "6 numbered processing steps"],
            ["Skin tone named",      "Yes — Step 1 first bullet, incl. undertone"],
            ["Background edge spec", "Yes — 'clean all the way to the image edges'"],
            ["Sharpness instruction","Yes — 'face razor-sharp in focus'"],
            ["Negative prohibitions","No"],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story,
        "<b>Key structural change:</b> Replaces free-form instruction blocks with "
        "numbered processing steps, explicitly sequencing the model to anchor identity "
        "first before applying styling.", styles)

    metric_table(story,
        ["Metric", "Improvement Mechanism"],
        [
            ["Skin Tone Match",
             "First bullet in Step 1 names skin tone and undertone explicitly; "
             "model processes identity before outfit colour."],
            ["Face SSIM",
             "Identity anchoring in Step 1 before styling reduces structural drift."],
            ["Background Uniformity",
             "Step 5 requires clean background 'all the way to the image edges'."],
            ["Face Sharpness",
             "Step 6 instructs 'face razor-sharp in focus'."],
            ["Framing",
             "Step 3 adds '5–10% headroom above the head' for reliable crown inclusion."],
        ],
        styles, col_widths=[4*cm, 13.5*cm],
    )

    # ---- v3 ----
    h2(story, "6.5  Experimental v3 — Directive + Prohibitions", styles)
    metric_table(story,
        ["Attribute", "Value"],
        [
            ["Approximate length",    "~1,400 characters / ~240 words"],
            ["Structure",             "5 headed sections + prohibitions block"],
            ["Lighting specification","3-point studio (key + fill + rim)"],
            ["Skin tone named",       "Yes — first identity bullet"],
            ["Negative prohibitions", "Yes — 6 explicit ✗ DO NOT rules"],
            ["Background edge spec",  "Yes — 'consistent from center to all four edges'"],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story,
        "<b>Key structural changes:</b> Abandons prose/bullet style for a structured "
        "brief with section dividers and a terminal STRICT PROHIBITIONS block. Tests "
        "whether explicit negative constraints (✗ DO NOT) are more reliably honoured "
        "than equivalent positive instructions. Adds a full 3-point studio lighting "
        "specification unique to this version.", styles)

    metric_table(story,
        ["Metric", "Improvement Mechanism"],
        [
            ["Skin Tone Match",
             "First identity bullet; skin tone both positively asserted and "
             "negatively prohibited."],
            ["Face SSIM",
             "'Zero tolerance' framing + dual positive/negative constraints on "
             "facial geometry."],
            ["Exposure Quality",
             "Explicit 3-point lighting with key/fill/rim spec; prohibition on "
             "HDR and cinematic grading."],
            ["Background Uniformity",
             "'Consistent from center to all four edges' targets corner-sampling metric."],
        ],
        styles, col_widths=[4*cm, 13.5*cm],
    )

    # ---- Comparison table ----
    h2(story, "6.6  Prompt Comparison Summary", styles)
    metric_table(story,
        ["Dimension", "Production", "v1", "v2", "v3"],
        [
            ["Identity before outfit",       "✗", "✓", "✓", "✓"],
            ["Skin tone named explicitly",   "✗", "✗", "✓", "✓"],
            ["Hair preservation",            "✗", "✓", "✓", "✓"],
            ["Age preservation",             "✗", "✗", "✓", "✓"],
            ["Background edge uniformity",   "✗", "✗", "✓", "✓"],
            ["Sharpness / focus instruction","✗", "✓", "✓", "✓"],
            ["3-point lighting spec",        "✗", "✗", "✗", "✓"],
            ["Negative prohibition block",   "✗", "✗", "✗", "✓"],
            ["Approx. word count",     "~75", "~160", "~200", "~240"],
        ],
        styles, col_widths=[7*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm],
    )

    # ---- 6.7 Current production prompt: type, pros & cons ----
    h2(story, "6.7  Current Production Prompt — Engineering Type, Pros & Cons", styles)
    body(story,
        "The prompt now shipping in "
        "<font name='Courier'>AiProfileGenerateService::getPrompts()</font> is the Directive + "
        "Prohibitions structure. It is not a single technique but a deliberate stack of several. "
        "Its dominant classification is <b>zero-shot, structured/modular instructional prompting "
        "with heavy constraint (negative) prompting</b>, applied to a text-to-image multimodal "
        "model.", styles)

    h3(story, "Techniques in the stack", styles)
    metric_table(story,
        ["Technique", "Where it appears in the current prompt"],
        [
            ["Modular / compositional (template)",
             "Final string assembled from six reusable blocks (intro, outfit, identity+"
             "background, framing, attire, lighting/quality). Only the outfit clause varies."],
            ["Zero-shot",
             "Pure instructions — no example input/output pairs are supplied to the model."],
            ["Instructional / directive",
             "Command voice with an explicit INPUT / OUTPUT contract "
             "('PROFESSIONAL HEADSHOT DIRECTIVE')."],
            ["Constraint / negative (defining)",
             "A terminal STRICT PROHIBITIONS block of ✗ Do NOT rules, plus the "
             "IDENTITY — ZERO TOLERANCE framing."],
            ["Delimiter / sectioned formatting",
             "━━━ SECTION ━━━ headers segment the prompt into semantic regions."],
            ["Emphasis / repetition (priming)",
             "Identity preservation is stated up front and restated as a prohibition; "
             "CAPS and → arrows weight critical tokens."],
            ["Parameterized variation",
             "limit / offset rotate a 16-item outfit list for controlled diversity from "
             "one template."],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story,
        "<b>One-line label for citation:</b> <i>structured zero-shot instructional prompting "
        "with negative constraints (modular, template-based).</i>", styles)

    h3(story, "Pros", styles)
    bullet(story, [
        "<b>Consistency &amp; reproducibility</b> — fixed blocks make every headshot read as "
        "if from the same studio; only the outfit changes.",
        "<b>Maintainability (DRY)</b> — six isolated components let one lever be tuned without "
        "touching the others.",
        "<b>Controlled diversity</b> — offset/limit rotation produces unique-but-on-brand "
        "variants deterministically.",
        "<b>Strong guardrails</b> — explicit Do NOT prohibitions target known failure modes "
        "(face drift, skin smoothing, added accessories, HDR stylization).",
        "<b>Self-documenting</b> — section delimiters make intent legible to the model and to "
        "future maintainers.",
        "<b>Low cost / low complexity</b> — zero-shot needs no example corpus, fine-tuning, or "
        "retrieval pipeline.",
    ], styles)

    h3(story, "Cons", styles)
    bullet(story, [
        "<b>Verbosity → token cost &amp; dilution</b> — long, repetitive prompts can cause "
        "image models to weight tokens unevenly and average out key instructions.",
        "<b>Negative-prompt unreliability</b> — image models often honour 'Do NOT X' poorly; "
        "naming a concept can raise its chance of appearing. Native negative-prompt fields are "
        "usually more reliable.",
        "<b>No reference grounding for style</b> — identity rides on the single input image "
        "plus words; few-shot or stronger conditioning typically locks identity better than "
        "'ZERO TOLERANCE' phrasing.",
        "<b>Model-coupling / brittleness</b> — wording is tuned to gemini-2.5-flash-image; a "
        "model swap can silently degrade results.",
        "<b>Soft / unenforced parameters</b> — aspectRatio is passed as prompt text only, not "
        "via API config, so the model may ignore it.",
        "<b>Limited semantic diversity</b> — variation is only the outfit string; pose, "
        "expression, and crop are frozen, so outputs can feel templated.",
        "<b>Emphasis overuse</b> — heavy CAPS and symbols have diminishing returns and can hurt "
        "if the model over-anchors on 'shouted' tokens.",
    ], styles)


# ---------------------------------------------------------------------------
# Section 7: Benchmarking Tool
# ---------------------------------------------------------------------------

def build_tool_design(story, styles):
    h1(story, "7. Benchmarking Tool Design", styles)

    h2(story, "7.1  Live Prompt Editor", styles)
    body(story,
        "The original application displayed prompts in a read-only expander. "
        "This was replaced with a live prompt editor — two side-by-side editable "
        "text areas with the following behaviour:", styles)
    bullet(story, [
        "<b>Auto-reload on fingerprint change:</b> A fingerprint string encodes "
        "gender | custom_outfit | experimental_outfit | background_style | exp_version_key. "
        "When any sidebar selection changes, both text areas reload with the updated preset.",
        "<b>Manual override:</b> Within a constant fingerprint, user edits persist "
        "across Streamlit re-runs. Exactly the edited text is sent to the API.",
        "<b>Reset buttons:</b> ↺ Reset restores the text area to the current preset "
        "without changing other state.",
        "<b>Live statistics:</b> Character and word count displayed beneath each editor.",
    ], styles)

    h2(story, "7.2  Experimental Version Selector", styles)
    body(story,
        "A radio widget in the sidebar presents the three experimental versions. "
        "Selecting a version changes the fingerprint, triggers auto-reload of the "
        "experimental text area, and labels the result image header with the version "
        "name for unambiguous identification.", styles)

    h2(story, "7.3  Configurable Model Selector", styles)
    body(story,
        "The Gemini model is now constructed dynamically from a sidebar selectbox. "
        "<font name='Courier'>call_gemini_api</font> accepts "
        "<font name='Courier'>url</font> as an explicit parameter "
        "(defaulting to <font name='Courier'>GEMINI_URL</font> for backwards "
        "compatibility). Both production and experimental calls use the same model, "
        "ensuring fair comparison.", styles)

    h2(story, "7.4  Parallel Generation", styles)
    body(story,
        "Both prompts are submitted concurrently using "
        "<font name='Courier'>ThreadPoolExecutor(max_workers=2)</font>, minimising total "
        "wall-clock time and ensuring that any temporal variation in the Gemini API "
        "(temperature, model load) affects both prompts equally.", styles)


# ---------------------------------------------------------------------------
# Section 8: Results
# ---------------------------------------------------------------------------

def build_results(story, styles):
    h1(story, "8. Results", styles)

    callout_box(story,
        "This section will be populated after benchmark runs are completed. "
        "The framework is ready for data collection.",
        styles, colour=colors.HexColor("#FEF3C7"), border=AMBER)

    h2(story, "8.1  Data Collection Protocol", styles)
    body(story,
        "For statistically meaningful results, each prompt version should be tested with:", styles)
    bullet(story, [
        "Minimum 3–5 different reference photos (diverse skin tones, genders, ages).",
        "At least 3 generations per photo per version, given Gemini's stochastic nature.",
        "Qualitative ratings completed immediately after each generation while the "
        "reference image is visible.",
    ], styles)

    h2(story, "8.2  Expected Results (Hypothesis)", styles)
    metric_table(story,
        ["Metric", "Expected Ranking"],
        [
            ["Face SSIM",            "v3 ≥ v2 > v1 > Production"],
            ["Skin Tone Match",      "v3 ≥ v2 > v1 > Production"],
            ["Face Sharpness",       "v2 ≈ v3 > v1 > Production"],
            ["Background Uniformity","v2 ≈ v3 > v1 > Production"],
            ["Framing Quality",      "v2 ≥ v1 ≈ v3 ≈ Production"],
            ["Exposure Quality",     "v3 > v2 ≈ v1 ≈ Production"],
            ["Overall Score",        "v3 ≥ v2 > v1 > Production"],
        ],
        styles, col_widths=[5*cm, 12.5*cm],
    )
    body(story,
        "<b>Note:</b> Longer prompts are not always better. There is a risk that v3's "
        "structured format (Unicode dividers, ✗ symbols) is less well-handled by the "
        "model than plain prose, which could cause unexpected regressions. "
        "This hypothesis must be validated empirically.", styles)

    h2(story, "8.3  Results Table (to be filled)", styles)
    metric_table(story,
        ["Run", "Reference Photo", "Gender", "Version", "Model",
         "SSIM", "Skin", "Sharp", "BG", "Overall"],
        [["—"] * 10],
        styles,
        col_widths=[1*cm, 3*cm, 2*cm, 2.5*cm, 3.5*cm,
                    1.2*cm, 1.2*cm, 1.2*cm, 1.2*cm, 1.7*cm],
    )


# ---------------------------------------------------------------------------
# Section 9: Recommendations
# ---------------------------------------------------------------------------

def build_recommendations(story, styles):
    h1(story, "9. Recommendations", styles)

    h2(story, "9.1  Immediate", styles)
    bullet(story, [
        "Run the benchmark with 3+ reference photos before making any prompt changes "
        "to production. Never change a production prompt based on visual intuition alone.",
        "Use gemini-2.5-flash-image for all runs in the initial benchmark pass to "
        "ensure model is not a confounding variable.",
        "Rate qualitative scores immediately after generation — recency bias affects "
        "scoring accuracy if ratings are done in batch later.",
    ], styles)

    h2(story, "9.2  Short-Term (pending benchmark results)", styles)
    bullet(story, [
        "If v2 or v3 outperforms production on Face SSIM + Skin Tone Match without "
        "regressing on Framing/Exposure, adopt the winner as the new production prompt "
        "in AiProfileGenerateService.php.",
        "Consider adding skin tone mention to the production prompt as a minimal "
        "low-risk improvement even before full experiment results are available, "
        "since it addresses a clear gap with no downside.",
    ], styles)

    h2(story, "9.3  Medium-Term", styles)
    bullet(story, [
        "Replace Haar cascade with a deep-learning face detector (MTCNN or RetinaFace). "
        "Haar cascade fails on non-frontal faces and profiles.",
        "Add FaceNet / ArcFace cosine similarity as an 8th metric. SSIM measures "
        "structural patterns but is not identity-aware — embedding-based identity "
        "distance is a more principled measure.",
        "Average metrics across 3 generations per prompt to reduce per-run stochasticity. "
        "A single bad generation can skew Overall Score by 5–10 points.",
        "Add CLIP scoring ('professional business headshot' anchor text) as a semantic "
        "quality metric independent of the reference photo.",
    ], styles)

    h2(story, "9.4  Long-Term", styles)
    bullet(story, [
        "Consider prompt personalisation by skin tone range: darker skin tones are "
        "more susceptible to brightening drift by the model.",
        "Evaluate Gemini 2.0 Flash Experimental as a model upgrade candidate using "
        "the configurable model selector added in this work.",
    ], styles)


# ---------------------------------------------------------------------------
# Section 10: Appendix
# ---------------------------------------------------------------------------

# Current production prompt — assembled by AiProfileGenerateService::getPrompts()
# (male subject, first outfit variant; {outfit} substituted per variant).
CURRENT_PROD_PROMPT = """\
PROFESSIONAL HEADSHOT DIRECTIVE

INPUT: Reference photograph of a real person
OUTPUT: Professional {gender} corporate headshot, {outfit}.

IDENTITY — ZERO TOLERANCE FOR CHANGES
The person in the generated image must be the EXACT SAME PERSON as in the
reference photo. Treat the face as a locked, uneditable asset:
  Skin color and undertone: match exactly — same warmth, depth, and tone
  Skin texture: preserve all natural texture, pores, fine lines — no AI smoothing
  Facial geometry: same bone structure, proportions, and all features
  Eyes: same color, shape, spacing, and brow arch
  Hair: same color and style as shown
  Age: no de-aging or aging — keep the subject's natural age

BACKGROUND
Soft neutral grey — clean, uniform, professional studio backdrop.
Completely free of texture, objects, or environmental context.
Background must be consistent from center to all four edges of the frame.

FRAMING & POSE
  Head-to-mid-chest crop — full crown of head with small headroom margin
  Face centered horizontally
  Upright, professional posture — relaxed shoulders, no unnatural tilt

ATTIRE
Garment must be sharp, properly fitted, and wrinkle-free.
Collar and neckline sit naturally against the neck — no gaps or floating fabric.
Neck and shoulder anatomy anatomically correct and proportional.

LIGHTING
3-point studio setup:
  Key light — upper-left at 45°, soft box diffused
  Fill light — right side, softer intensity to open shadows
  Rim / hair light — subtle, from behind, to separate subject from background
Result: even, shadow-minimized illumination; true-to-life color; no blown
highlights on skin.

TECHNICAL OUTPUT
  Photorealistic DSLR photograph — high resolution, no compression artifacts
  85mm portrait lens equivalent at f/2.2 — face tack-sharp, background subtly soft
  No artistic filters, no painterly or HDR effects, no stylization

STRICT PROHIBITIONS
  Do NOT generate a different face — must be recognizable as the reference person
  Do NOT smooth, beautify, or retouch skin
  Do NOT change skin tone, hair color, or eye color
  Do NOT alter facial proportions or make the person look any different
  Do NOT add accessories, props, or background elements not specified
  Do NOT apply cinematic, HDR, or stylized color grading"""

# Legacy production prompt (pre-2026-06) — retained for historical comparison.
PROD_PROMPT = """\
Generate a portrait of a professional {gender} {outfit}.
STRICTLY PRESERVE the subject's original face. The output must look exactly
like the person in the uploaded image. Do not alter facial structure, skin
texture, or expression. The body should be centered with a natural, professional
pose. Background must be a soft, solid, professional ID card style background.
Frame the image from the top of the head to the mid-chest. Ensure the neck and
shoulders are anatomically correct and proportional. The clothing must fit
naturally around the neck/collar area without floating or weird cuts.
PHOTOREALISTIC style. The image must look like a high-end photograph.
No cartoonish, 3D render, or filtered looks. Lighting should be natural studio
lighting."""

V1_PROMPT = """\
You are a professional portrait photographer. Using the uploaded reference photo,
generate a photorealistic headshot portrait with the following specifications:

IDENTITY PRESERVATION (CRITICAL):
- The subject's face must be IDENTICAL to the person in the uploaded image —
  same skin tone, eye color, nose shape, jawline, and every facial feature
- Do NOT alter, enhance, smooth, or modify the face in any way
- Preserve exact skin texture, any facial marks, and natural expression
- Do not change hair color, hair style, or eyebrow shape

SUBJECT & COMPOSITION:
- Professional {gender} portrait
- {outfit}
- Framing: from the crown of the head to the mid-chest, face centered horizontally
- Natural, confident, upright posture — shoulders squared to camera

CLOTHING & ANATOMY:
- Clothing must be sharp, properly fitted, wrinkle-free
- Collar and neckline must sit naturally — no gaps, floating fabric, or distortion
- Neck and shoulders must be anatomically correct and proportional

BACKGROUND:
- {background}, clean professional background (LinkedIn / ID card portrait style)
- No props, no distractions — soft gradient or flat solid color only

PHOTOGRAPHY STYLE:
- Ultra-photorealistic — must look like a real photograph taken in a professional studio
- No artistic filters, no painterly effects, no 3D rendering
- Soft box studio lighting: main light slightly above-left, subtle fill from the right
- Face in sharp focus, background softly diffused (shallow depth of field)
- Color grading: neutral, true-to-life — no heavy warm/cool toning

OUTPUT: A single portrait image matching all specifications above."""

V2_PROMPT = """\
You are processing a real reference photograph to generate a professional corporate
headshot. The face in the reference photo must appear EXACTLY in the output.

STEP 1 — ANCHOR THE IDENTITY (highest priority):
Study every detail of the face in the uploaded photo before generating:
  Skin tone and undertone (warm / cool / neutral) — match precisely
  Skin texture: pores, fine lines, any marks or freckles — do not smooth away
  Eye color, shape, and spacing
  Nose shape, lip shape, jawline, and cheekbone structure
  Hair: exact color, texture, and current style as shown
  Apparent age — do not de-age or age the person
  Ethnicity and all distinguishing features
This face must appear UNCHANGED in the output.

STEP 2 — APPLY PROFESSIONAL STYLING:
Subject: {gender} professional    Attire: {outfit}

STEP 3 — COMPOSITION:
  Framing: crown of head to mid-chest, 5-10% headroom above the head
  Face horizontally centered in frame
  Upright posture, shoulders relaxed, confident neutral expression

STEP 4 — CLOTHING & ANATOMY:
  Clothing crisp, well-tailored, wrinkle-free
  Collar sits flat against neck — no floating fabric, no gaps
  Neck and shoulder anatomy natural and proportional

STEP 5 — BACKGROUND:
  {background} — completely uniform solid or very subtle gradient
  Must be clean all the way to the image edges — no texture or environmental elements

STEP 6 — LIGHTING & FOCUS:
  Key light at 45° upper-left, gentle fill from right
  Even illumination — no harsh chin or nose shadows
  Face razor-sharp in focus; background may have slight depth-of-field softness
  Ultra-photorealistic — indistinguishable from a real studio photograph

OUTPUT: Single portrait image exactly matching the above specifications."""

V3_PROMPT = """\
PROFESSIONAL HEADSHOT DIRECTIVE
INPUT: Reference photograph of a real person
OUTPUT: Professional {gender} corporate headshot

IDENTITY — ZERO TOLERANCE FOR CHANGES
The person in the generated image must be the EXACT SAME PERSON as in the
reference photo. Treat the face as a locked, uneditable asset:
  Skin color and undertone: match exactly — same warmth, depth, and tone
  Skin texture: preserve all natural texture, pores, fine lines — no AI smoothing
  Facial geometry: same bone structure, proportions, and all features
  Eyes: same color, shape, spacing, and brow arch
  Hair: same color and style as shown
  Age: no de-aging or aging — keep the subject's natural age

ATTIRE
{outfit}  |  Garment must be sharp, properly fitted, and wrinkle-free.
Collar and neckline sit naturally — no gaps or floating fabric.

FRAMING & POSE
  Head-to-mid-chest crop — full crown of head with small headroom margin
  Face centered horizontally
  Upright, professional posture — relaxed shoulders, no unnatural tilt

BACKGROUND
{background} — clean, uniform, professional studio backdrop
Completely free of texture, objects, or environmental context.
Background must be consistent from center to all four edges of the frame.

LIGHTING  (3-point studio setup)
  Key light — upper-left at 45°, soft box diffused
  Fill light — right side, softer intensity to open shadows
  Rim / hair light — subtle, from behind, to separate subject from background

TECHNICAL OUTPUT
  Photorealistic DSLR photograph — high resolution, no compression artifacts
  85mm portrait lens equivalent at f/2.2 — face tack-sharp, background soft
  No artistic filters, no painterly or HDR effects, no stylization

STRICT PROHIBITIONS
  Do NOT generate a different face
  Do NOT smooth, beautify, or retouch skin
  Do NOT change skin tone, hair color, or eye color
  Do NOT alter facial proportions
  Do NOT add accessories, props, or background elements not specified
  Do NOT apply cinematic, HDR, or stylized color grading"""


def build_appendix(story, styles):
    h1(story, "10. Appendix — Full Prompt Texts", styles)

    for version, prompt_text in [
        ("A  Production Prompt (Current — Directive + Prohibitions)", CURRENT_PROD_PROMPT),
        ("B  Experimental v1 — Photographer Role", V1_PROMPT),
        ("C  Experimental v2 — Step-by-Step Identity", V2_PROMPT),
        ("D  Experimental v3 — Directive + Prohibitions", V3_PROMPT),
        ("E  Legacy Production Prompt (pre-2026-06)", PROD_PROMPT),
    ]:
        story.append(KeepTogether([
            Paragraph(f"<b>{version}</b>", styles["h2"]),
        ]))
        code_block(story, prompt_text, styles)
        story.append(Spacer(1, 8))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + 8*mm,
        bottomMargin=MARGIN_B + 8*mm,
        title="AI Profile Generator — Prompt Engineering Research Report",
        author="CheckinMe",
        subject="Prompt Engineering and Benchmarking",
    )

    styles = build_styles()
    story  = []

    canvas_cb = ReportCanvas(
        project="CheckinMe AI Profile Generator",
        report_date=datetime.date.today().strftime("%d %B %Y"),
    )

    build_cover(story, styles)
    build_toc(story, styles)
    build_executive_summary(story, styles)
    story.append(PageBreak())
    build_project_context(story, styles)
    story.append(PageBreak())
    build_problem_statement(story, styles)
    story.append(PageBreak())
    build_architecture(story, styles)
    story.append(PageBreak())
    build_methodology(story, styles)
    story.append(PageBreak())
    build_prompt_engineering(story, styles)
    story.append(PageBreak())
    build_tool_design(story, styles)
    story.append(PageBreak())
    build_results(story, styles)
    story.append(PageBreak())
    build_recommendations(story, styles)
    story.append(PageBreak())
    build_appendix(story, styles)

    doc.build(story, onFirstPage=canvas_cb, onLaterPages=canvas_cb)
    print(f"Report saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_pdf()
