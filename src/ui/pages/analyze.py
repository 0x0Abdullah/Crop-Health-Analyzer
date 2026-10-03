import io
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image

from src.config import SUPPORTED_CROP_NAMES
from src.ui.components import callout, chip, esc, page_header, section
from src.ui.state import default_crop, goto
from src.utils.image_utils import MAX_FILE_SIZE_MB, validate_image_file

MAX_PHOTOS = 4
SYMPTOM_OPTIONS = ["Yellow leaves", "Brown spots", "White powder", "Wilting", "Curling leaves", "Holes in leaves", "Water-soaked areas",
                   "Stem lesions", "Fruit damage", "Root problems", "Stunted growth", "Rapid spreading"]
WHEN_OPTIONS = ["Not sure", "Today", "2–3 days ago", "About a week ago", "More than a week ago"]
SPREAD_OPTIONS = ["Not sure", "No", "Slowly", "Quickly"]
PART_OPTIONS = ["Not sure", "Leaves", "Stem", "Fruit", "Roots", "Whole plant"]
ENV_OPTIONS = ["Not provided", "Field", "Greenhouse", "Home garden", "Pot/container"]
FORM_KEYS = ["an_crop", "an_plant", "an_symptoms", "an_when", "an_spread", "an_part", "an_notes", "an_loc", "an_env", "an_cam"]
QUALITY_LABEL = {"good": ("Good", "ok"), "blurry": ("Blurry", "warn"), "dark": ("Too dark", "warn"), "overexposed": ("Overexposed", "warn")}


@st.cache_data(show_spinner=False, max_entries=32)
def _validate(data: bytes, name: str) -> Dict[str, Any]:
    return validate_image_file(data, name)


def _thumbnail(data: bytes, size: int = 360) -> bytes:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((size, size))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82)
    return out.getvalue()


def build_symptom_text(symptoms: List[str], notes: str, spreading: str, part: str) -> str:
    """Only include what the user actually told us (no boilerplate that could skew the analysis)."""
    parts = list(symptoms)
    if notes.strip():
        parts.append(notes.strip())
    text = "; ".join(parts)
    extra = []
    if spreading == "Quickly":
        extra.append("Spreading rapidly.")
    elif spreading == "Slowly":
        extra.append("Spreading slowly.")
    if part != "Not sure":
        extra.append(f"Affected part: {part.lower()}.")
    return (text + (". " if text and extra else "") + " ".join(extra)).strip()


def _plant_labels(plants: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {f'{p["name"]} — {p["crop"]} (#{p["id"]})': p for p in plants}


def render(svc) -> None:
    settings = st.session_state.settings
    repo = svc.repo
    page_header("🔍", "Crop health assessment", "Add photos and/or describe what you see. Everything except the crop is optional, but more detail gives better results.")

    # reset form after a finished assessment, honour "Analyze this plant" shortcuts
    nonce = st.session_state.setdefault("an_nonce", 0)
    if st.session_state.pop("an_reset", False):
        for k in FORM_KEYS:
            st.session_state.pop(k, None)
        st.session_state.pop("an_quality_prompt", None)
        nonce = st.session_state["an_nonce"] = nonce + 1

    plants = repo.get_plants()
    by_label = _plant_labels(plants)
    plant_labels = ["No plant selected"] + list(by_label)
    prefill = st.session_state.pop("an_prefill_plant", None)
    if prefill:
        for lab, p in by_label.items():
            if p["id"] == prefill:
                st.session_state["an_plant"] = lab
    if st.session_state.get("an_plant") not in plant_labels:
        st.session_state["an_plant"] = "No plant selected"

    # ------------------------------------------------------------ 1. what
    section("1 · What are you checking?")
    c1, c2 = st.columns(2)
    plant_choice = c1.selectbox("Plant record (optional)", plant_labels, key="an_plant", help="Link this assessment to a plant to build its health timeline.")
    plant = by_label.get(plant_choice)
    if plant:
        st.session_state["an_crop"] = plant["crop"]
    elif st.session_state.get("an_crop") not in SUPPORTED_CROP_NAMES:
        st.session_state["an_crop"] = default_crop(settings)
    crop = c2.selectbox("Crop", SUPPORTED_CROP_NAMES, key="an_crop", disabled=bool(plant),
                        help="Taken from the plant record when one is selected." if plant else None)
    plant_id = plant["id"] if plant else None

    # ------------------------------------------------------------ 2. photos
    section("2 · Photos")
    st.caption("Best set: affected leaf, a healthy leaf for comparison, the whole plant, and stem/fruit/roots if relevant.")
    uploads = st.file_uploader(f"Upload up to {MAX_PHOTOS} photos (JPG or PNG, max {MAX_FILE_SIZE_MB} MB each)", type=["jpg", "jpeg", "png"],
                               accept_multiple_files=True, key=f"an_files_{nonce}")
    items: List[Dict[str, Any]] = [{"name": f.name, "bytes": f.getvalue()} for f in (uploads or [])]
    if st.toggle("📷 Take a photo with the camera", key="an_cam"):
        cam = st.camera_input("Camera", key=f"an_camera_{nonce}", label_visibility="collapsed")
        if cam:
            items.append({"name": "camera.jpg", "bytes": cam.getvalue()})
    if len(items) > MAX_PHOTOS:
        callout("warn", f"Only the first {MAX_PHOTOS} photos will be used ({len(items)} added).")
        items = items[:MAX_PHOTOS]

    validations = [_validate(i["bytes"], i["name"]) for i in items]
    if items:
        cols = st.columns(MAX_PHOTOS)  # fixed 4-column grid keeps thumbnails a sensible size
        for col, it, v in zip(cols, items, validations):
            with col:
                if v["valid"]:
                    st.image(it["bytes"], use_container_width=True)
                    label, kind = QUALITY_LABEL.get(v.get("quality"), (str(v.get("quality", "")).title(), "neutral"))
                    st.html(f'{chip(label, kind)}<div class="cha-muted" style="font-size:.82rem;margin-top:4px;word-break:break-all">{esc(it["name"])}</div>')
                    if v.get("quality_warning"):
                        st.caption(v["quality_warning"])
                    if settings.get("show_quality_details"):
                        st.caption(f'{v.get("width")}×{v.get("height")} px · sharpness {v.get("sharpness_score")} · brightness {v.get("brightness_score")}')
                else:
                    st.html(f'{chip("Problem", "danger")}<div class="cha-muted" style="font-size:.82rem;margin-top:4px;word-break:break-all">{esc(it["name"])}</div>')
                    st.caption(v.get("error") or "This file could not be used.")

    # ------------------------------------------------------------ 3. symptoms
    section("3 · What are you seeing?")
    symptoms = st.multiselect("Observed symptoms", SYMPTOM_OPTIONS, key="an_symptoms", placeholder="Select all that apply")
    c1, c2, c3 = st.columns(3)
    when = c1.selectbox("First noticed", WHEN_OPTIONS, key="an_when")
    spreading = c2.selectbox("Is it spreading?", SPREAD_OPTIONS, key="an_spread")
    part = c3.selectbox("Main affected part", PART_OPTIONS, key="an_part")
    notes = st.text_area("Anything else? (optional)", max_chars=1200, key="an_notes", height=100,
                         placeholder="e.g. rings on the lower leaves, started after heavy rain, only on the south side…")
    with st.expander("🌦️ Growing details (optional)"):
        st.caption("Saved with the assessment for your records.")
        d1, d2 = st.columns(2)
        location = d1.text_input("Region / location", key="an_loc")
        environment = d2.selectbox("Growing environment", ENV_OPTIONS, key="an_env")

    symptom_text = build_symptom_text(symptoms, notes, spreading, part)
    has_text_input = bool(symptoms) or len(notes.strip()) >= 5
    valid_items = [(i, v) for i, v in zip(items, validations) if v["valid"]]
    bad_items = [(i, v) for i, v in zip(items, validations) if not v["valid"]]
    low_quality = any(v.get("quality") in ("blurry", "dark", "overexposed") for _, v in valid_items)

    st.html(f'<div class="cha-muted" style="margin:.8rem 0 .3rem">Ready to analyze: <b>{len(valid_items)}</b> photo(s) · <b>{len(symptoms)}</b> symptom(s) selected'
            f'{" · notes added" if len(notes.strip()) >= 5 else ""}</div>')

    run_now = False
    if st.button("🔍 Analyze crop", type="primary", use_container_width=True, key="an_run"):
        st.session_state["an_quality_prompt"] = False
        if bad_items:
            callout("danger", "Remove the photo(s) marked “Problem” above (or replace them), then try again.", title="Some files can't be used")
        elif not valid_items and not has_text_input:
            callout("warn", "Add at least one readable photo, select a symptom, or describe what you see (a few words is enough).", title="Nothing to analyze yet")
        elif low_quality:
            st.session_state["an_quality_prompt"] = True
        else:
            run_now = True

    if st.session_state.get("an_quality_prompt") and not run_now:
        callout("warn", "At least one photo is blurry, dark or overexposed. A clearer close-up in daylight usually improves the result, "
                        "but you can continue with what you have.", title="Photo quality is limited")
        a, b = st.columns(2)
        if a.button("Analyze anyway", type="primary", use_container_width=True, key="an_anyway"):
            st.session_state["an_quality_prompt"] = False
            run_now = True
        if b.button("I'll retake the photos", use_container_width=True, key="an_retake"):
            st.session_state["an_quality_prompt"] = False
            st.rerun()

    if run_now:
        env = {"location": location, "growing_environment": environment, "first_noticed": when,
               "spreading": spreading, "affected_part": part}
        _run(svc, crop, plant_id, symptom_text, valid_items, env)


def _run(svc, crop: str, plant_id: Optional[int], symptom_text: str, valid_items, env: Dict[str, Any]) -> None:
    settings = st.session_state.settings
    byte_list = [i["bytes"] for i, _ in valid_items]
    meta = [{"filename": i["name"], **{k: v.get(k) for k in ("width", "height", "quality", "sharpness_score", "brightness_score")}} for i, v in valid_items]
    status = st.status("Running assessment…", expanded=True)
    bar = st.progress(0)

    def prog(msg: str, pct: float) -> None:
        status.write(msg)
        bar.progress(min(100, int(pct * 100)))

    try:
        result = svc.pipeline.run(crop=crop, symptoms=symptom_text, image_bytes=byte_list[0] if byte_list else None,
                                  image_bytes_list=byte_list, image_name=valid_items[0][0]["name"] if valid_items else None,
                                  environment=env, plant_id=plant_id, progress_callback=prog, image_metadata=meta)
    except Exception as exc:  # never show a raw traceback to the user
        status.update(label="Assessment failed", state="error", expanded=False)
        bar.empty()
        callout("danger", f"Something went wrong while analyzing ({type(exc).__name__}). Please try again; if it keeps happening, check the app log.", title="Assessment failed")
        return

    if not result.get("validation", {}).get("valid", False):
        status.update(label="Input needs attention", state="error", expanded=False)
        bar.empty()
        callout("danger", " ".join(result.get("errors") or ["The input could not be validated."]), title="Please check your input")
        return

    result["image_count"] = len(byte_list)
    result["environment"] = env
    result["thumbnails"] = [_thumbnail(b) for b in byte_list]
    st.session_state.current_analysis = result
    status.update(label="Assessment complete", state="complete", expanded=False)
    bar.empty()
    if result.get("analysis_id", -1) <= 0:
        callout("warn", "The assessment finished but could not be saved to your history.", title="Not saved")
    if settings.get("auto_open_results", True):
        goto("history", hist_view="Latest result", an_reset=True)
        st.rerun()
    else:
        callout("ok", "Your assessment is ready.", title="Done")
        st.button("View results →", type="primary", on_click=goto, args=("history",), kwargs={"hist_view": "Latest result", "an_reset": True}, key="an_view")
