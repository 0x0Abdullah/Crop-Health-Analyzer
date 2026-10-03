import streamlit as st

from src.database.models import ChatMessageRecord
from src.memory.short_term import ShortTermMemoryManager
from src.ui.components import callout, page_header
from src.ui.state import goto, toast

QUICK_QUESTIONS = ["What should I do first?", "Is it contagious to other plants?", "What are organic options?",
                   "How do I prevent it next season?", "How serious is this?", "When should I call an expert?"]


def _context(current):
    if not current:
        return {"crop": "", "result_condition": "", "has_analysis": False, "symptoms": "", "retrieved_evidence": []}
    fusion = current.get("evidence_fusion", {}) or {}
    return {
        "crop": current.get("crop"), "has_analysis": True,
        "result_condition": fusion.get("top_condition"), "evidence_level": fusion.get("evidence_level"),
        "severity": (current.get("risk_assessment") or {}).get("severity"),
        "symptoms": current.get("symptoms", ""), "management_guidance": current.get("management_guidance", {}),
        "retrieved_evidence": current.get("retrieved_evidence", []),
    }


def _ask(q: str) -> None:
    st.session_state["chat_pending"] = q


def render(svc) -> None:
    settings = st.session_state.settings
    page_header("🤖", "Agricultural assistant", "Ask follow-up questions about your assessment, prevention, or plant care.")
    current = ShortTermMemoryManager.get_current_analysis()
    messages = ShortTermMemoryManager.get_chat_messages()

    if current:
        cond = (current.get("evidence_fusion") or {}).get("top_condition", "Insufficient evidence")
        callout("info", f"{current.get('crop')} · {cond}", title="Answering about your latest assessment")
    else:
        callout("info", "I can answer general plant-health questions now. Run an assessment first for advice tailored to your crop.", title="No assessment yet")
        st.button("🔍 Start an assessment", on_click=goto, args=("analyze",), key="as_start")

    cfg = svc.llm.describe()
    st.caption(f"Engine: {cfg['provider'].title()} · {cfg['model']}" + ("" if cfg["configured"] else " — add an API key in .env to enable AI chat (see Settings)."))

    pending = st.session_state.pop("chat_pending", None)
    if not messages and not pending:
        st.markdown("**Try asking:**")
        cols = st.columns(3)
        for i, q in enumerate(QUICK_QUESTIONS):
            cols[i % 3].button(q, key=f"qq_{i}", use_container_width=True, on_click=_ask, args=(q,))

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    q = st.chat_input("Ask about this crop or plant health…") or pending
    if q:
        q = q.strip()[:1500]
        history = list(messages)
        ShortTermMemoryManager.add_chat_message("user", q)
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    ans, source = svc.llm.chat(q, _context(current), history)
                except Exception:
                    ans, source = "Sorry, I couldn't answer that just now. Please try again.", "built-in"
            st.markdown(ans)
            if cfg["configured"] and source == "built-in":
                st.caption("The AI service didn't respond, so this answer comes from the built-in knowledge assistant.")
        ShortTermMemoryManager.add_chat_message("assistant", ans)
        if settings.get("save_chats", True):
            aid = (current or {}).get("analysis_id")
            sid = ShortTermMemoryManager.get_session_id()
            try:
                svc.repo.save_chat_message(ChatMessageRecord(analysis_id=aid, session_id=sid, role="user", message=q))
                svc.repo.save_chat_message(ChatMessageRecord(analysis_id=aid, session_id=sid, role="assistant", message=ans))
            except Exception:
                pass

    if messages or q:
        if st.button("🧹 Clear conversation", key="as_clear"):
            st.session_state.chat_messages = []
            toast("Conversation cleared", "🧹")
            st.rerun()
