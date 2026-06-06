"""
generate_report.py
Generates the CheckinMe AI Profile Generator — Prompt Engineering Report as a
professional PDF using ReportLab Platypus.

This is the simplified report: methodology, Google Gemini implementation, image
generation model performance, and a before/after comparison of the original vs the
latest production prompt. No experimental variants, no source-code listings.

Usage:
    /opt/anaconda3/bin/python3 generate_report.py
Output:
    PROMPT_ENGINEERING_REPORT.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
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

        # ---- Code / prompt text ----
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

        # ---- Verdict / callout ----
        "callout": _s("callout",
            fontName="Helvetica-Bold", fontSize=9.5, leading=14,
            textColor=NAVY, leftIndent=12, rightIndent=12,
            spaceBefore=6, spaceAfter=6),

        # ---- TOC ----
        "toc": _s("toc",
            fontName="Helvetica", fontSize=9.5, leading=15,
            textColor=DARKGREY, leftIndent=0, spaceAfter=1),

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
                               "Prompt Engineering Report")

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
    # Split into lines to preserve formatting (used for prompt texts)
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
    avail_w = PAGE_W - MARGIN_L - MARGIN_R

    header_block = Table(
        [[Paragraph("", styles["cover_title"])]],
        colWidths=[avail_w], rowHeights=[0.3*cm],
    )
    header_block.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), NAVY)]))
    story.append(header_block)
    story.append(Spacer(1, 0))

    cover_content = [
        [Paragraph("AI Profile Generator", styles["cover_title"])],
        [Paragraph("Prompt Engineering Report", styles["cover_subtitle"])],
        [Paragraph("&nbsp;", styles["cover_meta"])],
        [Paragraph("Project: CheckinMe", styles["cover_meta"])],
        [Paragraph("Production model: Google Gemini 2.5 Flash Image "
                   "(nicknamed &quot;nano banana&quot;)", styles["cover_meta"])],
        [Paragraph("Scope: Methodology, Gemini implementation, model performance &amp; "
                   "prompt comparison", styles["cover_meta"])],
        [Paragraph(f"Date: {datetime.date.today().strftime('%d %B %Y')}", styles["cover_meta"])],
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

    accent = Table([[""]], colWidths=[avail_w], rowHeights=[6])
    accent.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), GREEN)]))
    story.append(accent)
    story.append(Spacer(1, 16))

    callout_box(story,
        "CheckinMe's AI Profile Generator turns a single reference photo into professional "
        "corporate headshots using Google Gemini image generation. This report covers the "
        "evaluation methodology, how generation is implemented with Gemini, how the available "
        "image models perform, and a before/after comparison of the original and the latest "
        "production & experimental prompt.",
        styles)

    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Table of Contents
# ---------------------------------------------------------------------------

def build_toc(story, styles):
    h1(story, "Table of Contents", styles)
    story.append(Spacer(1, 6))

    toc_items = [
        ("1.", "Overview"),
        ("2.", "Project Context"),
        ("3.", "Methodology"),
        ("4.", "Implementation with Google Gemini"),
        ("5.", "Image Generation Model Performance"),
        ("6.", "Prompt Comparison — Original vs Latest"),
        ("7.", "Appendix — Full Prompt Texts"),
    ]

    for num, title in toc_items:
        story.append(Paragraph(f"<b>{num}</b>  {title}", styles["toc"]))

    story.append(PageBreak())


# ---------------------------------------------------------------------------
# Section 1: Overview
# ---------------------------------------------------------------------------

def build_overview(story, styles):
    h1(story, "1. Overview", styles)

    body(story,
        "CheckinMe's AI Profile Generator turns a single user-supplied reference photo into "
        "a set of professional corporate headshots with varied attire. The whole product "
        "depends on one thing above all: <b>face identity preservation</b> — the generated "
        "headshot must clearly look like the same person in the reference photo.", styles)

    body(story, "This report covers three things, in plain terms:", styles)
    bullet(story, [
        "<b>The methodology</b> used to judge whether a generated headshot is good.",
        "<b>How the generation is implemented</b> with Google Gemini's image generation service.",
        "<b>A before/after comparison</b> of the original production prompt against the "
        "current (latest) prompt now used in production.",
    ], styles)


# ---------------------------------------------------------------------------
# Section 2: Project Context
# ---------------------------------------------------------------------------

def build_project_context(story, styles):
    h1(story, "2. Project Context", styles)

    body(story,
        "When a user requests headshots, the production service "
        "(<font name='Courier'>AiProfileGenerateService.php</font>):", styles)
    bullet(story, [
        "Takes a reference photo, the subject's gender, and how many headshots to produce.",
        "Picks a set of outfit descriptions from a fixed catalogue (16 per gender), rotating "
        "through them so each headshot wears something different.",
        "Builds one text prompt per outfit and sends it, together with the reference photo, "
        "to Google Gemini's image generation endpoint.",
        "Receives a generated image back and returns it to the app.",
    ], styles)

    body(story,
        "All outfits are conservative corporate styles (suits, blazers, formal blouses) "
        "chosen deliberately to avoid distortion around the neckline, a common failure point "
        "for AI portrait generators.", styles)

    metric_table(story,
        ["Gender", "Outfit Pool", "Style Range"],
        [
            ["Male",   "16",
             "Black / navy / charcoal / grey suits with varied shirt and tie combinations"],
            ["Female", "16",
             "Black / navy / grey / dark blazers over white and light-coloured blouses"],
        ],
        styles,
        col_widths=[2.5*cm, 2.5*cm, 12.5*cm],
    )


# ---------------------------------------------------------------------------
# Section 3: Methodology
# ---------------------------------------------------------------------------

def build_methodology(story, styles):
    h1(story, "3. Methodology", styles)

    body(story,
        "Each generated headshot is scored two ways — automatically (quantitative) and by a "
        "human reviewer (qualitative) — and the two are blended into one final score.", styles)

    h2(story, "3.1  Quantitative metrics", styles)
    body(story,
        "Seven measurements are taken on every generated image and compared against the "
        "reference photo. Each produces a 0–100 score, and they are combined with fixed "
        "weights.", styles)
    metric_table(story,
        ["Metric", "Weight", "What it checks"],
        [
            ["Face structural similarity", "25%", "Is it structurally the same face? (identity drift)"],
            ["Skin tone match",            "20%", "Did the complexion / undertone shift?"],
            ["Face sharpness",             "20%", "Is the face crisp, or blurred / over-smoothed?"],
            ["Background uniformity",      "15%", "Is the backdrop clean and even to the corners?"],
            ["Framing quality",            "10%", "Is the crop right — not too close, not too far?"],
            ["Face centering",             " 5%", "Is the face centred horizontally?"],
            ["Exposure quality",           " 5%", "Is it well-lit, not over- or under-exposed?"],
        ],
        styles,
        col_widths=[4.5*cm, 1.8*cm, 11.2*cm],
    )
    body(story,
        "<b>Overall quantitative score</b> = the weighted average of the seven metrics above.",
        styles)

    h2(story, "3.2  Qualitative assessment", styles)
    body(story,
        "A human reviewer rates five questions from 1 to 5 stars while looking at the "
        "reference photo side by side with the result:", styles)
    metric_table(story,
        ["Criterion", "Question"],
        [
            ["Face resemblance",   "Does the face look exactly like the person in the reference photo?"],
            ["Professional look",  "Does it look like a real professional headshot?"],
            ["Clothing quality",   "Does the clothing look natural and well-fitted?"],
            ["Background quality", "Is the background clean, solid, and professional?"],
            ["Overall preference", "Overall, how satisfied are you with this image?"],
        ],
        styles,
        col_widths=[4*cm, 13.5*cm],
    )
    body(story,
        "<b>Qualitative score</b> = the average star rating, scaled to 0–100.", styles)

    h2(story, "3.3  Final combined score", styles)
    callout_box(story,
        "Final score = 60% quantitative + 40% qualitative.",
        styles, colour=LIGHTGREY, border=GREEN)
    body(story,
        "When two prompts are compared, the one scoring at least 2 points higher wins; "
        "a gap of under 2 points is treated as a tie.", styles)


# ---------------------------------------------------------------------------
# Section 4: Implementation with Google Gemini
# ---------------------------------------------------------------------------

def build_implementation(story, styles):
    h1(story, "4. Implementation with Google Gemini", styles)

    body(story,
        "Headshots are generated through <b>Google Gemini's image generation service</b>. "
        "The implementation is deliberately simple: there is no fine-tuning, no training "
        "data, and no separate model to host. Everything is driven by the prompt plus the "
        "reference photo.", styles)

    h2(story, "How a single headshot is generated", styles)
    bullet(story, [
        "The reference photo is read and attached to the request alongside the text prompt.",
        "The request is sent to the Gemini image generation endpoint for the chosen model.",
        "Gemini returns the generated headshot image, which is passed back to the app.",
    ], styles)

    body(story,
        "The model used is configurable. Production runs on <b>Gemini 2.5 Flash Image</b>, "
        "and the benchmarking tool can point at a different model to compare results, without "
        "any code changes. Both the original and latest prompts are always run against the "
        "<b>same model</b> so the comparison stays fair.", styles)

    h2(story, "Practical notes on working with the Gemini image service", styles)
    bullet(story, [
        "<b>The reference photo does the heavy lifting for identity.</b> Identity preservation "
        "comes primarily from the attached photo; the prompt's job is to reinforce it and "
        "control everything else (attire, framing, background, lighting).",
        "<b>Instructions are text, not hard settings.</b> Things like aspect ratio and "
        "&quot;don't do X&quot; are requests in the prompt, not enforced parameters, so the "
        "model can occasionally ignore them. Wording matters.",
        "<b>Output varies between runs.</b> The same prompt can produce slightly different "
        "images, so judging a prompt reliably means generating several times rather than once.",
    ], styles)


# ---------------------------------------------------------------------------
# Section 5: Image Generation Model Performance
# ---------------------------------------------------------------------------

def build_model_performance(story, styles):
    h1(story, "5. Image Generation Model Performance", styles)

    body(story,
        "These are qualitative, observed characteristics of the Gemini image models available "
        "for this pipeline. Formal benchmark numbers will be added once full evaluation runs "
        "are complete; the descriptions below reflect how each model behaves on the headshot "
        "task.", styles)

    h2(story, "Gemini 2.5 Flash Image — &quot;nano banana&quot;", styles)
    body(story,
        "This is Google's current image generation and editing model, nicknamed "
        "<b>&quot;nano banana&quot;</b> — it is the same model as "
        "<font name='Courier'>gemini-2.5-flash-image</font>, not a separate one. It is the "
        "model used in production.", styles)
    bullet(story, [
        "<b>Identity preservation:</b> the strongest of the available options. It holds a "
        "subject's face, skin tone, and features well while changing clothing — exactly what "
        "this product needs.",
        "<b>Photorealism:</b> produces clean, realistic studio-style headshots with good "
        "lighting and sharp faces.",
        "<b>Editing behaviour:</b> good at &quot;keep the person, change the outfit / "
        "background&quot; style edits, which is the core operation here.",
        "<b>Trade-offs:</b> can still smooth or &quot;beautify&quot; skin if not explicitly "
        "told not to, and is more expensive per image than the older experimental model. This "
        "is why the prompt includes explicit instructions against smoothing and altering the face.",
    ], styles)

    h2(story, "Gemini 2.5 Pro — comparison baseline", styles)
    body(story,
        "<font name='Courier'>gemini-2.5-pro</font> is Google's high-end reasoning and "
        "multimodal model. It is excellent at understanding complex instructions, but it is a "
        "<b>general-purpose</b> model rather than one purpose-built for image generation and "
        "editing. It was tested as the comparison baseline for this task.", styles)
    bullet(story, [
        "<b>Identity preservation:</b> less consistent for the &quot;keep the exact person, "
        "change the outfit&quot; edit than the dedicated Flash Image model. As a "
        "general-purpose model it does not hold the subject's face as reliably across "
        "generations.",
        "<b>Photorealism:</b> capable, but not specialised for high-fidelity portrait image "
        "output the way Flash Image is.",
        "<b>Cost &amp; speed:</b> heavier, slower, and more expensive per image — a poor fit "
        "for a feature that generates several headshots per request.",
        "<b>Use:</b> a reasonable point of comparison, but <b>not the right tool</b> for "
        "identity-critical headshot generation at scale.",
    ], styles)

    h2(story, "Summary", styles)
    metric_table(story,
        ["Model", "Built for Image Gen", "Identity", "Speed / Cost", "Best for Task?"],
        [
            ["Gemini 2.5 Flash Image (nano banana)", "Yes — purpose-built",
             "Strong", "Fast / lower cost", "Yes"],
            ["Gemini 2.5 Pro", "No — general-purpose",
             "Less consistent", "Slower / higher cost", "No — baseline only"],
        ],
        styles,
        col_widths=[5*cm, 3.6*cm, 2.8*cm, 3*cm, 3.1*cm],
    )

    h2(story, "Decision: why Gemini 2.5 Flash Image is the best fit", styles)
    body(story,
        "After testing both, <b>Gemini 2.5 Flash Image (nano banana) is the best selection for "
        "this task</b>, for three reasons:", styles)
    bullet(story, [
        "<b>It is purpose-built for image generation and editing.</b> This task is "
        "fundamentally an image edit — &quot;keep this exact person, change their clothing and "
        "background.&quot; Flash Image is designed for exactly that, whereas Gemini 2.5 Pro is "
        "a general reasoning model whose image output is a secondary capability.",
        "<b>It preserves identity more reliably.</b> Identity preservation is the product's "
        "single most important requirement, and Flash Image holds the subject's face, skin "
        "tone, and features more consistently across generations than 2.5 Pro.",
        "<b>It is faster and cheaper at scale.</b> Each request produces several headshots, so "
        "a lighter, lower-cost-per-image model that doesn't sacrifice quality is the correct "
        "production choice. 2.5 Pro is heavier and more expensive without a quality advantage "
        "on this task.",
    ], styles)
    callout_box(story,
        "<b>Takeaway:</b> the choice of image model matters as much as the prompt. For "
        "identity-critical, high-volume headshot generation, the specialised Gemini 2.5 Flash "
        "Image model is the right production choice over the general-purpose Gemini 2.5 Pro.",
        styles, colour=LIGHTGREY, border=GREEN)


# ---------------------------------------------------------------------------
# Section 6: Prompt Comparison — Original vs Latest
# ---------------------------------------------------------------------------

def build_prompt_comparison(story, styles):
    h1(story, "6. Prompt Comparison — Original vs Latest", styles)

    body(story,
        "The production prompt was rewritten. Below is the before/after. Full text of both "
        "prompts is in the Appendix.", styles)

    h2(story, "The original prompt (before)", styles)
    body(story,
        "A short, single-paragraph instruction. It worked, but it had three weaknesses:", styles)
    bullet(story, [
        "<b>Outfit came first, identity second.</b> It opened by describing the outfit, "
        "implicitly signalling that generating clothing was the main task and preserving the "
        "face was a secondary constraint.",
        "<b>No mention of skin tone.</b> It asked to preserve &quot;facial structure, skin "
        "texture, and expression&quot; but never named skin colour or undertone — a gap, "
        "since skin tone shift is a common and noticeable failure.",
        "<b>Vague background.</b> &quot;ID card style background&quot; is ambiguous; it didn't "
        "ask for the backdrop to stay clean all the way to the edges of the frame.",
    ], styles)

    h2(story, "The latest prompt (after)", styles)
    body(story,
        "A structured brief organised into labelled sections, ending with an explicit list of "
        "prohibitions. It fixes all three weaknesses above and adds clearer lighting and "
        "quality direction.", styles)
    bullet(story, [
        "<b>Identity first, and stated as non-negotiable.</b> It leads with an &quot;identity "
        "— zero tolerance for changes&quot; block that names skin colour and undertone, skin "
        "texture, facial geometry, eyes, hair, and age explicitly.",
        "<b>Explicit &quot;do not&quot; list.</b> A closing prohibitions block spells out what "
        "the model must not do (generate a different face, smooth or beautify skin, change "
        "skin/hair/eye colour, add props, apply HDR/cinematic grading).",
        "<b>Clean, edge-to-edge background.</b> The background section requires consistency "
        "&quot;from centre to all four edges of the frame.&quot;",
        "<b>Defined lighting and output.</b> Adds a 3-point studio lighting description and a "
        "photorealistic DSLR output spec for more consistent, professional results.",
    ], styles)

    h2(story, "What changed, at a glance", styles)
    metric_table(story,
        ["Aspect", "Original Prompt", "Latest Prompt"],
        [
            ["Identity stated before outfit", "No", "Yes"],
            ["Skin tone / undertone named",   "No", "Yes"],
            ["Hair &amp; age preservation",   "No", "Yes"],
            ["Background clean to the edges",  "No", "Yes"],
            ["Explicit &quot;do not&quot; prohibitions", "No", "Yes"],
            ["Defined studio lighting",        "No", "Yes"],
            ["Length",  "Short (~75 words)", "Longer, structured (~240 words)"],
        ],
        styles,
        col_widths=[6.5*cm, 5.5*cm, 5.5*cm],
    )
    callout_box(story,
        "<b>Note:</b> longer is not automatically better. The latest prompt is more explicit "
        "and more consistent, but it is also more verbose, and image models can weight long "
        "instructions unevenly. The methodology in Section 3 exists precisely so prompt "
        "changes are judged on measured results rather than intuition.",
        styles, colour=colors.HexColor("#FEF3C7"), border=AMBER)


# ---------------------------------------------------------------------------
# Section 7: Appendix — Full Prompt Texts
# ---------------------------------------------------------------------------

ORIGINAL_PROMPT = """\
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

LATEST_PROMPT = """\
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


def build_appendix(story, styles):
    h1(story, "7. Appendix — Full Prompt Texts", styles)

    for title, prompt_text in [
        ("A.  Original prompt (before)", ORIGINAL_PROMPT),
        ("B.  Latest prompt (after — current production)", LATEST_PROMPT),
    ]:
        story.append(KeepTogether([Paragraph(f"<b>{title}</b>", styles["h2"])]))
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
        title="AI Profile Generator — Prompt Engineering Report",
        author="CheckinMe",
        subject="Prompt Engineering and Image Generation",
    )

    styles = build_styles()
    story  = []

    canvas_cb = ReportCanvas(
        project="CheckinMe AI Profile Generator",
        report_date=datetime.date.today().strftime("%d %B %Y"),
    )

    build_cover(story, styles)
    build_toc(story, styles)
    build_overview(story, styles)
    story.append(PageBreak())
    build_project_context(story, styles)
    story.append(PageBreak())
    build_methodology(story, styles)
    story.append(PageBreak())
    build_implementation(story, styles)
    story.append(PageBreak())
    build_model_performance(story, styles)
    story.append(PageBreak())
    build_prompt_comparison(story, styles)
    story.append(PageBreak())
    build_appendix(story, styles)

    doc.build(story, onFirstPage=canvas_cb, onLaterPages=canvas_cb)
    print(f"Report saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_pdf()
