import uuid
from typing import Dict, Any, List, Optional

class ShortTermMemoryManager:
    """Streamlit session memory kept behind a lazy import so backend tests do not require Streamlit."""
    @staticmethod
    def _st():
        import streamlit as st
        return st

    @staticmethod
    def initialize_session():
        st = ShortTermMemoryManager._st()
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = None
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "current_crop" not in st.session_state:
            st.session_state.current_crop = "Tomato"

    @staticmethod
    def get_session_id() -> str:
        ShortTermMemoryManager.initialize_session()
        return ShortTermMemoryManager._st().session_state.session_id

    @staticmethod
    def set_current_analysis(analysis_data: Dict[str, Any]):
        try:
            ShortTermMemoryManager._st().session_state.current_analysis = analysis_data
        except ModuleNotFoundError:
            return

    @staticmethod
    def get_current_analysis() -> Optional[Dict[str, Any]]:
        return ShortTermMemoryManager._st().session_state.get("current_analysis")

    @staticmethod
    def add_chat_message(role: str, content: str):
        st = ShortTermMemoryManager._st()
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        st.session_state.chat_messages.append({"role": role, "content": content})

    @staticmethod
    def get_chat_messages() -> List[Dict[str, str]]:
        return ShortTermMemoryManager._st().session_state.get("chat_messages", [])
