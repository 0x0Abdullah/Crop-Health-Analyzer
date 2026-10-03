import streamlit as st

from src.config import APP_TITLE, APP_VERSION
from src.ui.components import callout, feature_grid, page_header, section
from src.ui.pages.history import disclaimer


def render(svc) -> None:
    page_header("ℹ️", "About & safety", f"{APP_TITLE} · version {APP_VERSION}")
    section(f"What is {APP_TITLE}?")
    st.write("An AI-assisted agricultural decision-support app. It combines plant photos, reported symptoms and a curated agricultural knowledge base "
             "to help you understand possible crop health problems and decide what to do next, with an Integrated Pest Management (IPM) first approach.")
    feature_grid([
        {"icon": "🧠", "title": "Multi-agent pipeline", "text": "Input checks, photo features, symptom analysis, knowledge retrieval, risk fusion, IPM guidance and safety verification."},
        {"icon": "🔒", "title": "Private by default", "text": "Data stays in a local database. Photos are analysed in memory and not stored."},
        {"icon": "⚖️", "title": "Honest about uncertainty", "text": "Results show an evidence level and can say “insufficient evidence” instead of guessing."},
    ])
    section("Safety")
    st.write("AI assessments can be wrong, and similar conditions overlap. Treatment information must be verified against current local product labels, "
             "crop registration and agricultural guidance. Severe, fast-spreading or uncertain cases should be reviewed by a qualified professional.")
    disclaimer()
    section("Limitations")
    st.markdown("- Photo analysis is a lightweight colour/texture check, not a trained disease classifier.\n"
                "- The knowledge base covers a limited set of common conditions per crop.\n"
                "- No laboratory confirmation is performed.")
