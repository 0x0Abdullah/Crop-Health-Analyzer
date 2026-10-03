import csv
import io
from datetime import date
from typing import Any, Dict, List

import streamlit as st

from src.ui.components import (bullet_list, callout, chip, esc, evidence_chip, html_table, key_values, page_header, section, severity_chip)
from src.ui.state import goto, toast

VIEWS = ["Latest result", "Saved assessments", "Compare"]
LEVEL_HELP = {
    "strong": "Several independent sources of evidence agree.",
    "moderate": "Several indicators match, but similar conditions remain possible.",
    "limited": "Some indicators match; more photos or details are needed.",
    "insufficient": "There isn't enough information to name a likely condition reliably.",
}
SEV_RANK = {"Unknown": 0, "Low": 1, "Moderate": 2, "High": 3}


def _level_help(level: str) -> str:
    l = (level or "").lower()
    for k, v in LEVEL_HELP.items():
        if k in l:
            return v
    return ""


def disclaimer() -> None:
    callout("warn", "Results are AI-assisted estimates based on the information provided and available agricultural knowledge — not laboratory-confirmed "
                    "diagnoses. For severe, fast-spreading, uncertain or high-impact cases, seek qualified agricultural advice.", title="Important")


def evidence_cards(items: List[Dict[str, Any]]) -> None:
    if not items:
        callout("info", "No knowledge-base sources were matched to this assessment.")
        return
    for i, ev in enumerate(items):
        rec = ev.get("raw_record") or {}
        title = ev.get("title") or rec.get("title") or "Agricultural source"
        content = rec.get("content") or ev.get("content") or ""
        if not content and ev.get("text") and not str(ev["text"]).startswith("Crop:"):
            content = ev["text"]
        signs = rec.get("symptoms") or []
        with st.expander(f"📄 {title}", expanded=(i == 0)):
            if content:
                st.markdown(content)
            if signs:
                st.markdown("**Typical signs:** " + ", ".join(str(s) for s in signs))
            src = ev.get("source") or rec.get("source") or "Agricultural extension source"
            url = ev.get("url") or rec.get("url")
            st.caption(f"Source: {src}" + (f" · [Open source]({url})" if url else ""))


def _header(crop, condition, level, severity, meta_bits: List[str]) -> None:
    sev_cls = f"sev-{str(severity or 'unknown').lower()}"
    st.html(
        f'<div class="cha-result {sev_cls}"><div class="cha-muted" style="font-size:.85rem;font-weight:700;letter-spacing:.04em">POSSIBLE CONDITION · {esc(crop)}</div>'
        f'<div class="cond">{esc(condition or "Insufficient evidence")}</div>'
        f'<div>{evidence_chip(level)} {severity_chip(severity)}</div>'
        f'<div class="meta">{esc(_level_help(level))}</div>'
        f'<div class="meta">{esc(" · ".join(b for b in meta_bits if b))}</div></div>'
    )


# ------------------------------------------------------------------ latest result
def render_current(svc, result: Dict[str, Any]) -> None:
    fusion = result.get("evidence_fusion", {}) or {}
    risk = result.get("risk_assessment", {}) or {}
    mg = result.get("management_guidance", {}) or {}
    plant = svc.repo.get_plant(result["plant_id"]) if result.get("plant_id") else None
    bits = [f'{result.get("image_count", 0)} photo(s)' if result.get("image_count") else "No photos",
            "symptoms provided" if result.get("symptoms") else "", f'Plant: {plant["name"]}' if plant else ""]
    _header(result.get("crop"), fusion.get("top_condition"), fusion.get("evidence_level"), risk.get("severity"), bits)

    thumbs = result.get("thumbnails") or []
    if thumbs:
        cols = st.columns(4)
        for c, t in zip(cols, thumbs):
            c.image(t, use_container_width=True)

    if fusion.get("conflicting_evidence"):
        callout("warn", " ".join(fusion["conflicting_evidence"]), title="Mixed signals")
    if risk.get("escalation_required"):
        callout("warn", "Because the evidence is limited, conflicting or the severity is high, consider confirming with a local agricultural extension officer before taking costly action.", title="Consider expert advice")

    a, b, c = st.columns(3)
    a.button("🤖 Ask the assistant about this", use_container_width=True, on_click=goto, args=("assistant",), key="res_ask")
    b.button("➕ New assessment", use_container_width=True, on_click=goto, args=("analyze",), kwargs={"an_reset": True}, key="res_new")
    c.download_button("⬇️ Download report", data=result.get("final_report", ""), file_name=f'crop-report-{str(result.get("crop","")).split()[0].lower()}-{date.today().isoformat()}.md',
                      mime="text/markdown", use_container_width=True, key="res_dl")

    cands = fusion.get("candidates") or []
    if cands:
        section("Possible conditions")
        html_table([{"condition": x.get("condition"), "evidence": x.get("evidence_level")} for x in cands], ["condition", "evidence"],
                   labels={"evidence": "Evidence level"}, chips={"evidence": lambda v: evidence_chip(f"{v}")})

    tabs = ["🚨 What to do", "🔎 Why this result", "📚 Sources", "📝 Full report"]
    tab = st.radio("Result section", tabs, horizontal=True, key="res_tab", label_visibility="collapsed")
    if tab == tabs[0]:
        st.markdown("#### Do now")
        bullet_list(mg.get("immediate_actions"))
        st.markdown("#### 🌿 Prevention & IPM")
        bullet_list((mg.get("ipm") or []) + (mg.get("prevention") or []))
        if mg.get("biological_controls"):
            st.markdown("#### 🦠 Biological options")
            bullet_list(mg["biological_controls"])
        st.markdown("#### 🧪 Treatment information")
        if mg.get("treatment_information"):
            bullet_list(mg["treatment_information"])
        else:
            callout("info", "No chemical treatment information was retrieved. Verify any product locally before use.")
        st.caption("Verify product labels, crop registration, active ingredients, local requirements, PHI and REI before using any pesticide.")
        notes = (result.get("safety_result") or {}).get("safety_notes") or []
        if notes:
            with st.expander("⚠️ Safety notes"):
                bullet_list(notes)
    elif tab == tabs[1]:
        st.markdown("#### Evidence used")
        bullet_list(fusion.get("supporting_evidence"))
        sym = (result.get("symptom_result") or {}).get("observed_symptoms") or []
        if sym:
            st.markdown("#### Symptoms recognised")
            bullet_list(sym)
        miss = (result.get("symptom_result") or {}).get("missing_information") or []
        if miss:
            st.markdown("#### Details that would improve the result")
            bullet_list(miss)
        vis = result.get("vision_result") or {}
        if vis.get("available"):
            st.caption("Photo analysis uses a lightweight colour/texture check (not a trained neural network), so treat it as a hint rather than a diagnosis.")
        if result.get("symptoms"):
            st.markdown("#### What you reported")
            st.markdown(f"> {result['symptoms']}")
    elif tab == tabs[2]:
        evidence_cards(result.get("retrieved_evidence") or [])
    else:
        st.markdown(result.get("final_report") or "_No report was generated._")
    disclaimer()


# ------------------------------------------------------------------ saved assessments
def _csv(rows: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    cols = ["id", "created_at", "crop", "result_condition", "evidence_level", "severity", "plant_id", "symptoms"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in cols})
    return buf.getvalue()


def render_saved(svc) -> None:
    repo = svc.repo
    hist = repo.get_analysis_history(200)
    if not hist:
        callout("info", "No saved assessments yet. Run your first one from the Analyze page.")
        st.button("🔍 Start an assessment", type="primary", on_click=goto, args=("analyze",), key="sv_start")
        return
    crops = sorted({h["crop"] for h in hist})
    f1, f2 = st.columns([2, 1])
    crop_f = f1.selectbox("Filter by crop", ["All crops"] + crops, key="hist_crop")
    rows = [h for h in hist if crop_f == "All crops" or h["crop"] == crop_f]
    f2.download_button("⬇️ Export CSV", _csv(rows), file_name="assessments.csv", mime="text/csv", use_container_width=True, key="sv_csv")
    html_table([{**r, "created_at": r["created_at"][:16].replace("T", " ")} for r in rows],
               ["id", "created_at", "crop", "result_condition", "evidence_level", "severity"],
               labels={"id": "#", "created_at": "Date", "result_condition": "Possible condition", "evidence_level": "Evidence"},
               chips={"evidence_level": evidence_chip, "severity": lambda v: severity_chip(v).replace("Severity: ", "")})

    section("Open an assessment")
    labels = {f"#{r['id']} · {r['created_at'][:10]} · {r['crop']} · {r['result_condition']}": r["id"] for r in rows}
    if not labels:
        return
    choice = st.selectbox("Assessment", list(labels), key="hist_pick", label_visibility="collapsed")
    rec = repo.get_analysis_by_id(labels[choice])
    if not rec:
        callout("warn", "That assessment no longer exists.")
        return
    plant = repo.get_plant(rec["plant_id"]) if rec.get("plant_id") else None
    _header(rec["crop"], rec["result_condition"], rec.get("evidence_level"), rec["severity"],
            [rec["created_at"][:16].replace("T", " "), "photo(s) analysed" if rec.get("has_image") else "", f'Plant: {plant["name"]}' if plant else ""])
    if rec.get("symptoms"):
        st.markdown(f"**Reported:** {rec['symptoms']}")
    st.markdown(rec.get("report_json") or "_No report stored._")
    if rec.get("evidence"):
        st.markdown("#### Sources")
        evidence_cards(rec["evidence"])
    a, b = st.columns([1, 1])
    a.download_button("⬇️ Download report", rec.get("report_json") or "", file_name=f"assessment-{rec['id']}.md", mime="text/markdown", use_container_width=True, key=f"sv_dl_{rec['id']}")
    with b.popover("🗑️ Delete this assessment", use_container_width=True):
        st.write("This permanently removes the assessment and its stored sources.")
        if st.button("Yes, delete it", type="primary", key=f"sv_del_{rec['id']}"):
            repo.delete_analysis(rec["id"])
            cur = st.session_state.get("current_analysis")
            if cur and cur.get("analysis_id") == rec["id"]:
                st.session_state.current_analysis = None
            toast("Assessment deleted", "🗑️")
            st.rerun()
    disclaimer()


# ------------------------------------------------------------------ compare
def render_compare(svc) -> None:
    repo = svc.repo
    hist = repo.get_analysis_history(200)
    if len(hist) < 2:
        callout("info", "You need at least two saved assessments to compare. Run another assessment (ideally of the same plant) and come back.")
        return
    labels = {f"#{r['id']} · {r['created_at'][:10]} · {r['crop']} · {r['result_condition']}": r["id"] for r in hist}
    names = list(labels)
    x, y = st.columns(2)
    a = x.selectbox("Earlier", names, index=1, key="cmp_a")
    b = y.selectbox("Later", names, index=0, key="cmp_b")
    if a == b:
        callout("info", "Pick two different assessments.")
        return
    ra, rb = repo.get_analysis_by_id(labels[a]), repo.get_analysis_by_id(labels[b])
    if not ra or not rb:
        callout("warn", "One of the assessments no longer exists.")
        return
    fields = [("Crop", "crop"), ("Possible condition", "result_condition"), ("Evidence level", "evidence_level"), ("Severity", "severity")]
    rows = []
    for label, key in fields:
        same = ra.get(key) == rb.get(key)
        trend = "No change" if same else "Changed"
        if key == "severity" and not same:
            ka, kb = SEV_RANK.get(ra[key], 0), SEV_RANK.get(rb[key], 0)
            trend = "Worse" if kb > ka else "Improving" if kb < ka else "Changed"
        rows.append({"field": label, "earlier": ra.get(key), "later": rb.get(key), "trend": trend})
    kinds = {"No change": "neutral", "Changed": "info", "Worse": "danger", "Improving": "ok"}
    html_table(rows, ["field", "earlier", "later", "trend"], labels={"field": "", "trend": "Change"}, chips={"trend": lambda v: chip(v, kinds.get(v, "neutral"))})
    st.caption("The comparison uses the saved structured fields. Photos are not stored in this local build, so visual change is not assessed.")


# ------------------------------------------------------------------ page
def render(svc) -> None:
    page_header("📊", "Results & history", "Your latest assessment, everything you've saved, and side-by-side comparison.")
    current = st.session_state.get("current_analysis")
    if st.session_state.get("hist_view") not in VIEWS:
        st.session_state["hist_view"] = VIEWS[0] if current else VIEWS[1]
    view = st.radio("View", VIEWS, horizontal=True, key="hist_view", label_visibility="collapsed")
    if view == "Latest result":
        if current:
            render_current(svc, current)
        else:
            callout("info", "No assessment in this session yet. Run one, or open a saved assessment from the next tab.")
            st.button("🔍 Start an assessment", type="primary", on_click=goto, args=("analyze",), key="cur_start")
    elif view == "Saved assessments":
        render_saved(svc)
    else:
        render_compare(svc)
