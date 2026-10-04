import json
import platform
from datetime import date

import streamlit as st

from src.config import APP_VERSION, DATABASE_PATH, SUPPORTED_CROP_NAMES
from src.rag.loader import load_knowledge_documents
from src.settings import TEXT_SIZES, THEMES
from src.ui.components import callout, chip, esc, key_values, page_header, section, stat_grid
from src.ui.installer_ui import render_install_section
from src.ui.state import default_crop, restore_defaults, toast, update_setting

THEME_LABELS = {"System": "🖥️ System", "Light": "☀️ Light", "Dark": "🌙 Dark"}
SIZE_LABELS = {"Small": "Small", "Default": "Default", "Large": "Large"}


def _saver(repo, key: str, widget_key: str):
    def _cb() -> None:
        update_setting(repo, key, st.session_state[widget_key])
        toast("Setting saved")
    return _cb


def _danger_action(label: str, key: str, text: str, action) -> None:
    """Destructive action guarded by a popover (a deliberate second click) with an explicit confirm button."""
    with st.popover(label, use_container_width=True):
        st.write(text)
        st.caption("This cannot be undone.")
        if st.button("Yes, delete permanently", type="primary", key=f"{key}_go"):
            action()
            toast("Deleted", "🗑️")
            st.rerun()


def render(svc) -> None:
    repo = svc.repo
    s = st.session_state.settings
    page_header("⚙️", "Settings", "Changes are saved automatically and remembered the next time you open the app.")
    # A state-backed selector (not st.tabs): every setting change reruns the script, and st.tabs would jump back to the first tab.
    sections = ["🎨 Appearance", "🧭 Preferences", "🤖 AI & engine", "🗂️ Data & privacy", "📲 Install & about"]
    sec = st.radio("Settings section", sections, horizontal=True, key="set_section", label_visibility="collapsed")
    st.divider()

    # ------------------------------------------------------------ appearance
    if sec == sections[0]:
        section("Theme")
        st.radio("Theme", THEMES, index=THEMES.index(s["theme"]), format_func=THEME_LABELS.get, horizontal=True, key="w_theme",
                 on_change=_saver(repo, "theme", "w_theme"), label_visibility="collapsed")
        st.caption("System follows your device's light/dark setting automatically.")
        section("Text size")
        st.radio("Text size", TEXT_SIZES, index=TEXT_SIZES.index(s["text_size"]), format_func=SIZE_LABELS.get, horizontal=True, key="w_size",
                 on_change=_saver(repo, "text_size", "w_size"), label_visibility="collapsed")
        st.toggle("Reduce motion (turn off animations)", value=s["reduce_motion"], key="w_motion", on_change=_saver(repo, "reduce_motion", "w_motion"))
        section("Preview")
        st.html(f'<div class="cha-card flat"><h3>🌱 Sample card</h3><p>This is how text, cards and badges look right now.</p>'
                f'<div style="margin-top:.7rem">{chip("Strong evidence", "ok")} {chip("Moderate evidence", "info")} {chip("Limited evidence", "warn")} {chip("High severity", "danger")}</div></div>')
        callout("warn", "Warnings and notices stay readable in every theme.", title="Notice")

    # ------------------------------------------------------------ preferences
    if sec == sections[1]:
        section("Defaults")
        crops = SUPPORTED_CROP_NAMES
        st.selectbox("Default crop", crops, index=crops.index(default_crop(s)), key="w_crop", on_change=_saver(repo, "default_crop", "w_crop"),
                     help="Pre-selected when you start an assessment or add a plant.")
        st.toggle("Open the results automatically when an assessment finishes", value=s["auto_open_results"], key="w_auto", on_change=_saver(repo, "auto_open_results", "w_auto"))
        st.toggle("Show technical photo details (size, sharpness, brightness)", value=s["show_quality_details"], key="w_qd", on_change=_saver(repo, "show_quality_details", "w_qd"))
        section("Reminders & assistant")
        st.toggle("Show due follow-up reminders on the Home page", value=s["show_reminders_home"], key="w_rem", on_change=_saver(repo, "show_reminders_home", "w_rem"))
        st.toggle("Save assistant conversations to the local database", value=s["save_chats"], key="w_chat", on_change=_saver(repo, "save_chats", "w_chat"),
                  help="When off, chat messages only exist for the current session.")
        section("Reset")
        if st.button("↩️ Restore default settings", key="w_reset"):
            restore_defaults(repo)
            for k in [k for k in st.session_state if str(k).startswith("w_")]:
                del st.session_state[k]
            toast("Defaults restored", "↩️")
            st.rerun()

    # ------------------------------------------------------------ AI & engine
    if sec == sections[2]:
        cfg = svc.llm.describe()
        section("Language model")
        if cfg["configured"]:
            callout("ok", f"Connected configuration: {cfg['provider'].title()} · {cfg['model']}. If the service can't be reached the app falls back to its built-in assistant automatically.", title="AI assistant enabled")
        else:
            callout("info", "The app currently uses its built-in, knowledge-base-grounded assistant. It works offline and never invents product doses. "
                            "To enable a hosted AI model, add the lines below to a `.env` file next to app.py and restart.", title="Built-in assistant active")
            st.code("LLM_PROVIDER=gemini      # or openai\nLLM_API_KEY=your_api_key\nLLM_MODEL=gemini-flash-latest", language="bash")
        section("Analysis engine")
        docs = [d for d in load_knowledge_documents() if isinstance(d, dict)]
        key_values([("Photo analysis", "Colour/texture feature check (lightweight heuristic, runs locally)"),
                    ("Knowledge retrieval", f"TF-IDF search over {len(docs)} curated condition records"),
                    ("Supported crops", ", ".join(SUPPORTED_CROP_NAMES))])
        st.caption("API keys are read from environment variables only and are never displayed or stored in the database.")

    # ------------------------------------------------------------ data & privacy
    if sec == sections[3]:
        counts = repo.get_counts()
        section("Stored on this device")
        stat_grid([{"value": counts["assessments"], "label": "Assessments"}, {"value": counts["plants"], "label": "Plants"},
                   {"value": counts["open_reminders"], "label": "Open reminders"}, {"value": counts["chat_messages"], "label": "Saved chat messages"}])
        st.caption("Everything is stored in a local SQLite file. Photos are analysed in memory and are not saved. Don't put passwords or API keys in notes.")
        section("Export")
        st.download_button("⬇️ Download all my data (JSON)", data=json.dumps(repo.export_all(), indent=2, default=str),
                           file_name=f"crop-health-backup-{date.today().isoformat()}.json", mime="application/json", key="set_export")
        section("Clear data")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Clear this session's chat", use_container_width=True, key="set_clear_chat"):
                st.session_state.chat_messages = []
                toast("Session chat cleared", "🧹")
        with c2:
            _danger_action("🗑️ Delete saved chats", "d_chats", "Permanently delete every saved assistant message.", lambda: repo.delete_chat_messages())
        c3, c4 = st.columns(2)
        with c3:
            _danger_action("🗑️ Delete all assessments", "d_an", "Permanently delete all saved assessments and their sources.",
                           lambda: (repo.delete_all_analyses(), st.session_state.update(current_analysis=None)))
        with c4:
            _danger_action("🗑️ Delete plants & reminders", "d_pl", "Permanently delete all plants and reminders. Assessments are kept.", lambda: repo.delete_all_plants())

    # ------------------------------------------------------------ install & about
    if sec == sections[4]:
        render_install_section()
        section("About this build")
        key_values([("Version", APP_VERSION), ("Database file", str(DATABASE_PATH)), ("Python", platform.python_version()), ("Streamlit", st.__version__)])

