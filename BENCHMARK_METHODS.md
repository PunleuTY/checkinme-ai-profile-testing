# AI Portrait Benchmark — Evaluation Methods

**Project:** CheckinMe AI Profile Generator  
**Tool:** `benchmark_app.py` + `benchmark_metrics.py`  
**Purpose:** Objective + subjective comparison of production vs. experimental Gemini prompts for professional headshot generation.

---

## Table of Contents

1. [Overview](#overview)
2. [Metric Architecture](#metric-architecture)
3. [Metric 1 — Face SSIM](#1-face-ssim)
4. [Metric 2 — Skin Tone Match](#2-skin-tone-match)
5. [Metric 3 — Face Sharpness](#3-face-sharpness)
6. [Metric 4 — Background Uniformity](#4-background-uniformity)
7. [Metric 5 — Framing Quality](#5-framing-quality)
8. [Metric 6 — Face Centering](#6-face-centering)
9. [Metric 7 — Exposure Quality](#7-exposure-quality)
10. [Overall Quantitative Score](#overall-quantitative-score)
11. [Qualitative Ratings](#qualitative-ratings)
12. [Final Combined Score](#final-combined-score)
13. [Limitations & Known Gaps](#limitations--known-gaps)
14. [Dependency Reference](#dependency-reference)

---

## Overview

Each generated image is evaluated against two sources of truth:

| Source | Used by |
|---|---|
| **Reference photo** (uploaded by user) | Face SSIM, Skin Tone Match |
| **Absolute quality standards** (studio portrait norms) | Sharpness, Background, Framing, Centering, Exposure |

All metrics output a score in the range **0–100** (higher = better). They are combined into a single **Overall Quantitative Score** via a weighted average, then optionally blended with a **human Qualitative Score** for a **Final Combined Score**.

---

## Metric Architecture

```
Reference Photo ──────┐
                       ├──► Face SSIM           (weight 25%)
Generated Image ───────┤
                       ├──► Skin Tone Match     (weight 20%)
                       ├──► Face Sharpness      (weight 20%)
                       ├──► Background Uniform. (weight 15%)
                       ├──► Framing Quality     (weight 10%)
                       ├──► Face Centering      (weight  5%)
                       └──► Exposure Quality    (weight  5%)
                                    │
                                    ▼
                          Overall Score (0–100)
                                    │
                         + Qualitative Score
                                    │
                                    ▼
                          Final Combined Score
                        (60% Quant + 40% Qual)
```

### Shared pre-processing: Face Detection

Most metrics rely on locating the face first. We use **OpenCV's Haar Cascade Classifier** (`haarcascade_frontalface_default.xml`):

- Algorithm: Viola–Jones object detection (2001) — trained on thousands of positive/negative face examples using Adaboost
- Parameters: `scaleFactor=1.1`, `minNeighbors=5`, `minSize=(40,40)`
- Output: Bounding box `(x, y, w, h)` of the largest detected face
- Fallback: If no face is detected, the metric either falls back to a whole-image measurement or returns a neutral score of 50

---

## 1. Face SSIM

**Weight:** 25% | **Library:** `scikit-image` | **Depends on:** Face detection

### What it measures

Structural identity preservation — how closely the *structure* of the face in the generated image matches the reference photo. This is the primary proxy for "does the generated image still look like the same person."

### Method: Structural Similarity Index Measure (SSIM)

SSIM was introduced by Wang et al. (2004) as a perceptual quality metric that models human visual perception better than pixel-level metrics like MSE or PSNR. It compares two image patches across three independent components:

```
SSIM(x, y) = [l(x,y)]^α · [c(x,y)]^β · [s(x,y)]^γ
```

| Component | Formula | What it captures |
|---|---|---|
| Luminance `l` | `(2μₓμᵧ + C₁) / (μₓ² + μᵧ² + C₁)` | Mean brightness similarity |
| Contrast `c` | `(2σₓσᵧ + C₂) / (σₓ² + σᵧ² + C₂)` | Variance / edge strength |
| Structure `s` | `(σₓᵧ + C₃) / (σₓσᵧ + C₃)` | Local spatial pattern correlation |

- `μ` = local mean, `σ` = local standard deviation, `σₓᵧ` = covariance
- `C₁ = (0.01·L)²`, `C₂ = (0.03·L)²` where `L = 255` (8-bit range)
- Default weights: `α = β = γ = 1`

### Implementation steps

1. Detect face bounding box in both reference and generated image
2. Crop face region from each image
3. Convert both crops to **grayscale**
4. Resize both crops to a fixed **96×96 pixels** (LANCZOS resampling) — required because SSIM needs same-size inputs and different images will have different face sizes
5. Compute `structural_similarity(ref_patch, gen_patch, data_range=255)`
6. Raw output: `[-1, +1]` → remapped to `[0, 100]`:

```
score = max(0, (ssim_raw + 1) / 2 × 100)
```

### Score interpretation

| Score | Meaning |
|---|---|
| 85–100 | Near-identical face structure — excellent identity preservation |
| 65–84 | Slight structural differences — minor facial feature changes |
| 40–64 | Noticeable changes — different jawline, nose, or eye area |
| 0–39 | Face looks significantly different from reference |

### Why SSIM over pixel MSE?

MSE measures absolute pixel differences. A slight shift in head position or a small lighting change would produce high MSE even if the face looks identical. SSIM measures **patterns and local correlations**, making it robust to minor lighting and position differences while still being sensitive to genuine structural changes (reshaped nose, wider eyes, different jaw).

### Limitations

- Pose sensitivity: if the AI generates a slight head tilt not present in the reference, SSIM drops even if the identity is preserved
- The 96×96 resize discards fine-grained detail (pores, fine lines)
- Returns `50` (neutral) if face detection fails in either image

---

## 2. Skin Tone Match

**Weight:** 20% | **Library:** `numpy` | **Depends on:** Face detection

### What it measures

How consistently the AI preserved the subject's skin color. Skin tone drift (making someone lighter, darker, or a different undertone) is one of the most common failure modes in AI-generated portraits.

### Method: Color Histogram Correlation

1. Detect and crop the face region in both images
2. Extract pixel values as RGB arrays
3. For the **Red** channel and **Green** channel separately:
   - Build a **32-bin histogram** over range [0, 255] — each bin covers an 8-value brightness range
   - Normalize the histogram to a probability distribution (sum = 1):

```
h_normalized[i] = count[i] / total_pixels
```

4. Compute **Pearson correlation coefficient** between the normalized histograms of reference and generated:

```
r = Σ[(hᵣ - μᵣ)(hɡ - μɡ)] / (σᵣ · σɡ)
```

5. Average the correlation scores from R and G channels
6. Remap from `[-1, +1]` to `[0, 100]`:

```
score = max(0, (r + 1) / 2 × 100)
```

### Why R and G channels only?

Human skin tone is primarily encoded in the **red-green balance**. The blue channel carries relatively little skin-specific information and mostly reflects ambient light color temperature. Using R+G is consistent with dermatological colorimetry literature and standard skin segmentation research.

### Why histograms instead of mean color?

Mean color collapses the full tonal distribution into a single number. Two images can have the same mean skin tone but differ in how highlights and shadows are distributed (e.g., one might have deep shadows on one cheek). Histograms capture the **shape of the tonal distribution**, making the comparison far more discriminative.

### Score interpretation

| Score | Meaning |
|---|---|
| 80–100 | Skin tone preserved accurately |
| 60–79 | Minor tonal shift — slight undertone change |
| 40–59 | Noticeable skin tone difference (neutral / unknown) |
| 0–39 | Significant skin tone drift — visually different complexion |

### Limitations

- Sensitive to lighting changes: a darker shadow on one cheek will shift the histogram even if the underlying skin tone is correct
- Returns `50` (neutral) if face detection fails

---

## 3. Face Sharpness

**Weight:** 20% | **Library:** `opencv` | **Depends on:** Face detection

### What it measures

Focus quality specifically within the face region. A blurry face is the clearest sign of a low-quality AI generation, regardless of how accurate the content is.

### Method: Laplacian Variance

The **Laplacian operator** is a second-order spatial derivative that measures the rate of intensity change in an image:

```
∇²f = ∂²f/∂x² + ∂²f/∂y²
```

In discrete form, applied as a convolution with the kernel:

```
 0   1   0
 1  -4   1
 0   1   0
```

- **Sharp regions** (edges, fine textures): large positive/negative Laplacian values
- **Blurry/smooth regions**: Laplacian values close to zero

We compute the **variance** of the Laplacian response — a blurry image has a low-variance Laplacian (all near zero), while a sharp image has high variance (large peaks at edges):

```
sharpness_score = Var(∇²I)
```

Normalization: `score = min(100, (variance / 1500) × 100)`

The threshold of 1500 is empirically calibrated: professionally sharp portrait photos consistently exceed 500, while noticeably blurry images fall below 100.

### Why face region only?

Professional portraits intentionally blur the background (shallow depth of field). Measuring sharpness on the full image would penalize correctly bokeh'd backgrounds. By isolating the face crop (with a 10% inset padding to avoid hair edges), we measure only what matters: is the face itself in focus?

### Score interpretation

| Score | Meaning |
|---|---|
| 75–100 | Crisp, well-focused face |
| 50–74 | Acceptable sharpness, slightly soft |
| 25–49 | Noticeably blurry or over-smoothed face |
| 0–24 | Severely out of focus or heavily smoothed |

### Limitations

- High-contrast synthetic artifacts (sharp pixel noise) can score high even if the image looks artificial
- Very high-resolution images will naturally have lower Laplacian variance because edges are spread over more pixels; this is mitigated by working on the face crop at native resolution rather than downsampling

---

## 4. Background Uniformity

**Weight:** 15% | **Library:** `numpy` | **Depends on:** Nothing (no face detection needed)

### What it measures

Whether the background is clean, solid, and professional — as required by the prompt ("Background must be a soft, solid, professional ID card style background").

### Method: Corner Pixel Standard Deviation

In a correctly framed head-to-mid-chest portrait, the **four corners of the image contain only background** — the subject's face and clothing are in the center. We exploit this geometric property:

1. Define a corner margin: `m = max(12, 7% of min(width, height))`
2. Sample all pixels in the four corner patches:
   - Top-left: `[0:m, 0:m]`
   - Top-right: `[0:m, W-m:W]`
   - Bottom-left: `[H-m:H, 0:m]`
   - Bottom-right: `[H-m:H, W-m:W]`
3. Concatenate all corner pixels into one array
4. Compute standard deviation across all RGB values

```
score = max(0, 100 − (std / 60) × 100)
```

- `std < 5`: Near-perfect solid background → score ~92–100
- `std ≈ 30`: Subtle gradient background → score ~50
- `std > 60`: Textured or complex background → score ~0

### Score interpretation

| Score | Meaning |
|---|---|
| 85–100 | Solid, clean background — ideal for ID/LinkedIn |
| 60–84 | Subtle gradient, mostly acceptable |
| 30–59 | Visible texture or color variation |
| 0–29 | Complex, cluttered, or highly variable background |

### Limitations

- If the subject has very wide shoulders that extend into corners, clothing pixels enter the sample and falsely degrade the score
- Does not evaluate center-background quality — only the corners

---

## 5. Framing Quality

**Weight:** 10% | **Library:** `opencv` | **Depends on:** Face detection

### What it measures

Whether the AI followed the framing instruction in the prompt: *"Frame the image from the top of the head to the mid-chest."*

### Method: Face Height Ratio

1. Detect face bounding box → extract face height `fh`
2. Get total image height `H`
3. Compute the ratio `r = fh / H`
4. Define the ideal range: `[0.30, 0.65]`

```
if 0.30 ≤ r ≤ 0.65:
    score = 100
else:
    dist = min(|r − 0.30|, |r − 0.65|)
    score = max(0, 100 − (dist / 0.20) × 100)
```

The penalty ramps linearly to 0 at 0.20 distance outside the ideal range.

### Ideal range rationale

| Scenario | Face/Image height ratio |
|---|---|
| Head-to-mid-chest (target) | ~0.35–0.60 |
| Head-only close-up | ~0.65–0.85 |
| Full-body shot | ~0.10–0.25 |

The range `[0.30, 0.65]` gives tolerance for variation in neck/torso length while correctly identifying both excessively zoomed-in and zoomed-out frames.

### Limitations

- The Haar cascade box starts at the forehead, not the crown of the head — hair is excluded. Actual "head" occupies slightly more space, so ratios are slightly underestimated (~5–10%)
- Returns `0` if no face is detected

---

## 6. Face Centering

**Weight:** 5% | **Library:** `opencv` | **Depends on:** Face detection

### What it measures

Whether the face is horizontally centered in the frame — a standard requirement for professional ID and LinkedIn headshots.

### Method: Horizontal Centroid Offset

1. Detect face bounding box `(x, y, w, h)`
2. Compute face horizontal center: `face_cx = x + w/2`
3. Compute image horizontal center: `img_cx = W/2`
4. Compute normalized offset: `offset = |face_cx − img_cx| / img_cx`

```
score = max(0, 100 − offset × 200)
```

- Offset = 0 (perfectly centered) → score 100
- Offset = 0.25 (face shifted 25% to one side) → score 50
- Offset ≥ 0.50 (face at image edge) → score 0

### Score interpretation

| Score | Meaning |
|---|---|
| 85–100 | Well-centered, professional |
| 60–84 | Slight offset, mostly acceptable |
| 30–59 | Noticeably off-center |
| 0–29 | Face significantly displaced from center |

### Limitations

- Vertical centering is not assessed — the prompt controls this implicitly via framing
- Returns `0` if no face is detected

---

## 7. Exposure Quality

**Weight:** 5% | **Library:** `numpy` | **Depends on:** Nothing

### What it measures

Whether the image is correctly exposed for a professional studio portrait — not too dark (underexposed) and not too bright/washed-out (overexposed).

### Method: Mean Luminance Range Check

1. Convert image to grayscale (luminance channel)
2. Compute mean pixel value: `mean_L ∈ [0, 255]`
3. Define ideal studio portrait range: `[90, 175]`

```
if 90 ≤ mean_L ≤ 175:
    score = 100
elif mean_L < 90:
    score = max(0, (mean_L / 90) × 100)        # underexposed
else:
    score = max(0, ((255 − mean_L) / 80) × 100) # overexposed
```

### Ideal range rationale

| mean_L | Visual appearance |
|---|---|
| < 50 | Very dark — face details lost in shadow |
| 50–89 | Underexposed — professional but dim |
| **90–175** | **Correct studio exposure** |
| 176–210 | Slightly overexposed — highlights beginning to blow |
| > 210 | Overexposed — skin washed out, detail lost |

### Limitations

- This is a **global** metric — a correctly exposed face against a very dark suit could score lower than deserved
- Gemini generally handles exposure well, so this metric rarely differentiates prompts strongly; hence the 5% weight

---

## Overall Quantitative Score

The weighted sum of all seven metrics:

```
Overall = (Face_SSIM        × 0.25)
        + (Skin_Tone_Match   × 0.20)
        + (Face_Sharpness    × 0.20)
        + (Background_Unif.  × 0.15)
        + (Framing           × 0.10)
        + (Face_Centering    × 0.05)
        + (Exposure          × 0.05)
```

### Weight rationale

| Priority | Metrics | Total weight | Reasoning |
|---|---|---|---|
| Face identity | SSIM + Skin Tone | 45% | If the person is unrecognizable, the image is unusable |
| Technical quality | Face Sharpness | 20% | Blurry face = unusable image |
| Background | Uniformity | 15% | Core product requirement |
| Composition | Framing + Centering | 15% | Prompt compliance |
| Exposure | Exposure | 5% | Rarely the differentiating factor for Gemini |

---

## Qualitative Ratings

Human perception of portrait quality cannot be fully captured by mathematical metrics. Qualitative ratings cover subjective dimensions:

| Criterion | Question asked |
|---|---|
| **Face Resemblance** | Does the face look exactly like the person in the reference photo? |
| **Professional Look** | Does the overall image look like a professional headshot? |
| **Clothing Quality** | Does the clothing look natural, well-fitted, and realistic? |
| **Background Quality** | Is the background clean, solid, and professional? |
| **Overall Preference** | Overall, how satisfied are you with this image? |

Each criterion is rated **1–5 stars**. The five ratings are averaged and scaled to 0–100:

```
qualitative_score = (average_star_rating / 5) × 100
```

---

## Final Combined Score

```
Final = 0.60 × Quantitative_Overall + 0.40 × Qualitative_Average
```

The 60/40 split reflects that:
- Quantitative metrics are **objective and repeatable** but miss perceptual subtleties (uncanny valley, unnatural clothing texture, AI artifacts not captured by any single metric)
- Human judgment is **subjective but holistic** — a person can immediately tell if an image "feels off" even when all metrics score well

### Verdict thresholds

| Condition | Verdict |
|---|---|
| `|Exp − Prod| < 2` | Tie |
| `Exp − Prod ≥ 2` | Experimental wins |
| `Prod − Exp ≥ 2` | Production wins |

---

## Limitations & Known Gaps

| Gap | Impact | Potential improvement |
|---|---|---|
| Haar cascade face detection | Fails on non-frontal faces, heavy occlusion, or unusual lighting | Replace with MTCNN or RetinaFace (deep learning detector) |
| SSIM pose sensitivity | Score drops if head is at slightly different angle even with identical identity | Use face alignment (68-point landmark normalization) before SSIM |
| Global exposure metric | Dark clothing can drag down exposure score of a well-lit face | Measure exposure only within the face bounding box |
| No semantic quality score | Cannot assess "does this look professional" automatically | Integrate CLIP scoring against "professional business headshot" anchor text |
| No deep identity metric | SSIM is structural but not identity-aware | Add FaceNet/ArcFace embedding cosine similarity for true identity verification |
| Single-image evaluation | Prompt quality varies per run due to model stochasticity | Average metrics across 3–5 generations per prompt for statistical significance |

---

## Dependency Reference

| Library | Version | Used for |
|---|---|---|
| `opencv-python-headless` | ≥ 4.8 | Face detection (Haar cascade), Laplacian filter |
| `scikit-image` | ≥ 0.21 | SSIM computation |
| `numpy` | ≥ 1.24 | Histogram correlation, pixel array operations |
| `Pillow` | ≥ 10.0 | Image I/O, crop, resize, color conversion |
| `plotly` | ≥ 5.18 | Radar chart, bar charts |
| `pandas` | ≥ 2.0 | Metric breakdown table |
| `streamlit` | ≥ 1.32 | Web UI |

---

*Generated for CheckinMe AI Profile Benchmarking Tool*
