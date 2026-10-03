"""Crop Health Analyzer — Streamlit entry point.

Layout: theme CSS -> sticky navigation -> the selected page (src/ui/pages/*).
Run with:  streamlit run app.py
"""
import streamlit as st

from src.config import APP_TITLE
from src.ui.components import scroll_to_top
from src.ui.pages import about, analyze, assistant, history, home, learn, plants, settings as settings_page
from src.ui.state import PAGES, get_services, goto, init_navigation, init_session, init_settings, sync_url
from src.ui.theme import build_css

st.set_page_config(page_title=APP_TITLE, page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

svc = get_services()
init_session()
prefs = init_settings(svc.repo)
page = init_navigation()

# Theme is applied on every run, after callbacks have updated the settings, so changes are instant.
st.markdown(build_css(prefs["theme"], prefs["text_size"], prefs["reduce_motion"]), unsafe_allow_html=True)

with st.container(key="topnav"):
    cols = st.columns(len(PAGES))
    for col, (pid, icon, label) in zip(cols, PAGES):
        col.button(f"{icon} {label}", key=f"nav_{pid}", use_container_width=True,
                   type="primary" if pid == page else "secondary", on_click=goto, args=(pid,))

RENDERERS = {"home": home.render, "analyze": analyze.render, "plants": plants.render, "history": history.render,
             "assistant": assistant.render, "learn": learn.render, "settings": settings_page.render, "about": about.render}

# the nav callback may have changed the page after the line above ran
page = st.session_state.page
sync_url(page)
if st.session_state.get("_rendered_page") != page:
    st.session_state["_rendered_page"] = page
    scroll_to_top(page)

RENDERERS.get(page, home.render)(svc)

st.html(f'<div class="cha-footer">🌱 {APP_TITLE} · AI-assisted agricultural decision support · No laboratory-confirmed diagnosis</div>')
