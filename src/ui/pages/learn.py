import streamlit as st

from src.rag.loader import load_knowledge_documents
from src.ui.components import bullet_list, callout, chip, esc, page_header, section, steps

GLOSSARY = [
    ("IPM (Integrated Pest Management)", "A step-wise approach: prevent problems, monitor, use cultural and biological controls first, and chemicals only when needed."),
    ("Scouting", "Regularly inspecting plants (at least weekly) to catch problems early. Dated photos make changes easy to track."),
    ("PHI (Pre-Harvest Interval)", "The minimum number of days between the last pesticide application and harvest. It is printed on the product label."),
    ("REI (Re-Entry Interval)", "How long people must stay out of a treated area. Also on the label."),
    ("Evidence level", "How strongly the available information supports a result: strong, moderate, limited or insufficient."),
    ("Extension service", "Government or university advisers who give local, practical crop-protection advice, often free."),
]


@st.cache_data(show_spinner=False)
def _library():
    docs = [d for d in load_knowledge_documents() if isinstance(d, dict)]
    return sorted(docs, key=lambda d: (str(d.get("crop")), str(d.get("condition"))))


def render(svc) -> None:
    page_header("📚", "Learn", "How assessments work, how to take useful photos, and a library of the conditions in the knowledge base.")
    # state-backed selector instead of st.tabs: changing the library's crop filter reruns the script, and tabs would reset
    names = ["How it works", "Photo tips", "Disease library", "Glossary"]
    sec = st.radio("Topic", names, horizontal=True, key="learn_section", label_visibility="collapsed")
    st.divider()

    if sec == names[0]:
        section("How an assessment works")
        steps(["Image quality check", "Structured symptom assessment", "Visual feature analysis", "Agricultural knowledge retrieval",
               "Evidence fusion and uncertainty", "IPM-first guidance", "Safety verification", "Plant history and follow-up"])
        section("Evidence levels")
        st.html('<div class="cha-grid">'
                f'<div class="cha-card flat">{chip("Strong evidence", "ok")}<p style="margin-top:.5rem">Multiple evidence sources agree.</p></div>'
                f'<div class="cha-card flat">{chip("Moderate evidence", "info")}<p style="margin-top:.5rem">Several indicators match, but alternatives remain possible.</p></div>'
                f'<div class="cha-card flat">{chip("Limited evidence", "warn")}<p style="margin-top:.5rem">Some indicators match; more information is needed.</p></div>'
                f'<div class="cha-card flat">{chip("Insufficient evidence", "neutral")}<p style="margin-top:.5rem">Not enough to reliably tell the condition.</p></div></div>')
        callout("info", "The system is allowed to say “insufficient evidence” rather than forcing a guess. Photo analysis is a lightweight colour/texture check, so it supports — but never replaces — your symptom details and expert advice.")

    if sec == names[1]:
        section("Taking photos that work")
        steps(["Use natural daylight; avoid flash, harsh sun glare and deep shade.",
               "Hold the camera 20–30 cm from one affected leaf and make sure it is in sharp focus.",
               "Include some healthy tissue next to the damage for comparison.",
               "Add a whole-plant photo so the spread pattern is visible.",
               "Photograph the underside of the leaf, stem or fruit if you see symptoms there.",
               "Retake blurry or dark photos — the app will warn you."])

    if sec == names[2]:
        docs = _library()
        if not docs:
            callout("info", "The knowledge base is empty.")
        else:
            crops = sorted({str(d.get("crop")) for d in docs})
            crop = st.selectbox("Crop", ["All crops"] + crops, key="lib_crop")
            shown = [d for d in docs if crop == "All crops" or d.get("crop") == crop]
            st.caption(f"{len(shown)} condition(s)")
            for d in shown:
                with st.expander(f"🌿 {d.get('title') or d.get('condition')}"):
                    st.html(f'{chip(str(d.get("crop")), "ok")} {chip(str(d.get("category", "Condition")), "neutral")}')
                    st.markdown(str(d.get("content", "")))
                    for head, key in [("Typical signs", "symptoms"), ("Do now", "immediate_actions"), ("Prevention", "prevention"),
                                      ("IPM", "ipm"), ("Biological controls", "biological_controls"), ("Treatment information", "verified_treatments")]:
                        vals = d.get(key)
                        if vals:
                            st.markdown(f"**{head}**")
                            bullet_list(vals if isinstance(vals, list) else [vals])
                    st.caption(f"Source: {d.get('source', 'Agricultural extension')}" + (f" · [Open source]({d['url']})" if d.get("url") else "")
                               + " · Always verify product labels and local rules.")

    if sec == names[3]:
        for term, text in GLOSSARY:
            with st.expander(term):
                st.write(text)
