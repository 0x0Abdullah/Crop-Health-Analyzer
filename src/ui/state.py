"""Session state, cached services, navigation and settings helpers."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import streamlit as st

from src.config import SUPPORTED_CROP_NAMES
from src.database.db import init_db
from src.database.repository import DatabaseRepository
from src.llm.client import LLMClient
from src.memory.short_term import ShortTermMemoryManager
from src.settings import load_settings, save_setting, reset_settings, DEFAULTS
from src.workflow.pipeline import CropDoctorPipeline

# (id, icon, label)
PAGES = [
    ("home", "🏠", "Home"), ("analyze", "🔍", "Analyze"), ("plants", "🌱", "Plants"), ("history", "📊", "History"),
    ("assistant", "🤖", "Assistant"), ("learn", "📚", "Learn"), ("settings", "⚙️", "Settings"), ("about", "ℹ️", "About"),
]
PAGE_IDS = [p[0] for p in PAGES]


@dataclass
class Services:
    repo: DatabaseRepository
    pipeline: CropDoctorPipeline
    llm: LLMClient


@st.cache_resource(show_spinner=False)
def get_services() -> Services:
    """Create the database, pipeline and LLM client once per server process."""
    init_db()
    repo = DatabaseRepository()
    return Services(repo=repo, pipeline=CropDoctorPipeline(db_repo=repo), llm=LLMClient())


# ------------------------------------------------------------------ navigation
def init_navigation() -> str:
    if "page" not in st.session_state:
        wanted = st.query_params.get("page", "home")
        st.session_state.page = wanted if wanted in PAGE_IDS else "home"
    return st.session_state.page


def goto(page: str, **flags: Any) -> None:
    """Switch page. Safe to use as an on_click callback; extra flags are stored in session state."""
    if page not in PAGE_IDS:
        page = "home"
    st.session_state.page = page
    for k, v in flags.items():
        st.session_state[k] = v


def sync_url(page: str) -> None:
    if st.query_params.get("page") != page:
        st.query_params["page"] = page


# ------------------------------------------------------------------ settings
def init_settings(repo: DatabaseRepository) -> Dict[str, Any]:
    if "settings" not in st.session_state:
        st.session_state.settings = load_settings(repo, SUPPORTED_CROP_NAMES)
    return st.session_state.settings


def update_setting(repo: DatabaseRepository, key: str, value: Any) -> None:
    st.session_state.settings = save_setting(repo, key, value, SUPPORTED_CROP_NAMES)


def restore_defaults(repo: DatabaseRepository) -> None:
    st.session_state.settings = reset_settings(repo)


def default_crop(settings: Dict[str, Any]) -> str:
    c = settings.get("default_crop") or ""
    return c if c in SUPPORTED_CROP_NAMES else SUPPORTED_CROP_NAMES[0]


def toast(msg: str, icon: str = "✅") -> None:
    try:
        st.toast(msg, icon=icon)
    except Exception:  # very old Streamlit builds
        pass


def init_session() -> None:
    ShortTermMemoryManager.initialize_session()
