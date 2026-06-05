# AI Profile Generator — Prompt Engineering Research Report

**Project:** CheckinMe AI Profile Generator  
**Scope:** Prompt design, comparative benchmarking framework, and tooling  
**Model:** Google Gemini 2.5 Flash Image (configurable)  
**Date:** 2026-06-05 (rev. 2 — reflects current production prompt)  
**Status:** Directive + Prohibitions variant adopted into production; benchmarking ongoing

---

## Revision Note — 2026-06-05

Since rev. 1 (2026-05-08), the **Directive + Prohibitions** structure originally
introduced as experimental **v3** has been promoted to the **live production prompt**
in `AiProfileGenerateService.php`. The earlier "ID card style" baseline described in
rev. 1 is now the *legacy* prompt and is retained for historical comparison in
[Appendix E](#e-legacy-production-prompt-pre-202606).

Changes in this revision:

- Production prompt is now assembled from six modular components in `getPrompts()`
  (gender intro, outfit variant, identity/background block, framing, attire, lighting/quality).
- The three structural weaknesses identified in §3.3 (late identity anchoring, no skin-tone
  instruction, ambiguous background) are **resolved** by the current production prompt.
- New [§6.7](#67-current-production-prompt--engineering-type-pros--cons) classifies the
  prompt-engineering *type* of the current production prompt and documents its pros and cons.
- [Appendix A](#a-production-prompt-current--directive--prohibitions) now contains the
  current production prompt text.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Context](#2-project-context)
3. [Problem Statement](#3-problem-statement)
4. [Technical Architecture](#4-technical-architecture)
5. [Evaluation Methodology](#5-evaluation-methodology)
6. [Prompt Engineering Analysis](#6-prompt-engineering-analysis)
7. [Benchmarking Tool Design](#7-benchmarking-tool-design)
8. [Results](#8-results)
9. [Recommendations](#9-recommendations)
10. [Appendix — Full Prompt Texts](#10-appendix--full-prompt-texts)

---

## 1. Executive Summary

CheckinMe's AI Profile Generator uses Google Gemini to transform a user-supplied reference photograph into a set of professional headshots with varied attire. The primary quality requirement — and the most common failure mode — is **face identity preservation**: the generated image must be recognisably the same person as in the input photo.

This report documents a structured prompt engineering effort to improve generation quality across four measurable dimensions: face structural similarity, skin tone fidelity, image sharpness, and background uniformity. Four prompt versions were designed (one production baseline and three experimental variants), and a Python/Streamlit benchmarking application was built to evaluate them against a seven-metric quantitative framework augmented by human qualitative assessment.

Key contributions of this work:

- Identification of three structural weaknesses in the production prompt.
- Design of three experimental prompt variants, each addressing a different hypothesis about model instruction following.
- A reproducible benchmarking tool supporting side-by-side visual comparison, automated metric computation, and human rating capture.
- A configurable model selector enabling cross-model comparisons without code changes.

**Outcome (as of this revision):** The **Directive + Prohibitions** variant (formerly
experimental v3) has been adopted as the production prompt. It pairs strong positive
identity anchoring with an explicit negative-constraint block and a modular, sectioned
layout. See [§6.7](#67-current-production-prompt--engineering-type-pros--cons) for the
prompt-engineering classification and a candid pros/cons assessment of this approach.

---

## 2. Project Context

### 2.1 System Overview

The production generation pipeline is implemented in `AiProfileGenerateService.php` (Laravel). When a user requests headshots, the service:

1. Accepts a reference image path, gender, quantity (`limit`), and rotation offset.
2. Selects `limit` outfit descriptions from a pool of 16 per gender, applying the offset as a circular rotation.
3. Constructs one text prompt per outfit.
4. Calls the Gemini multimodal endpoint (`gemini-2.5-flash-image:generateContent`) with the prompt and the base64-encoded reference image.
5. Extracts the `inlineData.data` field from the API response and returns it as a base64 PNG.

In non-production environments the service short-circuits and returns random existing media URLs to avoid API cost during development.

### 2.2 Outfit Catalogue

| Gender | Pool size | Style range |
|--------|-----------|-------------|
| Male   | 16        | Black/navy/charcoal/grey suits with varied shirt and tie combinations |
| Female | 16        | Black/navy/grey/dark blazers over white and light-coloured blouses |

All outfits are conservative corporate styles deliberately selected to minimise the risk of anatomical distortion at the neckline (a known failure mode of AI portrait generators).

---

## 3. Problem Statement

### 3.1 Primary Failure Mode: Identity Drift

When a generative vision model is instructed to re-dress a subject, it faces a fundamental tension: it must synthesise new clothing while holding the face constant. Without sufficiently strong identity anchoring instructions, models tend to:

- Smooth or "beautify" skin texture, altering the perceived person.
- Shift skin tone slightly warm or cool depending on the chosen outfit's colour temperature.
- Subtly reshape the nose, jaw, or eye area to fit a "professional" archetype.
- Alter hair style or colour.

The combined effect is a headshot that looks professional but is not recognisably the same individual — a product failure.

### 3.2 Secondary Failure Modes

| Failure mode | Visible symptom | Affected metric |
|---|---|---|
| Skin tone drift | Complexion appears lighter/darker or different undertone | Skin Tone Match (20%) |
| Over-smoothing | Skin looks plastic or AI-generated | Face SSIM (25%), Face Sharpness (20%) |
| Framing errors | Head cropped, or too much torso shown | Framing Quality (10%) |
| Background noise | Gradient, texture, or vignette at corners | Background Uniformity (15%) |
| Anatomical distortion | Floating collar, misaligned neck | Qualitative — Clothing Quality |

### 3.3 Structural Weaknesses in the Legacy Production Prompt

> **Resolved in current production (2026-06-05).** The three issues below were identified
> in the *legacy* production prompt ([Appendix E](#e-legacy-production-prompt-pre-202606)).
> All three are addressed by the current Directive + Prohibitions production prompt
> ([Appendix A](#a-production-prompt-current--directive--prohibitions)): identity is anchored
> immediately after the outfit clause, skin colour and undertone are named explicitly and
> reinforced by a prohibition, and the background block requires consistency "from center to
> all four edges of the frame." This section is retained to document the original rationale.

Analysis of the legacy `build_production_prompt()` revealed three structural issues:

**Issue 1 — Late identity anchoring.**  
The production prompt opens with outfit instruction (`Generate a portrait of a professional [gender] [outfit]`) before stating face preservation requirements. This ordering implicitly signals that the primary task is outfit generation, with identity preservation as a constraint. Multimodal LLMs tend to weight earlier instructions more heavily during synthesis.

**Issue 2 — Absent skin tone instruction.**  
The phrase "Do not alter facial structure, skin texture, or expression" does not mention skin colour or undertone explicitly. Skin tone shift is measured at 20% of the quantitative score, making this a high-impact omission.

**Issue 3 — Ambiguous background specification.**  
"A soft, solid, professional ID card style background" is semantically underspecified. The benchmark measures background uniformity by sampling pixel variance in the four image corners. Any gradient or subtle texture that extends to the corners penalises the score; the production prompt does not instruct the model to maintain consistency to the image edges.

---

## 4. Technical Architecture

### 4.1 Production Service (`AiProfileGenerateService.php`)

```
User request
    │
    ├── getPrompts(gender, limit, offset, aspectRatio)
    │       ├── Selects outfits from $outfits[gender]
    │       ├── Applies circular offset rotation
    │       └── Assembles prompt string from $commonIntro + $style + $commonFeatures
    │                                       + $framingFix + $neckFix + $imageQuality
    │
    └── foreach $prompts as $prompt
            └── POST /v1beta/models/gemini-2.5-flash-image:generateContent
                    ├── parts[0]: text prompt
                    └── parts[1]: inline_data (base64 PNG/JPEG)
                    → returns base64 image → stored / returned to controller
```

### 4.2 Benchmarking Application (`benchmark_app.py`)

```
Streamlit UI
    │
    ├── Sidebar
    │       ├── Gemini API Key
    │       ├── Model selector (dynamic URL construction)
    │       ├── Gender selector
    │       ├── Outfit builder (suit colour + shirt + tie / blazer + blouse + accessories)
    │       ├── Background style selector
    │       └── Experimental prompt version selector (v1 / v2 / v3)
    │
    ├── Prompt Editor (main area)
    │       ├── Production text area — editable, ↺ Reset button, live char count
    │       └── Experimental text area — editable, ↺ Reset button, live char count
    │               • Auto-reloads when version / outfit / background changes (fingerprint)
    │               • Manual edits persist until fingerprint changes or Reset pressed
    │
    ├── Generate & Compare (button)
    │       └── ThreadPoolExecutor(max_workers=2)
    │               ├── call_gemini_api(prod_prompt, gemini_url)
    │               └── call_gemini_api(exp_prompt, gemini_url)
    │
    ├── Side-by-Side Image Comparison
    │
    ├── Quantitative Metrics (auto-computed via benchmark_metrics.py)
    │       └── bm.compute_all(ref_img, generated_img) → dict of 8 scores
    │
    └── Qualitative Rating Panel (5 criteria × 1–5 stars)
            └── Final Combined Score = 60% Quantitative + 40% Qualitative
```

### 4.3 Model URL Architecture

The Gemini model endpoint follows the pattern:

```
https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent
```

The model ID was previously hardcoded as the module-level constant `GEMINI_URL`. It is now constructed dynamically from a sidebar selectbox, enabling cross-model comparison (e.g., `gemini-2.5-flash-image` vs `gemini-2.0-flash-exp-image-generation`) without modifying source code. A custom model ID text input is also available for unreleased or preview models.

---

## 5. Evaluation Methodology

### 5.1 Quantitative Metrics

All metrics produce scores on a 0–100 scale. They are combined into an **Overall Quantitative Score** via a fixed weighted average.

| Metric | Weight | Library | Method | Primary failure it detects |
|---|---|---|---|---|
| Face SSIM | 25% | scikit-image | Structural Similarity Index on 96×96 grayscale face crop | Identity drift — structural |
| Skin Tone Match | 20% | numpy | Pearson correlation of R+G channel histograms (32 bins) on face crop | Skin colour / undertone shift |
| Face Sharpness | 20% | opencv | Laplacian variance on face crop (threshold 1500) | Blur, over-smoothing |
| Background Uniformity | 15% | numpy | Std dev of RGB pixels sampled from four corner patches | Gradients, textures, vignettes |
| Framing Quality | 10% | opencv | Face height / image height ratio vs ideal range [0.30, 0.65] | Zoom too close or too far |
| Face Centering | 5% | opencv | Horizontal centroid offset normalised to image width | Off-centre composition |
| Exposure Quality | 5% | numpy | Mean luminance vs ideal studio range [90, 175] | Over/underexposure |

**Overall Quantitative = Σ (metric × weight)**

### 5.2 Face Detection

Pre-processing for SSIM, Skin Tone, Sharpness, Framing, and Centering depends on locating the face. The implementation uses OpenCV's Haar cascade (`haarcascade_frontalface_default.xml`) with `scaleFactor=1.1`, `minNeighbors=5`, `minSize=(40,40)`. If detection fails, affected metrics return a neutral score of 50 (or 0 for Framing/Centering).

### 5.3 Qualitative Assessment

Five criteria rated 1–5 by a human evaluator:

| Criterion | Question |
|---|---|
| Face Resemblance | Does the face look exactly like the person in the reference photo? |
| Professional Look | Does the overall image look like a professional headshot? |
| Clothing Quality | Does the clothing look natural, well-fitted, and realistic? |
| Background Quality | Is the background clean, solid, and professional? |
| Overall Preference | Overall, how satisfied are you with this image? |

```
Qualitative Score = (mean star rating / 5) × 100
```

### 5.4 Final Combined Score

```
Final = 0.60 × Quantitative_Overall + 0.40 × Qualitative_Average
```

**Verdict thresholds:**

| Condition | Verdict |
|---|---|
| `\|Exp − Prod\| < 2` | Tie |
| `Exp − Prod ≥ 2` | Experimental wins |
| `Prod − Exp ≥ 2` | Production wins |

---

## 6. Prompt Engineering Analysis

### 6.1 Design Philosophy

Each experimental version tests a distinct hypothesis about how Gemini processes multimodal instructions:

| Version | Hypothesis | Status |
|---|---|---|
| Legacy Production | Baseline: implicit identity constraint appended after outfit instruction. | Retired (see Appendix E) |
| v1 — Photographer Role | Assigning a domain expert persona improves instruction compliance for professional outputs. | Experimental |
| v2 — Step-by-Step Identity | Sequential processing steps with explicit metric-aligned sub-instructions improve targeted output quality. | Experimental |
| v3 — Directive + Prohibitions | Explicit negative constraints (`✗ DO NOT`) are more reliably honoured than equivalent positive instructions. | **Adopted to production** |

### 6.2 Legacy Production Prompt (Retired Baseline)

> This was the production prompt at rev. 1. It has since been replaced by the Directive +
> Prohibitions structure (see [§6.5](#65-experimental-v3--directive--prohibitions) and
> [§6.7](#67-current-production-prompt--engineering-type-pros--cons)). Full text in
> [Appendix E](#e-legacy-production-prompt-pre-202606).

**Approximate length:** ~430 characters / ~75 words

**Template structure:**
```
Generate a portrait of a professional {gender} {outfit}.
{face preservation block}
{framing instruction}
{neck/anatomy instruction}
{photorealism instruction}
```

**Strengths:**
- Concise; low token overhead.
- Includes neck/anatomy fix and framing instruction.

**Weaknesses:**
- Outfit is the first clause — identity anchoring is secondary.
- No explicit skin tone preservation.
- Background described as "ID card style" — semantically ambiguous for corner uniformity.
- No instruction about hair, age, or ethnic features.
- All instructions written as positive constraints; no negative prohibition list.

**Expected benchmark ceiling:**  
Strong on Framing (explicit instruction) and Exposure (standard studio lighting). Vulnerable on Face SSIM and Skin Tone Match due to absent skin tone instruction and late identity anchoring.

---

### 6.3 Experimental v1 — Photographer Role

**Approximate length:** ~900 characters / ~160 words

**Key structural change:** Assigns the model a domain expert role (`You are a professional portrait photographer`) before any task specification. Role-prompting has been shown in LLM literature to shift model behaviour toward domain-appropriate defaults.

**Identity block:**
```
IDENTITY PRESERVATION (CRITICAL):
- The subject's face must be IDENTICAL … same skin tone, eye color, nose shape, jawline…
- Do NOT alter, enhance, smooth, or modify the face in any way
- Preserve exact skin texture, any facial marks, and natural expression
- Do not change hair color, hair style, or eyebrow shape
```

**Improvements over production:**
- Identity section now appears before outfit description.
- Adds hair and eyebrow preservation.
- Background instruction includes "flat solid color only" (slightly tighter than production).
- Adds shallow depth-of-field instruction (sharpness signal).

**Remaining gaps:**
- Skin tone and undertone still not called out by name.
- Background uniformity to the image edges not explicitly required.
- No negative prohibition block.

---

### 6.4 Experimental v2 — Step-by-Step Identity

**Approximate length:** ~1,150 characters / ~200 words

**Key structural change:** Replaces free-form instruction blocks with numbered processing steps, explicitly sequencing the model to *anchor identity first* before applying any styling.

**Step structure:**
```
STEP 1 — ANCHOR THE IDENTITY (highest priority)
  • Skin tone and undertone (warm / cool / neutral) — match precisely   ← direct skin tone metric alignment
  • Skin texture: pores, fine lines, any marks or freckles — do not smooth away
  • Eye color, shape, and spacing
  • … (full feature list)
This face must appear UNCHANGED in the output.

STEP 2 — APPLY PROFESSIONAL STYLING: {gender}, {outfit}
STEP 3 — COMPOSITION: framing, centering, posture
STEP 4 — CLOTHING & ANATOMY: fit, collar, neck
STEP 5 — BACKGROUND: uniform, clean to image edges   ← edge uniformity aligned with metric
STEP 6 — LIGHTING & FOCUS: sharp face, soft background   ← sharpness signal
```

**Targeted metric improvements:**

| Metric | Mechanism |
|---|---|
| Skin Tone Match (+) | First bullet in Step 1 names skin tone and undertone explicitly; model processes identity before outfit colour. |
| Face SSIM (+) | Identity anchoring in Step 1 before styling reduces structural drift. |
| Background Uniformity (+) | Step 5 requires clean background "all the way to the image edges" — directly addresses corner sampling. |
| Face Sharpness (+) | Step 6 instructs "face razor-sharp in focus". |
| Framing (+) | Step 3 adds "5–10% headroom above the head" for more reliable crown inclusion. |

---

### 6.5 Experimental v3 — Directive + Prohibitions

**Approximate length:** ~1,400 characters / ~240 words

**Key structural change:** Abandons the prose/bullet style entirely in favour of a structured brief with section dividers and a terminal `STRICT PROHIBITIONS` block. This tests whether explicit negative constraints are more reliably honoured than equivalent positive instructions.

**Identity section:**
```
━━━ IDENTITY — ZERO TOLERANCE FOR CHANGES ━━━
Treat the face as a locked, uneditable asset:
→ Skin color and undertone: match exactly — same warmth, depth, and tone   ← skin tone first
→ Skin texture: preserve all natural texture, pores, fine lines — no AI smoothing
→ Facial geometry: same bone structure, proportions, and all features
→ Eyes: same color, shape, spacing, and brow arch
→ Hair: same color and style as shown
→ Age: no de-aging or aging — keep the subject's natural age
```

**Lighting specification (unique to v3):**
```
3-point studio setup:
  • Key light — upper-left at 45°, soft box diffused
  • Fill light — right side, softer intensity to open shadows
  • Rim / hair light — subtle, from behind, to separate subject from background
```

**Prohibitions block:**
```
✗ Do NOT generate a different face
✗ Do NOT smooth, beautify, or retouch skin
✗ Do NOT change skin tone, hair color, or eye color
✗ Do NOT alter facial proportions
✗ Do NOT add accessories, props, or background elements not specified
✗ Do NOT apply cinematic, HDR, or stylized color grading
```

**Targeted metric improvements:**

| Metric | Mechanism |
|---|---|
| Skin Tone Match (+) | First identity bullet; skin tone is both positively asserted and negatively prohibited. |
| Face SSIM (+) | "Zero tolerance" framing + dual positive/negative constraints on facial geometry. |
| Exposure Quality (+) | Explicit 3-point lighting with key/fill/rim spec; prohibition on HDR and cinematic grading. |
| Background Uniformity (+) | "Consistent from center to all four edges" targets corner-sampling metric directly. |

---

### 6.6 Prompt Comparison Summary

| Dimension | Production | v1 | v2 | v3 |
|---|---|---|---|---|
| Identity before outfit | ✗ | ✓ | ✓ | ✓ |
| Skin tone named explicitly | ✗ | ✗ | ✓ | ✓ |
| Hair preservation | ✗ | ✓ | ✓ | ✓ |
| Age preservation | ✗ | ✗ | ✓ | ✓ |
| Background edge uniformity | ✗ | ✗ | ✓ | ✓ |
| Sharpness / focus instruction | ✗ | ✓ | ✓ | ✓ |
| 3-point lighting spec | ✗ | ✗ | ✗ | ✓ |
| Negative prohibition block | ✗ | ✗ | ✗ | ✓ |
| Approximate word count | ~75 | ~160 | ~200 | ~240 |

---

### 6.7 Current Production Prompt — Engineering Type, Pros & Cons

The prompt now shipping in `AiProfileGenerateService::getPrompts()` is the Directive +
Prohibitions structure. It is not a single technique but a deliberate **stack** of several.
Its dominant classification is:

> **Zero-shot, structured/modular instructional prompting with heavy constraint (negative)
> prompting** — applied to a text-to-image multimodal model.

#### 6.7.1 Techniques in the stack

| # | Technique | Where it appears in the current prompt |
|---|---|---|
| 1 | **Modular / compositional (template) prompting** | Final string assembled from six reusable blocks: `{$commonIntro} {$style}.{$commonFeatures}{$framingFix}{$neckFix}{$imageQuality}`. Only the outfit clause varies per image. |
| 2 | **Zero-shot prompting** | Pure instructions — no example input/output pairs are supplied to the model. |
| 3 | **Instructional / directive prompting** | Command voice with an explicit `INPUT:` / `OUTPUT:` contract (`PROFESSIONAL HEADSHOT DIRECTIVE`). |
| 4 | **Constraint / negative prompting** | A terminal `STRICT PROHIBITIONS` block of `✗ Do NOT…` rules, plus the `IDENTITY — ZERO TOLERANCE` framing. This is the defining feature. |
| 5 | **Delimiter / sectioned formatting** | `━━━ SECTION ━━━` headers segment the prompt (IDENTITY, BACKGROUND, FRAMING, ATTIRE, LIGHTING, TECHNICAL, PROHIBITIONS). |
| 6 | **Emphasis / repetition (priming)** | Identity preservation is stated up front *and* restated as a prohibition; CAPS and `→` arrows weight critical tokens. |
| 7 | **Parameterized variation** | `$limit` / `$offset` rotate a 16-item outfit list, yielding controlled diversity from one template rather than relying on model randomness. |

One-line label for citation: *"structured zero-shot instructional prompting with negative
constraints (modular, template-based)."*

#### 6.7.2 Pros

- **Consistency & reproducibility** — identity, background, framing, lighting, and quality
  are fixed blocks, so every headshot reads as if from the same studio; only the outfit changes.
- **Maintainability (DRY)** — six isolated components mean one lever can be tuned without
  touching the others; the service file documents these as the tunable surface.
- **Controlled diversity** — `offset`/`limit` rotation produces unique-but-on-brand variants
  deterministically.
- **Strong guardrails** — explicit `Do NOT` prohibitions directly target the known failure
  modes (face drift, skin smoothing/beautification, added accessories, HDR stylization).
- **Self-documenting** — section delimiters make intent legible to both the model and future maintainers.
- **Low cost / low complexity** — zero-shot needs no example corpus, fine-tuning, or retrieval pipeline.

#### 6.7.3 Cons

- **Verbosity → token cost & dilution** — the prompt is long and repetitive; past a point,
  image models weight tokens unevenly and key instructions can be averaged out.
- **Negative-prompt unreliability** — image models often honour `Do NOT X` poorly; naming a
  concept (e.g. "HDR", "accessories") can *raise* its chance of appearing. Native negative-prompt
  fields are usually more reliable than in-prompt prohibitions.
- **No reference grounding for style** — identity rides entirely on the single input image plus
  words; a few-shot or stronger conditioning signal typically locks identity better than
  "ZERO TOLERANCE" phrasing.
- **Model-coupling / brittleness** — wording is tuned to `gemini-2.5-flash-image`; a model swap
  can silently degrade results with no example-based anchoring to cushion it.
- **Soft / unenforced parameters** — `aspectRatio` is passed as prompt *text only*, not via API
  config, so the model may ignore it. Instruction-as-text is weaker than a real config constraint.
- **Limited semantic diversity** — variation is only the outfit string (mostly suit/blazer colour
  permutations); pose, expression, and crop are frozen, so outputs can feel templated.
- **Emphasis overuse** — heavy CAPS and symbols have diminishing returns and can hurt if the model
  over-anchors on "shouted" tokens.

---

## 7. Benchmarking Tool Design

### 7.1 Prompt Editor

The original application displayed prompts in a read-only expander. This was replaced with a live prompt editor — two side-by-side editable `st.text_area` widgets with the following behaviour:

- **Auto-reload on fingerprint change:** A fingerprint string encodes `gender|custom_outfit|experimental_outfit|background_style|exp_version_key`. When any sidebar selection changes, both text areas reload with the updated preset. This prevents stale prompt text from persisting across session parameter changes.
- **Manual override:** Within a constant fingerprint (same version, outfit, and background), user edits persist across Streamlit re-runs. Exactly the edited text is sent to the API.
- **Reset buttons:** `↺ Reset` restores the text area to the current preset without changing other state.
- **Live statistics:** Character and word count displayed beneath each editor.

### 7.2 Experimental Prompt Version Selector

A `st.radio` in the sidebar presents the three experimental versions. Selecting a version:
1. Changes the fingerprint.
2. Triggers auto-reload of the experimental text area with the corresponding preset.
3. Labels the result image header with the version name for unambiguous identification.

### 7.3 Model Selector

The Gemini model was previously hardcoded as `GEMINI_URL = "…/gemini-2.5-flash-image:generateContent"`. It is now constructed dynamically:

```python
gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
```

The sidebar offers:
- `gemini-2.5-flash-image` (current production default)
- `gemini-2.0-flash-exp-image-generation`
- Free-text custom model ID

`call_gemini_api` accepts `url` as an explicit parameter (defaulting to `GEMINI_URL` for backwards compatibility), and the generation block passes `gemini_url` from the sidebar selection. Both production and experimental calls use the same model, ensuring fair comparison.

### 7.4 Parallel Generation

Both prompts are submitted concurrently using `ThreadPoolExecutor(max_workers=2)`, minimising total wall-clock time and ensuring that any temporal variation in the Gemini API (temperature, model load) affects both prompts equally.

---

## 8. Results

*This section will be populated after benchmark runs are completed. The framework is ready for data collection.*

### 8.1 Data Collection Protocol

For statistically meaningful results, each prompt version should be tested with:
- Minimum 3–5 different reference photos (diverse skin tones, genders, ages).
- At least 1 generation per photo per version (per Gemini's stochastic nature, 3+ generations per prompt per photo are preferred).
- Qualitative ratings completed immediately after each generation while the reference image is visible.

### 8.2 Expected Results (Hypothesis)

Based on the structural analysis in Section 6:

| Metric | Expected ranking |
|---|---|
| Face SSIM | v3 ≥ v2 > v1 > Production |
| Skin Tone Match | v3 ≥ v2 > v1 > Production |
| Face Sharpness | v2 ≈ v3 > v1 > Production |
| Background Uniformity | v2 ≈ v3 > v1 > Production |
| Framing Quality | v2 ≥ v1 ≈ v3 ≈ Production |
| Exposure Quality | v3 > v2 ≈ v1 ≈ Production |
| Overall Score | v3 ≥ v2 > v1 > Production |

Note: Longer prompts are not always better. There is a risk that v3's structured format (Unicode dividers, `✗` symbols) is less well-handled by the model than plain prose, which could cause unexpected regressions. This hypothesis must be validated empirically.

### 8.3 Results Table (to be filled)

| Run | Reference photo | Gender | Prompt version | Model | SSIM | Skin | Sharp | BG Unif | Framing | Centering | Exposure | Overall Quant | Overall Qual | Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

---

## 9. Recommendations

### 9.1 Immediate

1. **Run the benchmark** with 3+ reference photos before making any prompt changes to production. Never change a production prompt based on visual intuition alone.
2. **Use `gemini-2.5-flash-image`** for all runs in the initial benchmark pass to ensure model is not a confounding variable.
3. **Rate qualitative scores immediately** after generation — recency bias affects scoring accuracy if ratings are done in batch later.

### 9.2 Short-Term (pending benchmark results)

4. If v2 or v3 outperforms production on Face SSIM + Skin Tone Match without regressing on Framing/Exposure, adopt the winner as the new production prompt in `AiProfileGenerateService.php`.
5. Consider **adding skin tone mention** to the production prompt as a minimal low-risk improvement even before full experiment results are available, since it addresses a clear gap with no downside.

### 9.3 Medium-Term

6. **Replace Haar cascade** with a deep-learning face detector (MTCNN or RetinaFace). Haar cascade fails on non-frontal faces and profiles, producing neutral-score fallbacks that mask real quality differences.
7. **Add FaceNet / ArcFace cosine similarity** as an 8th metric. SSIM measures structural patterns but is not identity-aware — two different people with similar face structure can score high. Embedding-based identity distance is a more principled measure for this use case.
8. **Average metrics across 3 generations per prompt** to reduce per-run stochasticity. A single bad generation can skew Overall Score by 5–10 points.
9. **Add CLIP scoring** (`"professional business headshot"` anchor text) as a semantic quality metric independent of the reference photo.

### 9.4 Long-Term

10. Consider **prompt personalisation by skin tone range**: darker skin tones are more susceptible to brightening drift by the model. A skin-tone-aware prompt variant (with reinforced tone preservation wording) may be warranted.
11. Evaluate **Gemini 2.0 Flash Experimental** as a model upgrade candidate using the configurable model selector added in this work.

---

## 10. Appendix — Full Prompt Texts

### A. Production Prompt (Current — Directive + Prohibitions)

This is the live production prompt assembled by `AiProfileGenerateService::getPrompts()`.
Shown for a male subject, first outfit variant; `{outfit}` is substituted per variant and
the background is fixed to soft neutral grey.

```
PROFESSIONAL HEADSHOT DIRECTIVE

INPUT: Reference photograph of a real person
OUTPUT: Professional {gender} corporate headshot, {outfit}.

━━━ IDENTITY — ZERO TOLERANCE FOR CHANGES ━━━
The person in the generated image must be the EXACT SAME PERSON as in the reference photo.
Treat the face as a locked, uneditable asset:
→ Skin color and undertone: match exactly — same warmth, depth, and tone
→ Skin texture: preserve all natural texture, pores, fine lines — no AI smoothing
→ Facial geometry: same bone structure, proportions, and all features
→ Eyes: same color, shape, spacing, and brow arch
→ Hair: same color and style as shown
→ Age: no de-aging or aging — keep the subject's natural age

━━━ BACKGROUND ━━━
Soft neutral grey — clean, uniform, professional studio backdrop.
Completely free of texture, objects, or environmental context.
Background must be consistent from center to all four edges of the frame.

━━━ FRAMING & POSE ━━━
• Head-to-mid-chest crop — full crown of head with small headroom margin
• Face centered horizontally
• Upright, professional posture — relaxed shoulders, no unnatural tilt

━━━ ATTIRE ━━━
Garment must be sharp, properly fitted, and wrinkle-free.
Collar and neckline sit naturally against the neck — no gaps or floating fabric.
Neck and shoulder anatomy anatomically correct and proportional.

━━━ LIGHTING ━━━
3-point studio setup:
  • Key light — upper-left at 45°, soft box diffused
  • Fill light — right side, softer intensity to open shadows
  • Rim / hair light — subtle, from behind, to separate subject from background
Result: even, shadow-minimized illumination; true-to-life color; no blown highlights on skin.

━━━ TECHNICAL OUTPUT ━━━
• Photorealistic DSLR photograph — high resolution, no compression artifacts
• 85mm portrait lens equivalent at f/2.2 — face tack-sharp, background subtly soft
• No artistic filters, no painterly or HDR effects, no stylization

━━━ STRICT PROHIBITIONS ━━━
✗ Do NOT generate a different face — the subject must be recognizable as the reference person
✗ Do NOT smooth, beautify, or retouch skin
✗ Do NOT change skin tone, hair color, or eye color
✗ Do NOT alter facial proportions or make the person look any different
✗ Do NOT add accessories, props, or background elements not specified
✗ Do NOT apply cinematic, HDR, or stylized color grading
```

> **Component map** (assembly order in `getPrompts()`):
> `$commonIntro` (intro + `{gender}` + `{outfit}`) → `$commonFeatures` (IDENTITY + BACKGROUND)
> → `$framingFix` (FRAMING & POSE) → `$neckFix` (ATTIRE) → `$imageQuality`
> (LIGHTING + TECHNICAL OUTPUT + STRICT PROHIBITIONS).

---

### B. Experimental v1 — Photographer Role

```
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
- Soft box studio lighting: main light slightly above-left, subtle fill from the right,
  minimal shadow under chin
- Face in sharp focus, background softly diffused (shallow depth of field)
- Color grading: neutral, true-to-life — no heavy warm/cool toning

OUTPUT: A single portrait image matching all specifications above.
```

---

### C. Experimental v2 — Step-by-Step Identity

```
You are processing a real reference photograph to generate a professional corporate
headshot. The face in the reference photo must appear EXACTLY in the output —
this is identity-critical.

STEP 1 — ANCHOR THE IDENTITY (highest priority):
Study every detail of the face in the uploaded photo before generating:
• Skin tone and undertone (warm / cool / neutral) — match precisely
• Skin texture: pores, fine lines, any marks or freckles — do not smooth away
• Eye color, shape, and spacing
• Nose shape, lip shape, jawline, and cheekbone structure
• Hair: exact color, texture, and current style as shown
• Apparent age — do not de-age or age the person
• Ethnicity and all distinguishing features

This face must appear UNCHANGED in the output.

STEP 2 — APPLY PROFESSIONAL STYLING:
Subject: {gender} professional
Attire: {outfit}

STEP 3 — COMPOSITION:
• Framing: crown of head to mid-chest, 5–10% headroom above the head
• Face horizontally centered in frame
• Upright posture, shoulders relaxed, confident neutral expression

STEP 4 — CLOTHING & ANATOMY:
• Clothing crisp, well-tailored, wrinkle-free
• Collar sits flat against neck — no floating fabric, no gaps
• Neck and shoulder anatomy natural and proportional

STEP 5 — BACKGROUND:
• {background} — completely uniform solid or very subtle gradient
• Must be clean all the way to the image edges — no texture or environmental elements

STEP 6 — LIGHTING & FOCUS:
• Professional soft-box studio setup: key light at 45° upper-left, gentle fill from right
• Even illumination across the face — no harsh chin or nose shadows
• True-to-life color rendition — no warm or cool color cast
• Face razor-sharp in focus; background may have slight depth-of-field softness
• Ultra-photorealistic — indistinguishable from a real studio photograph

OUTPUT: Single portrait image exactly matching the above specifications.
```

---

### D. Experimental v3 — Directive + Prohibitions

```
PROFESSIONAL HEADSHOT DIRECTIVE

INPUT: Reference photograph of a real person
OUTPUT: Professional {gender} corporate headshot

━━━ IDENTITY — ZERO TOLERANCE FOR CHANGES ━━━
The person in the generated image must be the EXACT SAME PERSON as in the
reference photo. Treat the face as a locked, uneditable asset:
→ Skin color and undertone: match exactly — same warmth, depth, and tone
→ Skin texture: preserve all natural texture, pores, fine lines — no AI smoothing
→ Facial geometry: same bone structure, proportions, and all features
→ Eyes: same color, shape, spacing, and brow arch
→ Hair: same color and style as shown
→ Age: no de-aging or aging — keep the subject's natural age

━━━ ATTIRE ━━━
{outfit}
Garment must be sharp, properly fitted, and wrinkle-free.
Collar and neckline sit naturally against the neck — no gaps or floating fabric.
Neck and shoulder anatomy anatomically correct and proportional.

━━━ FRAMING & POSE ━━━
• Head-to-mid-chest crop — full crown of head with small headroom margin
• Face centered horizontally
• Upright, professional posture — relaxed shoulders, no unnatural tilt

━━━ BACKGROUND ━━━
{background} — clean, uniform, professional studio backdrop
Completely free of texture, objects, or environmental context.
Background must be consistent from center to all four edges of the frame.

━━━ LIGHTING ━━━
3-point studio setup:
  • Key light — upper-left at 45°, soft box diffused
  • Fill light — right side, softer intensity to open shadows
  • Rim / hair light — subtle, from behind, to separate subject from background
Result: even, shadow-minimized illumination; true-to-life color; no blown
highlights on skin.

━━━ TECHNICAL OUTPUT ━━━
• Photorealistic DSLR photograph — high resolution, no compression artifacts
• 85mm portrait lens equivalent at f/2.2 — face tack-sharp, background subtly soft
• No artistic filters, no painterly or HDR effects, no stylization

━━━ STRICT PROHIBITIONS ━━━
✗ Do NOT generate a different face — subject must be recognizable as reference person
✗ Do NOT smooth, beautify, or retouch skin
✗ Do NOT change skin tone, hair color, or eye color
✗ Do NOT alter facial proportions or make the person look any different
✗ Do NOT add accessories, props, or background elements not specified
✗ Do NOT apply cinematic, HDR, or stylized color grading
```

---

### E. Legacy Production Prompt (pre-2026-06)

Retained for historical comparison. This was the production prompt at rev. 1, before the
Directive + Prohibitions structure (Appendix A) was adopted.

```
Generate a portrait of a professional {gender} {outfit}.
STRICTLY PRESERVE the subject's original face. The output must look exactly like
the person in the uploaded image. Do not alter facial structure, skin texture, or
expression. The body should be centered with a natural, professional pose.
Background must be a soft, solid, professional ID card style background.
Frame the image from the top of the head to the mid-chest.
Ensure the neck and shoulders are anatomically correct and proportional.
The clothing must fit naturally around the neck/collar area without floating or
weird cuts.
PHOTOREALISTIC style. The image must look like a high-end photograph.
No cartoonish, 3D render, or filtered looks. Lighting should be natural studio lighting.
```

---

*Report generated as part of CheckinMe AI Profile Benchmarking initiative.*  
*For questions or to contribute benchmark data, update Section 8 with run results.*
