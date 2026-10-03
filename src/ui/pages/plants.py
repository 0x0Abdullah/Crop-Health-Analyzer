from datetime import date, timedelta

import streamlit as st

from src.config import SUPPORTED_CROP_NAMES
from src.ui.components import callout, card_container, chip, esc, evidence_chip, html_table, page_header, section, severity_chip
from src.ui.state import default_crop, goto, toast

ENVS = ["Field", "Greenhouse", "Home garden", "Pot/container"]


def _age(planting_date: str) -> str:
    try:
        d = (date.today() - date.fromisoformat(planting_date)).days
    except (TypeError, ValueError):
        return ""
    if d < 0:
        return "planting date is in the future"
    return "planted today" if d == 0 else f"{d} day{'s' if d != 1 else ''} since planting"


def render(svc) -> None:
    repo = svc.repo
    settings = st.session_state.settings
    page_header("🌱", "My plants", "Keep a profile for each plant or plot, link assessments to it, and set follow-up reminders.")
    plants = repo.get_plants()

    with st.expander("➕ Add a plant", expanded=not plants):
        with st.form("plant_form", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Plant or plot name *", placeholder="e.g. Backyard tomatoes")
            crops = SUPPORTED_CROP_NAMES
            crop = b.selectbox("Crop", crops, index=crops.index(default_crop(settings)))
            c, d = st.columns(2)
            variety = c.text_input("Variety (optional)")
            planting = d.date_input("Planting date", value=date.today(), max_value=date.today() + timedelta(days=365))
            e, f = st.columns(2)
            location = e.text_input("Location (optional)")
            env = f.selectbox("Growing environment", ENVS)
            notes = st.text_area("Notes (optional)", max_chars=1200)
            if st.form_submit_button("Save plant", type="primary"):
                if not name.strip():
                    st.session_state["plant_form_error"] = True
                else:
                    repo.create_plant(name.strip(), crop, variety.strip(), planting.isoformat(), location.strip(), env, notes.strip())
                    toast(f"Saved “{name.strip()}”")
                    st.rerun()
        if st.session_state.pop("plant_form_error", False):
            callout("danger", "Please give the plant a name.")

    # ---------------------------------------------------------------- reminders
    reminders = repo.get_reminders()
    if reminders:
        section("🔔 Follow-up reminders")
        today = date.today().isoformat()
        for r in reminders:
            late = r["due_date"] < today
            c1, c2, c3 = st.columns([6, 1, 1])
            when = "overdue since " if late else ("due today · " if r["due_date"] == today else "due ")
            with c1:
                callout("danger" if late else ("warn" if r["due_date"] == today else "info"),
                        f'{r["note"]} — {r.get("plant_name") or "plant"} · {when}{r["due_date"]}')
            if c2.button("Done", key=f"rem_done_{r['id']}", use_container_width=True):
                repo.complete_reminder(r["id"]); toast("Reminder completed"); st.rerun()
            if c3.button("✕", key=f"rem_del_{r['id']}", use_container_width=True, help="Delete reminder"):
                repo.delete_reminder(r["id"]); st.rerun()

    section("Your plants")
    if not plants:
        callout("info", "No plants yet. Add your first one above to start tracking its health over time.")
        return

    for p in plants:
        timeline = repo.get_plant_timeline(p["id"])
        with card_container(f"plant_{p['id']}"):
            st.html(f'<div style="font-size:1.25rem;font-weight:800;color:var(--ink)">🌱 {esc(p["name"])}</div>'
                    f'<div style="margin:.35rem 0 .2rem">{chip(p["crop"], "ok")} {chip(p.get("growing_environment") or "—", "neutral")} '
                    f'{chip(_age(p.get("planting_date")), "info") if _age(p.get("planting_date")) else ""}</div>')
            bits = [f'Variety: {p["variety"]}' if p.get("variety") else "", f'Location: {p["location"]}' if p.get("location") else ""]
            if any(bits):
                st.caption(" · ".join(b for b in bits if b))
            if p.get("notes"):
                st.markdown(f"> {p['notes']}")
            if timeline:
                st.markdown("**Health timeline**")
                html_table([{**t, "created_at": t["created_at"][:10]} for t in timeline], ["created_at", "result_condition", "evidence_level", "severity"],
                           labels={"created_at": "Date", "result_condition": "Possible condition", "evidence_level": "Evidence"},
                           chips={"evidence_level": evidence_chip, "severity": lambda v: severity_chip(v).replace("Severity: ", "")})
            else:
                st.caption("No assessments linked to this plant yet.")

            a, b, c = st.columns(3)
            a.button("🔍 Analyze this plant", key=f"pl_an_{p['id']}", use_container_width=True, type="primary",
                     on_click=goto, args=("analyze",), kwargs={"an_prefill_plant": p["id"], "an_reset": True})
            with b.popover("🔔 Add reminder", use_container_width=True):
                rd = st.date_input("Recheck date", value=date.today() + timedelta(days=7), min_value=date.today(), key=f"rd_{p['id']}")
                rn = st.text_input("Reminder", "Recheck plant symptoms and take a new photo.", key=f"rn_{p['id']}")
                if st.button("Save reminder", type="primary", key=f"rs_{p['id']}"):
                    if rn.strip():
                        repo.create_reminder(p["id"], rd.isoformat(), rn.strip()); toast("Reminder saved", "🔔"); st.rerun()
            with c.popover("🗑️ Delete", use_container_width=True):
                st.write("Delete this plant and its reminders? Past assessments are kept but unlinked.")
                if st.button("Yes, delete plant", type="primary", key=f"pl_del_{p['id']}"):
                    repo.delete_plant(p["id"]); toast("Plant deleted", "🗑️"); st.rerun()
