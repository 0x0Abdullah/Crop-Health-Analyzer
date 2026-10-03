from typing import Dict, Any, List, Optional
import uuid

def create_initial_workflow_state(
    session_id: Optional[str] = None,
    crop: str = "",
    symptoms: str = "",
    has_image: bool = False
) -> Dict[str, Any]:
    """
    Creates a fresh, structured workflow state dictionary.
    """
    return {
        "session_id": session_id or str(uuid.uuid4()),
        "crop": crop,
        "symptoms": symptoms,
        "has_image": has_image,
        "input_mode": "insufficient",
        "validation": {},
        "vision_result": {},
        "symptom_result": {},
        "retrieved_evidence": [],
        "evidence_fusion": {},
        "risk_assessment": {},
        "management_guidance": {},
        "safety_result": {},
        "final_report": "",
        "messages": [],
        "errors": []
    }
