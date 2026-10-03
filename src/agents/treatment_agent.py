import logging
from typing import Dict, Any, List

logger = logging.getLogger("treatment_agent")

class TreatmentIPMAgent:
    """
    Treatment & IPM Agent:
    Assembles evidence-grounded management guidance prioritizing IPM, cultural practices,
    prevention, biological controls, and non-chemical measures.
    """
    def run(
        self,
        crop: str,
        condition: str,
        retrieved_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        immediate_actions = []
        prevention = []
        ipm = []
        biological_controls = []
        treatment_information = []

        if retrieved_evidence:
            top_rec = retrieved_evidence[0].get("raw_record", {})
            immediate_actions = top_rec.get("immediate_actions", [])
            prevention = top_rec.get("prevention", [])
            ipm = top_rec.get("ipm", [])
            biological_controls = top_rec.get("biological_controls", [])
            treatment_information = top_rec.get("verified_treatments", [])
        
        # Generic defaults if knowledge record is minimal
        if not immediate_actions:
            immediate_actions = [
                "Inspect lower leaves of adjacent plants for early spot spread.",
                "Prune infected foliage near soil level and burn/dispose away from field."
            ]
        if not prevention:
            prevention = [
                "Practice strict 3-year crop rotation with non-host crop families.",
                "Use certified disease-resistant seed stock or transplants."
            ]
        if not ipm:
            ipm = [
                "Scout fields twice weekly during warm humid weather.",
                "Maintain optimal weed-free borders to prevent vector harborage."
            ]
        if not biological_controls:
            biological_controls = [
                "Apply Bacillus subtilis bio-fungicide foliar spray per label directions."
            ]
        if not treatment_information:
            treatment_information = []

        return {
            "immediate_actions": immediate_actions,
            "prevention": prevention,
            "ipm": ipm,
            "biological_controls": biological_controls,
            "treatment_information": treatment_information,
            "verification_required": True,
            "is_grounded": len(retrieved_evidence) > 0
        }
