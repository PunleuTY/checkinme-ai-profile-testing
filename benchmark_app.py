import streamlit as st
import requests
import base64
from PIL import Image
import io
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

import benchmark_metrics as bm

st.set_page_config(
    page_title="AI Profile Benchmark",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"

# ---------------------------------------------------------------------------
# Production outfit presets — replicated from AiProfileGenerateService.php
# ---------------------------------------------------------------------------
PRODUCTION_OUTFITS = {
    "male": [
        "wearing a tailored black suit jacket over a crisp white shirt and a black silk tie",
        "wearing a charcoal gray business suit jacket with a white shirt and a dark red tie",
        "wearing a navy blue suit jacket over a white shirt and a navy tie",
        "wearing a dark grey formal blazer with a light blue shirt and a dark grey tie",
        "wearing a classic black blazer over a white shirt and a silver tie",
        "wearing a dark blue suit jacket with a white shirt and a blue tie",
        "wearing a slate grey suit jacket over a white shirt and a black tie",
        "wearing a formal black suit jacket with a light grey shirt and a charcoal tie",
        "wearing a deep navy blazer with a crisp white shirt and a burgundy tie",
        "wearing a dark brown suit jacket over a cream shirt and a brown tie",
        "wearing a midnight blue suit jacket with a white shirt and a dark blue tie",
        "wearing a medium grey blazer over a white shirt and a navy tie",
        "wearing a clean black suit jacket over a light blue shirt and a dark blue tie",
        "wearing a formal dark grey suit jacket with a white shirt and a grey tie",
        "wearing a classic navy blazer over a light blue shirt and a navy tie",
        "wearing a sharp black suit jacket with a white shirt and a black tie",
    ],
    "female": [
        "wearing a tailored black blazer over a white blouse",
        "wearing a charcoal gray business blazer with a white top",
        "wearing a navy blue blazer over a clean white blouse",
        "wearing a dark grey formal blazer with a light blue blouse",
        "wearing a classic black blazer over a white scoop-neck top",
        "wearing a dark blue blazer with a white blouse",
        "wearing a slate grey blazer over a white top",
        "wearing a formal black blazer with a light grey blouse",
        "wearing a deep navy blazer with a crisp white blouse",
        "wearing a dark brown blazer over a cream blouse",
        "wearing a midnight blue blazer with a white top",
        "wearing a textured grey blazer over a white blouse",
        "wearing a clean black blazer over a light blue blouse",
        "wearing a formal dark grey blazer with a white blouse",
        "wearing a classic navy blazer over a light blue top",
        "wearing a sharp black blazer with a white blouse",
    ],
}

NEW_OUTFITS = {
    "male": [
        "wearing a burgundy suit jacket over a white shirt and a dark burgundy tie",
        "wearing a wine-red blazer with a white shirt and a black tie",
        "wearing a forest green suit jacket over a white shirt and a dark green tie",
        "wearing an olive green blazer over a cream shirt and a dark brown tie",
        "wearing a light grey suit jacket over a white shirt and a silver tie",
        "wearing a steel blue suit jacket over a white shirt and a dark blue tie",
        "wearing a cobalt blue blazer with a white shirt and a navy tie",
        "wearing a deep teal suit jacket over a white shirt and a dark teal tie",
        "wearing a dark plum blazer with a white shirt and a plum-toned tie",
        "wearing a double-breasted navy suit jacket over a white shirt with a white pocket square",
        "wearing a double-breasted charcoal suit jacket with a light blue shirt and a dark tie",
        "wearing a tailored black suit jacket with a white shirt, black tie, and a white pocket square",
        "wearing a slim-fit navy suit with a white shirt and a striped blue-silver tie",
        "wearing a modern slim-fit black tuxedo jacket over a white dress shirt with a black bow tie",
        "wearing a classic black suit jacket with a mock-neck black turtleneck underneath",
        "wearing a charcoal suit jacket over a dark navy turtleneck",
        "wearing a smart navy blazer over a white open-collar shirt, no tie",
        "wearing a dark grey blazer over a light blue open-collar shirt, business casual",
    ],
    "female": [
        "wearing a burgundy blazer over a white blouse with a delicate gold pendant necklace",
        "wearing a wine-red blazer with a cream blouse and small pearl stud earrings",
        "wearing a forest green blazer over a white blouse with a subtle gold chain necklace",
        "wearing an emerald green blazer with a white top and small gold hoop earrings",
        "wearing a cobalt blue blazer over a white blouse with a sapphire pendant necklace",
        "wearing a royal blue blazer with a white top and gold button earrings",
        "wearing a light grey blazer over a white blouse with a single-strand pearl necklace",
        "wearing a silver-grey blazer with a white top and diamond stud earrings",
        "wearing a camel-toned blazer over a white blouse with a thin gold chain",
        "wearing a warm tan blazer with a cream blouse and small gold hoop earrings",
        "wearing a tailored white blazer over a soft grey blouse with subtle pearl button earrings",
        "wearing an ivory blazer over a white blouse with minimal silver accessories",
        "wearing a classic black blazer over a silk white blouse with a silk neck scarf in navy",
        "wearing a navy blazer with a white blouse and a thin patterned silk scarf tied loosely",
        "wearing a charcoal grey blazer over a white blouse with a simple silver necklace",
        "wearing a dark grey blazer with a light pink blouse and rose gold stud earrings",
        "wearing a double-breasted black blazer over a white blouse with a subtle gold lapel pin",
        "wearing a structured double-breasted navy blazer with a white top and pearl drop earrings",
    ],
}

BACKGROUND_OPTIONS = {
    "Soft Neutral Grey": "soft neutral grey",
    "Pure White": "pure white",
    "Warm Light Beige": "warm light beige",
    "Light Sky Blue": "light sky blue",
    "Pale Mint / Off-White": "pale mint off-white",
}

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def build_production_prompt(gender: str, outfit_style: str) -> str:
    is_female = gender == "female"
    common_intro = f"Generate a portrait of a professional {'female' if is_female else 'male'} "
    common_features = (
        " STRICTLY PRESERVE the subject's original face. The output must look exactly like the person"
        " in the uploaded image. Do not alter facial structure, skin texture, or expression."
        " The body should be centered with a natural, professional pose."
        " Background must be a soft, solid, professional ID card style background."
    )
    hair_fix = (
        " PRESERVE the subject's original hairstyle — keep the same length, cut, parting, hairline,"
        " and natural hair color. If the hair in the uploaded photo looks raw, messy, or unkempt,"
        " neatly groom it into the closest PROFESSIONAL version of that same hairstyle: tame flyaways,"
        " smooth frizz and stray strands, and tidy the edges, WITHOUT changing the overall style,"
        " length, or color. The hair must always end up looking clean, groomed, and professional. "
    )
    if is_female:
        hair_fix += (
            " Be especially strict with the hair: keep the EXACT same hair length and keep it worn"
            " the same way as the original — loose or tied up, and the same ponytail, bun, or updo if"
            " present. Keep the same fringe/bangs, the same parting side, and the same way the hair"
            " falls over the shoulders. Do NOT lengthen, shorten, add volume, curl, straighten, or"
            " otherwise restyle it. "
        )
    neck_fix = (
        " Ensure the neck and shoulders are anatomically correct and proportional."
        " The clothing must fit naturally around the neck/collar area without floating or weird cuts. "
    )
    framing_fix = " Frame the image from the top of the head to the mid-chest. "
    outfit_fix = (
        " The attire must look fully professional and formal — well-fitted, clean, and wrinkle-free"
        " business clothing appropriate for a corporate ID / headshot. No casual, novelty, or"
        " non-professional clothing. "
    )
    if is_female:
        outfit_fix += (
            " Reproduce the specified attire and accessories EXACTLY as described — the same blazer,"
            " the same top/blouse, and only the necklace, earrings, or scarf that are named — with"
            " nothing added, removed, or substituted, and no extra jewelry, patterns, or buttons. "
        )
    image_quality = (
        " PHOTOREALISTIC style. The image must look like a high-end photograph."
        " No cartoonish, 3D render, or filtered looks."
        " Lighting should be natural studio lighting. "
    )
    return f"{common_intro} {outfit_style}.{common_features}{hair_fix}{framing_fix}{outfit_fix}{neck_fix}{image_quality}"


def build_experimental_prompt(
    gender: str, outfit_style: str, background_style: str = "seamless light grey studio backdrop"
) -> str:
    """Agency-studio headshot brief. Casting-agency / magazine realism (natural pores, beauty
    lighting, 85mm look) with the original face/hairstyle preserved and the clothing replaced
    with professional attire."""
    return (
        f"PROFESSIONAL PORTRAIT\n\n"
        f"Image edit directive, convert the subject from the input photo into a clean professional "
        f"studio headshot while preserving the exact face and hairstyle from the original image. "
        f"Keep the SAME hairstyle — identical length, cut, parting, hairline, natural hair color, and "
        f"overall shape — but always present a clean, groomed, professional version of it: tame "
        f"flyaways and frizz, smooth stray strands, and tidy the edges. If the hair in the original "
        f"photo looks raw, messy, or unkempt, neatly restyle it into the CLOSEST professional version "
        f"of that same hairstyle (same length, cut, and color) so it reads as polished and "
        f"office-appropriate, without switching to a different hairstyle. The hair must end up looking "
        f"professional in every case. "
        f"Replace the clothing with professional, formal business attire. Dress the subject in "
        f"{outfit_style}. The clothing must look fully professional — well-fitted, clean, and "
        f"wrinkle-free, with no casual or non-professional elements. Remove any non-professional items "
        f"the person is wearing in the original "
        f"photo — earphones, earbuds, headphones, hats, caps, sunglasses, lanyards, casual or "
        f"novelty jewelry, and similar accessories must NOT appear in the output. Only keep "
        f"prescription eyeglasses if the subject is wearing them. Studio portrait look. Tight head "
        f"and shoulders framing, "
        f"centered composition, neutral confident expression. Reposition the subject to face the "
        f"camera directly in a perfectly straight-on, front-facing pose — head level and upright "
        f"(not tilted), shoulders squared and parallel to the camera, body centered in the frame "
        f"with equal margins on the left and right, and eyes looking directly into the lens — even "
        f"if the original photo shows the person turned, angled, tilted, or posed to the left or "
        f"right. The subject must sit straight and symmetrical within the professional headshot "
        f"frame. "
        f"Professional talent headshot aesthetic used by casting agencies and magazine profiles. "
        f"Background a clean, solid, professional corporate ID-style {background_style} with soft "
        f"falloff. No visible texture, props, or environment. Lighting setup high end studio beauty "
        f"lighting. Large soft key light "
        f"slightly above eye level, centered but angled down. Soft fill from front to remove harsh "
        f"shadows. Subtle rim light behind shoulders for separation. Even illumination across face "
        f"with gentle shadow under jawline. Catchlights visible in both eyes. Camera perspective "
        f"eye level. Shot on common 85mm 118 portrait lenses. Crisp focus on eyes, shallow depth "
        f"of field so ears and shoulders fall slightly softer. Skin rendering realistic and "
        f"professional. Natural pores visible, subtle skin texture, no plastic smoothing. Balanced "
        f"color grading, neutral skin tones, clean contrast. Hair carefully groomed but natural. "
        f"Individual strands visible. The new clothing must look natural and realistic with "
        f"accurate fabric texture, folds, and color, well-fitted and wrinkle-free, with the collar "
        f"and neckline sitting naturally against the neck — no floating fabric or gaps, neck and "
        f"shoulders anatomically correct. Retouch level magazine professional but realistic. "
        f"Remove temporary blemishes only keep natural facial structure, freckles, pores, and fine "
        f"lines. Final look polished agency headshot. Neutral background, balanced lighting, "
        f"symmetrical framing, professional studio finish."
    )


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def call_gemini_api(
    api_key: str, image_b64: str, prompt: str, mime_type: str = "image/jpeg",
    url: str = GEMINI_URL,
):
    try:
        response = requests.post(
            f"{url}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64,
                                }
                            },
                        ]
                    }
                ],
            },
            timeout=180,
        )
        return response
    except Exception:
        return None


def parse_image_b64(response_json: dict):
    try:
        parts = response_json["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return part["inlineData"]["data"]
    except (KeyError, IndexError):
        pass
    return None


def b64_to_pil(b64_string: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64_string)))


def pil_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_result(label: str, response, key_suffix: str):
    st.markdown(f"### {label}")
    if response is None:
        st.error("Request failed — network error or timeout.")
        return None
    if response.status_code != 200:
        st.error(f"API error {response.status_code}")
        with st.expander("Error details"):
            st.code(response.text[:3000])
        return None
    try:
        resp_json = response.json()
    except Exception:
        st.error("Could not parse API response as JSON.")
        with st.expander("Raw response"):
            st.code(response.text[:3000])
        return None
    img_b64 = parse_image_b64(resp_json)
    if img_b64:
        img = b64_to_pil(img_b64)
        st.image(img, use_container_width=True)
        st.download_button(
            "⬇️ Download PNG",
            pil_to_bytes(img),
            file_name=f"{key_suffix}_result.png",
            mime="image/png",
            key=f"dl_{key_suffix}",
        )
        return img
    else:
        st.warning("Response received but contained no image data.")
        with st.expander("Raw response (inspect for errors)"):
            st.json(resp_json)
        return None


# ---------------------------------------------------------------------------
# Benchmark visualization helpers
# ---------------------------------------------------------------------------


def _score_color(score: float) -> str:
    if score >= 75:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def render_score_cards(prod_m: dict, exp_m: dict):
    """Render a row of metric cards showing both scores and the winner."""
    display_keys = bm.RADAR_METRICS + ["Sharpness", "Overall"]
    cols = st.columns(len(display_keys))
    for col, key in zip(cols, display_keys):
        p = prod_m.get(key, 0)
        e = exp_m.get(key, 0)
        winner = "Prod" if p >= e else "Exp"
        winner_icon = "🏭" if winner == "Prod" else "🧪"
        with col:
            st.metric(
                label=key,
                value=f"{max(p, e):.0f}",
                delta=f"{e - p:+.0f} (Exp vs Prod)",
                delta_color="normal",
            )
            st.caption(f"Prod {_score_color(p)} {p}  |  Exp {_score_color(e)} {e}")
            st.caption(f"Winner: {winner_icon} {winner}")


def render_radar_chart(prod_m: dict, exp_m: dict) -> go.Figure:
    cats = bm.RADAR_METRICS + [bm.RADAR_METRICS[0]]  # close the polygon
    prod_vals = [prod_m.get(c, 0) for c in cats]
    exp_vals = [exp_m.get(c, 0) for c in cats]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=prod_vals,
            theta=cats,
            fill="toself",
            name="Production",
            line_color="#2563EB",
            fillcolor="rgba(37,99,235,0.15)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=exp_vals,
            theta=cats,
            fill="toself",
            name="Experimental",
            line_color="#16A34A",
            fillcolor="rgba(22,163,74,0.15)",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="Metric Radar",
        height=420,
        margin=dict(l=30, r=30, t=50, b=30),
    )
    return fig


def render_bar_chart(prod_m: dict, exp_m: dict) -> go.Figure:
    keys = bm.RADAR_METRICS + ["Sharpness"]
    df = pd.DataFrame(
        {
            "Metric": keys * 2,
            "Score": [prod_m.get(k, 0) for k in keys] + [exp_m.get(k, 0) for k in keys],
            "Prompt": ["Production"] * len(keys) + ["Experimental"] * len(keys),
        }
    )
    fig = px.bar(
        df,
        x="Metric",
        y="Score",
        color="Prompt",
        barmode="group",
        color_discrete_map={"Production": "#2563EB", "Experimental": "#16A34A"},
        range_y=[0, 105],
        title="Score Comparison per Metric",
        height=380,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=80))
    fig.update_xaxes(tickangle=-35)
    return fig


def render_qualitative_section(key_prefix: str) -> dict:
    """Render star-rating sliders for qualitative assessment, return dict of ratings."""
    criteria = {
        "Face Resemblance": "Does the face look exactly like the person in the reference photo?",
        "Professional Look": "Does the overall image look like a professional headshot?",
        "Clothing Quality": "Does the clothing look natural, well-fitted, and realistic?",
        "Background Quality": "Is the background clean, solid, and professional?",
        "Overall Preference": "Overall, how satisfied are you with this image?",
    }
    ratings = {}
    for label, help_text in criteria.items():
        ratings[label] = st.slider(
            label, 1, 5, 3, help=help_text, key=f"{key_prefix}_{label}"
        )
    return ratings


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

for _k in ("ref_img", "prod_img", "exp_img", "prod_metrics", "exp_metrics"):
    if _k not in st.session_state:
        st.session_state[_k] = None

if "prompt_fingerprint" not in st.session_state:
    st.session_state["prompt_fingerprint"] = ""

for _k in ("fetched_models", "fetch_error"):
    if _k not in st.session_state:
        st.session_state[_k] = None

# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main():
    st.title("📸 AI Profile Generator — Prompt Benchmarking")
    st.caption(
        "Upload a headshot, pick a look, generate with both prompts, then compare quantitative + qualitative results."
    )

    # ---- Sidebar ----
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input(
            "Gemini API Key", type="password", placeholder="......"
        )

        # ---- Model selector with live fetch ----
        st.markdown("**Gemini Model**")
        _mhdr, _mbtn = st.columns([3, 1])
        with _mhdr:
            st.caption("Preset list or fetch all models for your key.")
        with _mbtn:
            _fetch_clicked = st.button(
                "🔍 Fetch",
                key="fetch_models_btn",
                disabled=not api_key,
                use_container_width=True,
                help="Call the Gemini models API and list every model your key can access.",
            )

        if _fetch_clicked and api_key:
            with st.spinner("Fetching models from Gemini API…"):
                try:
                    _r = requests.get(
                        "https://generativelanguage.googleapis.com/v1beta/models",
                        params={"key": api_key},
                        timeout=12,
                    )
                    if _r.status_code == 200:
                        _all = _r.json().get("models", [])
                        # Keep only models that support generateContent
                        st.session_state["fetched_models"] = [
                            m for m in _all
                            if "generateContent" in m.get("supportedGenerationMethods", [])
                        ]
                        st.session_state["fetch_error"] = None
                    else:
                        _err = _r.json().get("error", {})
                        st.session_state["fetch_error"] = (
                            f"HTTP {_r.status_code} — "
                            f"{_err.get('message', _r.text[:160])}"
                        )
                        st.session_state["fetched_models"] = None
                except Exception as _exc:
                    st.session_state["fetch_error"] = str(_exc)
                    st.session_state["fetched_models"] = None

        if st.session_state["fetch_error"]:
            st.error(st.session_state["fetch_error"])

        _fetched = st.session_state["fetched_models"]

        if _fetched is not None:
            # -- Filter toggle --
            _img_only = st.toggle(
                "Image generation models only",
                value=True,
                help="Filters to models whose name contains 'image' — the subset that "
                     "can output generated images rather than just text.",
            )
            _visible = (
                [m for m in _fetched if "image" in m["name"].lower()]
                if _img_only else _fetched
            )
            if not _visible:          # filter too aggressive — show all
                _visible = _fetched
                st.caption("No image models found — showing all generateContent models.")
            else:
                st.caption(
                    f"{'🖼 ' if _img_only else ''}"
                    f"{len(_visible)} model{'s' if len(_visible) != 1 else ''} found."
                )

            def _model_label(m):
                mid   = m["name"].split("/")[-1]
                dname = m.get("displayName", "")
                return f"{dname}  ({mid})" if dname else mid

            _label_to_id = {_model_label(m): m["name"].split("/")[-1] for m in _visible}
            _label_to_id["Custom model…"] = "__custom__"
            _labels = list(_label_to_id.keys())

            _sel_label = st.selectbox(
                "model_dynamic", _labels,
                label_visibility="collapsed",
                key="model_select_dynamic",
            )
            _chosen_id = _label_to_id[_sel_label]

            # Show model metadata
            if _chosen_id != "__custom__":
                _meta = next(
                    (m for m in _visible if m["name"].split("/")[-1] == _chosen_id), None
                )
                if _meta:
                    with st.expander("Model details", expanded=False):
                        if _meta.get("description"):
                            st.caption(_meta["description"])
                        _methods = _meta.get("supportedGenerationMethods", [])
                        st.caption(f"Methods: `{'`, `'.join(_methods)}`")
                        if _meta.get("inputTokenLimit"):
                            st.caption(f"Input token limit: {_meta['inputTokenLimit']:,}")
                        if _meta.get("outputTokenLimit"):
                            st.caption(f"Output token limit: {_meta['outputTokenLimit']:,}")
        else:
            # -- Static fallback when not yet fetched --
            _STATIC = {
                "gemini-2.5-flash-image": "gemini-2.5-flash-image",
                "gemini-2.0-flash-exp-image-generation": "gemini-2.0-flash-exp-image-generation",
                "Custom model…": "__custom__",
            }
            _sel_label = st.selectbox(
                "Gemini Model", list(_STATIC.keys()),
                help="Enter an API key and click 🔍 Fetch to load all models available to your key.",
            )
            _chosen_id = _STATIC[_sel_label]

        if _chosen_id == "__custom__":
            model_name = st.text_input("Model ID", placeholder="gemini-…")
        else:
            model_name = _chosen_id

        gemini_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            if model_name else GEMINI_URL
        )
        st.caption(f"`…/models/{model_name}:generateContent`")

        st.divider()
        st.header("👤 Subject")
        gender = st.radio("Gender", ["male", "female"], horizontal=True)

        st.divider()
        st.header("👔 Look Customization")
        st.caption("Applied to both prompts automatically.")

        # 5 curated outfit sets per gender. Each combination is hand-picked to
        # render naturally with the model; the first entry is the strongest look
        # and is used as the default.
        if gender == "male":
            outfit_sets = {
                "Black Suit · White Shirt · Black Tie":
                    "wearing a tailored black suit jacket over a crisp white shirt and a black silk tie",
                "Navy Suit · White Shirt · Navy Tie":
                    "wearing a navy blue suit jacket over a white shirt and a navy tie",
                "Charcoal Suit · Light Blue Shirt · Charcoal Tie":
                    "wearing a charcoal grey suit jacket over a light blue shirt and a charcoal tie",
                "Dark Grey Suit · White Shirt · Silver Tie":
                    "wearing a dark grey suit jacket over a white shirt and a silver tie",
                "Navy Blazer · White Shirt · Open Collar":
                    "wearing a smart navy blazer over a crisp white open-collar shirt, no tie",
            }
        else:
            outfit_sets = {
                "Black Blazer · White Blouse":
                    "wearing a tailored black blazer over a crisp white blouse",
                "Navy Blazer · White Blouse":
                    "wearing a navy blue blazer over a clean white blouse",
                "Charcoal Blazer · Light Blue Blouse":
                    "wearing a charcoal grey blazer over a light blue blouse",
                "Dark Grey Blazer · White Blouse":
                    "wearing a dark grey blazer over a white blouse",
                "Navy Blazer · White Top · Pearl Studs":
                    "wearing a navy blue blazer over a white top with small pearl stud earrings",
            }

        outfit_choice = st.selectbox("Outfit Set", list(outfit_sets.keys()))
        custom_outfit = outfit_sets[outfit_choice]

        st.divider()
        st.header("🖼️ Background")
        bg_choice = st.selectbox("Background Style", list(BACKGROUND_OPTIONS.keys()))
        background_style = BACKGROUND_OPTIONS[bg_choice]

    # ---- Upload ----
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        st.subheader("📁 Reference Image")
        uploaded_file = st.file_uploader(
            "Upload a front-facing headshot", type=["jpg", "jpeg", "png", "webp"]
        )
    with col_prev:
        if uploaded_file:
            ref_img = Image.open(uploaded_file)
            st.image(ref_img, caption="Input", use_container_width=True)
            st.session_state.ref_img = ref_img

    # ---------------------------------------------------------------------------
    # Prompt editor
    # ---------------------------------------------------------------------------
    default_prod = build_production_prompt(gender, custom_outfit)
    default_exp  = build_experimental_prompt(gender, custom_outfit, background_style)

    # Auto-reload editors whenever outfit / background changes
    fingerprint = f"{gender}|{custom_outfit}|{background_style}"
    if st.session_state["prompt_fingerprint"] != fingerprint:
        st.session_state["editor_prod"] = default_prod
        st.session_state["editor_exp"]  = default_exp
        st.session_state["prompt_fingerprint"] = fingerprint

    st.subheader("📝 Edit Prompts")
    st.caption(
        "Prompts are loaded from your sidebar selections. "
        "Edit either text area freely — your exact text is what gets sent to Gemini on generation."
    )

    ec1, ec2 = st.columns(2)
    with ec1:
        h1, b1 = st.columns([4, 1])
        with h1:
            st.markdown("**🏭 Production Prompt**")
        with b1:
            if st.button("↺ Reset", key="reset_prod", use_container_width=True, help="Restore to default production prompt"):
                st.session_state["editor_prod"] = default_prod
                st.rerun()
        prod_prompt = st.text_area(
            "prod_editor",
            key="editor_prod",
            height=360,
            label_visibility="collapsed",
        )
        st.caption(f"{len(prod_prompt):,} chars · {len(prod_prompt.split())} words")

    with ec2:
        h2, b2 = st.columns([4, 1])
        with h2:
            st.markdown("**🧪 Experimental — Agency Studio**")
        with b2:
            if st.button("↺ Reset", key="reset_exp", use_container_width=True, help="Restore to selected version preset"):
                st.session_state["editor_exp"] = default_exp
                st.rerun()
        exp_prompt = st.text_area(
            "exp_editor",
            key="editor_exp",
            height=360,
            label_visibility="collapsed",
        )
        st.caption(f"{len(exp_prompt):,} chars · {len(exp_prompt.split())} words")

    st.divider()

    if not api_key:
        st.info("Enter your Gemini API Key in the sidebar to enable generation.")

    gen_btn = st.button(
        "🚀 Generate & Compare",
        disabled=not (api_key and uploaded_file),
        use_container_width=True,
        type="primary",
    )

    if gen_btn:
        img_bytes = uploaded_file.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()
        ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
        mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }.get(ext, "image/jpeg")

        st.subheader("🔬 Side-by-Side Comparison")
        status = st.status("Generating both images in parallel…", expanded=True)
        with status:
            st.write("Calling Gemini — Production prompt…")
            st.write("Calling Gemini — Experimental prompt…")
            with ThreadPoolExecutor(max_workers=2) as ex:
                pf = ex.submit(call_gemini_api, api_key, img_b64, prod_prompt, mime, gemini_url)
                ef = ex.submit(call_gemini_api, api_key, img_b64, exp_prompt, mime, gemini_url)
                prod_resp = pf.result()
                exp_resp = ef.result()
            status.update(label="Generation complete", state="complete")

        r1, r2 = st.columns(2)
        with r1:
            prod_img = render_result("🏭 Production Prompt", prod_resp, "production")
            st.session_state.prod_img = prod_img
        with r2:
            exp_img = render_result("🧪 Experimental — Agency Studio", exp_resp, "experimental")
            st.session_state.exp_img = exp_img

        # Auto-compute metrics if both images generated
        if prod_img and exp_img and st.session_state.ref_img:
            with st.spinner("Computing benchmark metrics…"):
                st.session_state.prod_metrics = bm.compute_all(
                    st.session_state.ref_img, prod_img
                )
                st.session_state.exp_metrics = bm.compute_all(
                    st.session_state.ref_img, exp_img
                )

    # ---- Benchmark Results ----
    prod_m = st.session_state.prod_metrics
    exp_m = st.session_state.exp_metrics

    if prod_m and exp_m:
        st.divider()
        st.header("📊 Benchmark Results")

        # ---- Overall verdict ----
        p_overall = prod_m["Overall"]
        e_overall = exp_m["Overall"]
        diff = e_overall - p_overall
        if abs(diff) < 2:
            verdict = "⚖️ **Tie** — both prompts score within 2 points of each other."
        elif diff > 0:
            verdict = f"🧪 **Experimental wins** by **{diff:.1f} points** (Exp {e_overall} vs Prod {p_overall})"
        else:
            verdict = f"🏭 **Production wins** by **{abs(diff):.1f} points** (Prod {p_overall} vs Exp {e_overall})"

        st.subheader("Overall Verdict")
        st.info(verdict)

        ov1, ov2 = st.columns(2)
        with ov1:
            st.metric(
                "🏭 Production Overall",
                f"{p_overall:.1f} / 100",
                delta=f"{p_overall - e_overall:+.1f} vs Experimental",
            )
        with ov2:
            st.metric(
                "🧪 Experimental Overall",
                f"{e_overall:.1f} / 100",
                delta=f"{e_overall - p_overall:+.1f} vs Production",
            )

        st.divider()

        # ---- Score cards ----
        st.subheader("Per-Metric Score Cards")
        st.caption("🟢 ≥75  🟡 50-74  🔴 <50")
        render_score_cards(prod_m, exp_m)

        st.divider()

        # ---- Charts ----
        st.subheader("Visual Comparison")
        ch1, ch2 = st.columns(2)
        with ch1:
            st.plotly_chart(render_radar_chart(prod_m, exp_m), use_container_width=True)
        with ch2:
            st.plotly_chart(render_bar_chart(prod_m, exp_m), use_container_width=True)

        # ---- Detailed table ----
        with st.expander("🔍 Full Metric Breakdown Table"):
            all_keys = list(bm.METRIC_DESCRIPTIONS.keys())
            table_data = []
            for k in all_keys:
                if k not in prod_m:
                    continue
                p = prod_m[k]
                e = exp_m[k]
                winner = "🏭 Prod" if p >= e else "🧪 Exp"
                table_data.append(
                    {
                        "Metric": k,
                        "Description": bm.METRIC_DESCRIPTIONS.get(k, ""),
                        "Production": p,
                        "Experimental": e,
                        "Δ (Exp−Prod)": round(e - p, 1),
                        "Winner": winner,
                    }
                )
            df = pd.DataFrame(table_data)

            def _score_bg(val):
                if not isinstance(val, (int, float)):
                    return ""
                if val >= 75:
                    return "background-color: #bbf7d0; color: #14532d"  # green
                if val >= 50:
                    return "background-color: #fef08a; color: #713f12"  # yellow
                return "background-color: #fecaca; color: #7f1d1d"  # red

            def _delta_bg(val):
                if not isinstance(val, (int, float)):
                    return ""
                if val > 2:
                    return "color: #15803d; font-weight: bold"
                if val < -2:
                    return "color: #dc2626; font-weight: bold"
                return "color: #6b7280"

            styled = df.style.map(_score_bg, subset=["Production", "Experimental"]).map(
                _delta_bg, subset=["Δ (Exp−Prod)"]
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

        st.divider()

        # ---- Qualitative ratings ----
        st.subheader("⭐ Qualitative Ratings  (your human judgment)")
        st.caption(
            "Rate each image on the criteria below (1 = poor, 5 = excellent). Scores are combined with the quantitative results."
        )

        qc1, qc2 = st.columns(2)
        with qc1:
            st.markdown("#### 🏭 Production")
            prod_ratings = render_qualitative_section("prod")
        with qc2:
            st.markdown("#### 🧪 Experimental")
            exp_ratings = render_qualitative_section("exp")

        if st.button("📝 Calculate Qualitative Score", use_container_width=True):
            prod_qual = sum(prod_ratings.values()) / len(prod_ratings) * 20  # 0-100
            exp_qual = sum(exp_ratings.values()) / len(exp_ratings) * 20

            st.divider()
            st.subheader("🏆 Final Combined Score")

            # Combined = 60% quantitative + 40% qualitative
            prod_final = 0.60 * p_overall + 0.40 * prod_qual
            exp_final = 0.60 * e_overall + 0.40 * exp_qual

            fc1, fc2 = st.columns(2)
            with fc1:
                st.metric(
                    "🏭 Production Final",
                    f"{prod_final:.1f} / 100",
                    help="60% quantitative + 40% qualitative",
                )
            with fc2:
                st.metric(
                    "🧪 Experimental Final",
                    f"{exp_final:.1f} / 100",
                    help="60% quantitative + 40% qualitative",
                )

            final_diff = exp_final - prod_final
            if abs(final_diff) < 2:
                final_verdict = "⚖️ **Tie** — both prompts are virtually equivalent."
            elif final_diff > 0:
                final_verdict = f"🧪 **Experimental wins** overall — {final_diff:.1f} pts ahead (Quant + Human judgment)"
            else:
                final_verdict = f"🏭 **Production wins** overall — {abs(final_diff):.1f} pts ahead (Quant + Human judgment)"

            st.success(final_verdict)

            # Breakdown bar
            breakdown = pd.DataFrame(
                {
                    "Component": ["Quantitative", "Qualitative", "Final"] * 2,
                    "Score": [
                        p_overall,
                        prod_qual,
                        prod_final,
                        e_overall,
                        exp_qual,
                        exp_final,
                    ],
                    "Prompt": ["Production"] * 3 + ["Experimental"] * 3,
                }
            )
            fig_final = px.bar(
                breakdown,
                x="Component",
                y="Score",
                color="Prompt",
                barmode="group",
                color_discrete_map={"Production": "#2563EB", "Experimental": "#16A34A"},
                range_y=[0, 105],
                title="Final Score Breakdown",
                height=350,
            )
            st.plotly_chart(fig_final, use_container_width=True)


if __name__ == "__main__":
    main()
