"""
Portrait benchmarking metrics.
All public functions accept PIL Images and return scores 0-100 (higher = better).
"""

import numpy as np
import cv2
from PIL import Image
from skimage.metrics import structural_similarity
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

def _to_gray(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("L"))

# ---------------------------------------------------------------------------
# Face detection
# ---------------------------------------------------------------------------

_CASCADE = None

def _get_cascade():
    global _CASCADE
    if _CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _CASCADE = cv2.CascadeClassifier(path)
    return _CASCADE

def detect_face(img: Image.Image) -> Optional[Tuple[int, int, int, int]]:
    """Return (x, y, w, h) of the largest detected face, or None."""
    gray = _to_gray(img)
    faces = _get_cascade().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    if len(faces) == 0:
        return None
    return tuple(max(faces, key=lambda f: f[2] * f[3]))

# ---------------------------------------------------------------------------
# Individual metrics
# ---------------------------------------------------------------------------

def score_sharpness(img: Image.Image) -> float:
    """Overall image clarity via Laplacian variance (0-100)."""
    gray = _to_gray(img)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(100.0, (lap_var / 1500.0) * 100.0))


def score_face_sharpness(img: Image.Image) -> float:
    """Sharpness within the detected face region (0-100)."""
    face = detect_face(img)
    if face is None:
        return score_sharpness(img)
    x, y, w, h = face
    pad = int(w * 0.1)
    crop = img.crop((x + pad, y + pad, x + w - pad, y + h - pad))
    gray = _to_gray(crop)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(100.0, (lap_var / 1500.0) * 100.0))


def score_background_uniformity(img: Image.Image) -> float:
    """
    Variance of corner pixels as a proxy for solid / uniform background.
    0-100, higher = more uniform (better for professional portraits).
    """
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    m = max(12, int(min(h, w) * 0.07))
    corners = np.concatenate([
        arr[:m,    :m   ].reshape(-1, 3),
        arr[:m,  w-m:   ].reshape(-1, 3),
        arr[h-m:,  :m   ].reshape(-1, 3),
        arr[h-m:, w-m:  ].reshape(-1, 3),
    ])
    std = corners.std()
    return float(max(0.0, 100.0 - (std / 60.0) * 100.0))


def score_framing(img: Image.Image) -> float:
    """
    Face height should occupy 30-65 % of image height for a
    head-to-mid-chest portrait framing (0-100).
    """
    face = detect_face(img)
    if face is None:
        return 0.0
    _, _, _, fh = face
    ratio = fh / img.size[1]
    lo, hi = 0.30, 0.65
    if lo <= ratio <= hi:
        return 100.0
    dist = min(abs(ratio - lo), abs(ratio - hi))
    return float(max(0.0, 100.0 - (dist / 0.20) * 100.0))


def score_face_centering(img: Image.Image) -> float:
    """How horizontally centered the face is in the frame (0-100)."""
    face = detect_face(img)
    if face is None:
        return 0.0
    x, _, w, _ = face
    face_cx = x + w / 2.0
    img_cx = img.size[0] / 2.0
    offset_ratio = abs(face_cx - img_cx) / img_cx
    return float(max(0.0, 100.0 - offset_ratio * 200.0))


def score_exposure(img: Image.Image) -> float:
    """
    Mean luminance in the ideal studio portrait range (90-175).
    0-100, higher = better exposed.
    """
    gray = _to_gray(img)
    mean = float(gray.mean())
    lo, hi = 90.0, 175.0
    if lo <= mean <= hi:
        return 100.0
    if mean < lo:
        return max(0.0, (mean / lo) * 100.0)
    return max(0.0, ((255.0 - mean) / (255.0 - hi)) * 100.0)


def score_skin_tone_match(reference: Image.Image, generated: Image.Image) -> float:
    """
    Correlation of face-region color histograms (R + G channels, which are
    most sensitive to skin tone). 0-100.
    """
    ref_box = detect_face(reference)
    gen_box = detect_face(generated)
    if ref_box is None or gen_box is None:
        return 50.0

    def face_arr(img, box):
        x, y, w, h = box
        return np.array(img.convert("RGB").crop((x, y, x + w, y + h)), dtype=np.uint8)

    ref_arr = face_arr(reference, ref_box)
    gen_arr = face_arr(generated, gen_box)

    scores = []
    for ch in (0, 1):  # R, G
        h_ref = np.histogram(ref_arr[:, :, ch], bins=32, range=(0, 256))[0].astype(float)
        h_gen = np.histogram(gen_arr[:, :, ch], bins=32, range=(0, 256))[0].astype(float)
        h_ref /= h_ref.sum() + 1e-9
        h_gen /= h_gen.sum() + 1e-9
        corr = float(np.corrcoef(h_ref, h_gen)[0, 1])
        scores.append(max(0.0, (corr + 1.0) / 2.0 * 100.0))

    return float(np.mean(scores))


def score_face_ssim(reference: Image.Image, generated: Image.Image) -> Optional[float]:
    """
    SSIM between face regions of reference and generated image.
    Acts as an objective face-identity-preservation score. 0-100.
    Returns None if a face cannot be detected in either image.
    """
    ref_box = detect_face(reference)
    gen_box = detect_face(generated)
    if ref_box is None or gen_box is None:
        return None

    TARGET = (96, 96)

    def face_patch(img, box):
        x, y, w, h = box
        crop = img.convert("L").crop((x, y, x + w, y + h)).resize(TARGET, Image.LANCZOS)
        return np.array(crop)

    ssim = structural_similarity(
        face_patch(reference, ref_box),
        face_patch(generated, gen_box),
        data_range=255,
    )
    return float(max(0.0, (ssim + 1.0) / 2.0 * 100.0))


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

METRIC_WEIGHTS = {
    "Face SSIM": 0.25,
    "Skin Tone Match": 0.20,
    "Face Sharpness": 0.20,
    "Background Uniformity": 0.15,
    "Framing": 0.10,
    "Face Centering": 0.05,
    "Exposure": 0.05,
}

METRIC_DESCRIPTIONS = {
    "Sharpness":             "Overall image clarity (Laplacian variance)",
    "Face Sharpness":        "Focus quality within the detected face region",
    "Background Uniformity": "How solid / uniform the background is",
    "Framing":               "Face occupies correct portion of the frame",
    "Face Centering":        "Face is horizontally centered",
    "Exposure":              "Luminance in the ideal studio portrait range",
    "Skin Tone Match":       "Face-region color histogram similarity vs reference",
    "Face SSIM":             "Structural similarity of face region vs reference photo",
    "Overall":               "Weighted composite of all metrics above",
}

RADAR_METRICS = [
    "Face SSIM", "Skin Tone Match", "Face Sharpness",
    "Background Uniformity", "Framing", "Face Centering", "Exposure",
]


def compute_all(reference: Image.Image, generated: Image.Image) -> dict:
    """
    Compute every metric and the overall weighted score.
    Returns {metric_name: score_0_to_100}.
    """
    face_ssim = score_face_ssim(reference, generated)

    raw = {
        "Sharpness":             score_sharpness(generated),
        "Face Sharpness":        score_face_sharpness(generated),
        "Background Uniformity": score_background_uniformity(generated),
        "Framing":               score_framing(generated),
        "Face Centering":        score_face_centering(generated),
        "Exposure":              score_exposure(generated),
        "Skin Tone Match":       score_skin_tone_match(reference, generated),
        "Face SSIM":             face_ssim if face_ssim is not None else 50.0,
    }

    overall = sum(raw.get(k, 50.0) * w for k, w in METRIC_WEIGHTS.items())
    raw["Overall"] = overall

    return {k: round(v, 1) for k, v in raw.items()}
