# AI Profile Generator — Prompt Engineering Report

**Project:** CheckinMe AI Profile Generator
**Scope:** Prompt design, evaluation methodology, and Google Gemini image generation
**Production model:** Google Gemini 2.5 Flash Image (nicknamed *"nano banana"*)
**Date:** 2026-06-06

---

## Table of Contents

1. [Overview](#1-overview)
2. [Project Context](#2-project-context)
3. [Methodology](#3-methodology)
4. [Implementation with Google Gemini](#4-implementation-with-google-gemini)
5. [Image Generation Model Performance](#5-image-generation-model-performance)
6. [Prompt Comparison — Original vs Latest](#6-prompt-comparison--original-vs-latest)
7. [Appendix — Full Prompt Texts](#7-appendix--full-prompt-texts)

---

## 1. Overview

CheckinMe's AI Profile Generator turns a single user-supplied reference photo into a
set of professional corporate headshots with varied attire. The whole product depends on
one thing above all: **face identity preservation** — the generated headshot must clearly
look like the same person in the reference photo.

This report covers three things, in plain terms:

- **The methodology** used to judge whether a generated headshot is good.
- **How the generation is implemented** with Google Gemini's image generation service.
- **A before/after comparison** of the original production prompt against the current
  (latest) prompt now used in production.

Earlier drafts of this report experimented with several throwaway prompt variants. Those
are no longer relevant and have been removed. What remains is the original prompt and the
latest prompt that replaced it.

---

## 2. Project Context

When a user requests headshots, the production service (`AiProfileGenerateService.php`):

1. Takes a reference photo, the subject's gender, and how many headshots to produce.
2. Picks a set of outfit descriptions from a fixed catalogue (16 per gender), rotating
   through them so each headshot wears something different.
3. Builds one text prompt per outfit and sends it, together with the reference photo, to
   Google Gemini's image generation endpoint.
4. Receives a generated image back and returns it to the app.

All outfits are conservative corporate styles (suits, blazers, formal blouses) chosen
deliberately to avoid distortion around the neckline, a common failure point for AI
portrait generators.

| Gender | Outfit pool | Style range |
|--------|-------------|-------------|
| Male   | 16 | Black / navy / charcoal / grey suits with varied shirt and tie combinations |
| Female | 16 | Black / navy / grey / dark blazers over white and light-coloured blouses |

---

## 3. Methodology

Each generated headshot is scored two ways — automatically (quantitative) and by a human
reviewer (qualitative) — and the two are blended into one final score.

### 3.1 Quantitative metrics

Seven measurements are taken on every generated image and compared against the reference
photo. Each produces a 0–100 score, and they are combined with fixed weights.

| Metric | Weight | What it checks |
|---|---|---|
| Face structural similarity | 25% | Is it structurally the same face? (identity drift) |
| Skin tone match | 20% | Did the complexion / undertone shift? |
| Face sharpness | 20% | Is the face crisp, or blurred / over-smoothed? |
| Background uniformity | 15% | Is the backdrop clean and even to the corners? |
| Framing quality | 10% | Is the crop right — not too close, not too far? |
| Face centering | 5% | Is the face centred horizontally? |
| Exposure quality | 5% | Is it well-lit, not over- or under-exposed? |

**Overall quantitative score** = the weighted average of the seven metrics above.

### 3.2 Qualitative assessment

A human reviewer rates five questions from 1 to 5 stars while looking at the reference
photo side by side with the result:

| Criterion | Question |
|---|---|
| Face resemblance | Does the face look exactly like the person in the reference photo? |
| Professional look | Does it look like a real professional headshot? |
| Clothing quality | Does the clothing look natural and well-fitted? |
| Background quality | Is the background clean, solid, and professional? |
| Overall preference | Overall, how satisfied are you with this image? |

**Qualitative score** = the average star rating, scaled to 0–100.

### 3.3 Final combined score

The final score weights the automated measurements slightly higher than the human rating:

**Final = 60% quantitative + 40% qualitative.**

When two prompts are compared, the one scoring at least 2 points higher wins; a gap of
under 2 points is treated as a tie.

---

## 4. Implementation with Google Gemini

Headshots are generated through **Google Gemini's image generation service**. The
implementation is deliberately simple: there is no fine-tuning, no training data, and no
separate model to host. Everything is driven by the prompt plus the reference photo.

**How a single headshot is generated:**

1. The reference photo is read and attached to the request alongside the text prompt.
2. The request is sent to the Gemini image generation endpoint for the chosen model.
3. Gemini returns the generated headshot image, which is passed back to the app.

The model used is configurable. Production runs on **Gemini 2.5 Flash Image**, and the
benchmarking tool can point at a different model to compare results, without any code
changes. Both the original and latest prompts are always run against the **same model**
so the comparison stays fair.

A few practical notes about working with the Gemini image service:

- **The reference photo does the heavy lifting for identity.** Identity preservation comes
  primarily from the attached photo; the prompt's job is to reinforce it and control
  everything else (attire, framing, background, lighting).
- **Instructions are text, not hard settings.** Things like aspect ratio and "don't do X"
  are requests in the prompt, not enforced parameters, so the model can occasionally ignore
  them. Wording matters.
- **Output varies between runs.** The same prompt can produce slightly different images, so
  judging a prompt reliably means generating several times rather than once.

---

## 5. Image Generation Model Performance

These are qualitative, observed characteristics of the Gemini image models available for
this pipeline. Formal benchmark numbers will be added once full evaluation runs are
complete; the descriptions below reflect how each model behaves on the headshot task.

### Gemini 2.5 Flash Image — *"nano banana"* (production)

This is Google's current image generation and editing model, nicknamed **"nano banana"**
— it is the same model as `gemini-2.5-flash-image`, not a separate one. It is the model
used in production.

- **Identity preservation:** the strongest of the available options. It holds a subject's
  face, skin tone, and features well while changing clothing — exactly what this product
  needs.
- **Photorealism:** produces clean, realistic studio-style headshots with good lighting and
  sharp faces.
- **Editing behaviour:** good at "keep the person, change the outfit / background" style
  edits, which is the core operation here.
- **Trade-offs:** can still smooth or "beautify" skin if not explicitly told not to, and is
  more expensive per image than the older experimental model. This is why the prompt
  includes explicit instructions against smoothing and altering the face.

### Gemini 2.0 Flash (experimental image generation) — comparison baseline

`gemini-2.0-flash-exp-image-generation` is an earlier, experimental native image
generation model.

- **Identity preservation:** noticeably weaker — more likely to drift the face, alter
  features, or change skin tone when re-dressing the subject.
- **Photorealism:** lower and less consistent fidelity than nano banana; results feel more
  "generated."
- **Use:** useful as a cheaper baseline for comparison, but **not recommended** for
  identity-critical headshots in production.

### Summary

| Model | Identity preservation | Photorealism | Recommended for production |
|---|---|---|---|
| Gemini 2.5 Flash Image (nano banana) | Strong | High | **Yes** |
| Gemini 2.0 Flash (exp. image gen) | Weaker | Moderate | No — baseline only |

**Takeaway:** the choice of image model matters as much as the prompt. Gemini 2.5 Flash
Image (nano banana) is the right production choice because identity preservation is the
product's primary requirement, and it is clearly the better model on that dimension.

---

## 6. Prompt Comparison — Original vs Latest

The production prompt was rewritten. Below is the before/after. Full text of both prompts
is in the [Appendix](#7-appendix--full-prompt-texts).

### The original prompt (before)

A short, single-paragraph instruction. It worked, but it had three weaknesses:

1. **Outfit came first, identity second.** It opened by describing the outfit, implicitly
   signalling that generating clothing was the main task and preserving the face was a
   secondary constraint.
2. **No mention of skin tone.** It asked to preserve "facial structure, skin texture, and
   expression" but never named skin colour or undertone — a gap, since skin tone shift is a
   common and noticeable failure.
3. **Vague background.** "ID card style background" is ambiguous; it didn't ask for the
   backdrop to stay clean all the way to the edges of the frame.

### The latest prompt (after)

A structured brief organised into labelled sections, ending with an explicit list of
prohibitions. It fixes all three weaknesses above and adds clearer lighting and quality
direction.

- **Identity first, and stated as non-negotiable.** It leads with an "identity — zero
  tolerance for changes" block that names skin colour and undertone, skin texture, facial
  geometry, eyes, hair, and age explicitly.
- **Explicit "do not" list.** A closing prohibitions block spells out what the model must
  not do (generate a different face, smooth or beautify skin, change skin/hair/eye colour,
  add props, apply HDR/cinematic grading).
- **Clean, edge-to-edge background.** The background section requires consistency "from
  centre to all four edges of the frame."
- **Defined lighting and output.** Adds a 3-point studio lighting description and a
  photorealistic DSLR output spec for more consistent, professional results.

### What changed, at a glance

| Aspect | Original prompt | Latest prompt |
|---|---|---|
| Identity stated before outfit | No | Yes |
| Skin tone / undertone named | No | Yes |
| Hair & age preservation | No | Yes |
| Background clean to the edges | No | Yes |
| Explicit "do not" prohibitions | No | Yes |
| Defined studio lighting | No | Yes |
| Length | Short (~75 words) | Longer, structured (~240 words) |

**Note:** longer is not automatically better. The latest prompt is more explicit and more
consistent, but it is also more verbose, and image models can weight long instructions
unevenly. The methodology in Section 3 exists precisely so prompt changes are judged on
measured results rather than intuition.

---

## 7. Appendix — Full Prompt Texts

### A. Original prompt (before)

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

### B. Latest prompt (after — current production)

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

---

*Report prepared as part of the CheckinMe AI Profile Benchmarking initiative.*
