from datetime import date

import streamlit as st

from src.config import APP_TITLE, APP_SUBTITLE
from src.ui.components import (esc, callout, section, feature_grid, stat_grid, html_table, evidence_chip, severity_chip)
from src.ui.state import goto, toast


def render(svc) -> None:
    settings = st.session_state.settings
    repo = svc.repo
    st.html(
        f'<div class="cha-hero"><h1>🌱 {esc(APP_TITLE)}</h1><p><b>{esc(APP_SUBTITLE)}</b></p>'
        '<p>Upload photos and describe symptoms to identify possible plant health problems, '
        'then get evidence-based, IPM-first guidance you can act on today.</p></div>'
    )

    c1, c2 = st.columns([3, 2])
    c1.button("🔍 Start a new assessment", type="primary", use_container_width=True, on_click=goto, args=("analyze",), key="home_cta")
    c2.button("🤖 Ask the assistant", use_container_width=True, on_click=goto, args=("assistant",), key="home_ask")

    counts = repo.get_counts()
    stat_grid([
        {"value": counts["assessments"], "label": "Assessments saved"},
        {"value": counts["plants"], "label": "Plants tracked"},
        {"value": counts["open_reminders"], "label": "Open reminders"},
    ])

    if settings.get("show_reminders_home", True):
        due = repo.get_due_reminders()
        if due:
            section("🔔 Due follow-ups")
            today = date.today().isoformat()
            for r in due[:5]:
                late = r["due_date"] < today
                a, b = st.columns([5, 1])
                with a:
                    callout("danger" if late else "warn",
                            f'{r["note"]} — {r.get("plant_name") or "plant"} · {"overdue since" if late else "due"} {r["due_date"]}')
                if b.button("Done", key=f"home_rem_{r['id']}", use_container_width=True):
                    repo.complete_reminder(r["id"]); toast("Reminder completed"); st.rerun()

    section("What you can do")
    feature_grid([
        {"icon": "📷", "title": "Image analysis", "text": "Quality checks, guided photography and visual evidence from up to four photos."},
        {"icon": "📚", "title": "Evidence-based guidance", "text": "Agricultural knowledge retrieval with visible sources and honest uncertainty."},
        {"icon": "🌱", "title": "Plant monitoring", "text": "Plant profiles, health timelines, history and follow-up reminders."},
    ])
    callout("info", "For best results: photograph one affected leaf in focus, use even daylight, and include a whole-plant image when possible.", title="Tip")

    recent = repo.get_analysis_history(5)
    section("Recent assessments")
    rows = [{"date": r["created_at"][:10], "crop": r["crop"], "condition": r["result_condition"],
             "evidence": r.get("evidence_level"), "severity": r["severity"]} for r in recent]
    html_table(rows, ["date", "crop", "condition", "evidence", "severity"],
               empty="No assessments yet — start your first one above.",
               chips={"evidence": evidence_chip, "severity": lambda v: severity_chip(v).replace("Severity: ", "")})
    if recent:
        st.button("View all history →", on_click=goto, args=("history",), kwargs={"hist_view": "Saved assessments"}, key="home_hist")
