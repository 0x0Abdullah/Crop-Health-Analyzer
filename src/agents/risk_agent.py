import logging
from typing import Dict, Any, List

logger = logging.getLogger("risk_agent")

class RiskSeverityAgent:
    """Evidence fusion without presenting heuristic scores as calibrated probabilities."""
    def run(self, crop: str, vision_result: Dict[str, Any], symptom_result: Dict[str, Any], retrieved_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        vision_preds = vision_result.get("predictions", []) if vision_result.get("available") else []
        top_vision = vision_preds[0] if vision_preds else None
        evidence = retrieved_evidence or []
        top_ev = evidence[0] if evidence else None
        candidates=[]
        for ev in evidence[:3]:
            candidates.append({"condition": ev.get("condition") or "Possible condition", "evidence_level": "Moderate" if ev.get("score",0)>0.12 else "Limited", "reason": ev.get("text","")[:260]})
        if top_vision and not any(c["condition"].lower() in str(top_vision.get("label","")).lower() for c in candidates):
            candidates.insert(0,{"condition": top_vision.get("label","Possible condition"),"evidence_level":"Limited","reason":"Visual feature analysis produced this candidate; it requires corroboration."})
        condition = top_ev.get("condition", "Insufficient evidence") if top_ev else (top_vision.get("label","Insufficient evidence") if top_vision else "Insufficient evidence")
        has_conflict=False
        if top_ev and top_vision:
            a=str(top_ev.get("condition","")).lower(); b=str(top_vision.get("label","")).lower()
            has_conflict=bool(a and b and a not in b and b not in a and "healthy" not in b)
        symptoms_present = bool(symptom_result.get("observed_symptoms"))
        # free text we could not map to a known symptom is input, but not corroboration
        symptoms_recognised = any(not str(x).startswith("General reported symptoms") for x in symptom_result.get("observed_symptoms", []))
        vision_label = str((top_vision or {}).get("label", ""))
        vision_healthy = "healthy" in vision_label.lower()
        vision_signal = bool(top_vision) and not vision_healthy
        # Retrieval always returns records for a crop. They only corroborate something if the user's own
        # input (symptoms or a non-healthy photo signal) shaped the query.
        no_signal = not symptoms_present and not vision_signal
        if no_signal:
            top_ev, evidence, candidates, has_conflict = None, [], [], False
            condition = "No clear problem detected" if vision_healthy else "Insufficient evidence"
            level = "Limited evidence" if vision_healthy else "Insufficient evidence"
        else:
            kb_signal = bool(top_ev)
            vision_matches_kb = bool(top_ev and vision_signal and not has_conflict)
            agreement = int(symptoms_recognised) + int(vision_signal) + int(kb_signal) + int(vision_matches_kb)
            if has_conflict or agreement < 2:
                level = "Limited evidence"
            elif agreement >= 4:
                level = "Strong evidence"
            else:
                level = "Moderate evidence"
        # Backward-compatible internal score only; UI must use evidence_level instead of treating it as calibrated probability.
        legacy_confidence = min(0.92, max(0.0, max([float(ev.get("score", 0.0)) * 2.5 for ev in evidence[:3]] + [float(top_vision.get("confidence", 0.0)) if top_vision else 0.0])))
        symptoms = symptom_result.get("observed_symptoms", [])
        cond_lower=condition.lower()
        if level == "Insufficient evidence": severity="Unknown"
        elif condition == "No clear problem detected": severity="Low"
        elif any(k in cond_lower for k in ("late blight","blast","wilt","collapse","water-soaked")) or "rapidly" in " ".join(symptoms).lower(): severity="High"
        elif "healthy" in cond_lower: severity="Low"
        else: severity="Moderate"
        supporting=[]
        if no_signal and vision_healthy: supporting.append("The photo analysis found no clear disease signs, and no symptoms were reported. Add symptoms or clearer close-ups to check further.")
        elif top_vision: supporting.append("Visual feature analysis was available.")
        if symptoms: supporting.append("Reported symptoms were included in the assessment.")
        if evidence: supporting.append(f"{len(evidence)} agricultural knowledge record(s) were retrieved.")
        if has_conflict: supporting.append("Visual and knowledge evidence do not clearly agree.")
        return {"evidence_fusion":{"top_condition":condition,"confidence":legacy_confidence,"evidence_level":level,"uncertainty":level,"supporting_evidence":supporting,"no_signal":no_signal,"conflicting_evidence":["Vision and retrieved knowledge disagree; additional evidence is recommended."] if has_conflict else [],"has_conflict":has_conflict,"candidates":candidates[:4]},"risk_assessment":{"severity":severity,"escalation_required": severity=="High" or has_conflict or level in ("Limited evidence","Insufficient evidence"),"notes":"Severity is an assessment of urgency, not a laboratory diagnosis."}}
