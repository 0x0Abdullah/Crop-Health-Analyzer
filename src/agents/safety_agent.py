import logging
from typing import Dict, Any, List

logger = logging.getLogger("safety_agent")

UNGROUNDED_CHEMICAL_KEYWORDS = ["ddt", "aldrin", "dieldrin", "paraquat_unlabeled", "unregistered_spray"]

class SafetyVerificationAgent:
    """
    Safety & Verification Agent:
    Validates proposed management options before report output.
    Filters unverified pesticide claims, ensures safety notices, and handles low-confidence escalation.
    """
    def run(
        self,
        crop: str,
        condition: str,
        confidence: float,
        management_guidance: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        safety_notes = []
        treatments = management_guidance.get("treatment_information", management_guidance.get("verified_treatments", []))
        filtered_treatments = []

        # 1. Filter hazardous or ungrounded pesticide claims
        for treatment in treatments:
            treat_lower = treatment.lower()
            if any(bad in treat_lower for bad in UNGROUNDED_CHEMICAL_KEYWORDS):
                logger.warning(f"Safety agent stripped unsafe/unregistered treatment: {treatment}")
                safety_notes.append(f"Removed unverified chemical claim '{treatment}'.")
            else:
                filtered_treatments.append(treatment)

        # Update management guidance with filtered treatments
        management_guidance["treatment_information"] = filtered_treatments
        # Backward compatibility for older callers/tests; UI uses treatment_information.
        management_guidance["verified_treatments"] = filtered_treatments
        management_guidance["verification_required"] = True

        # 2. Add Standard Safety Notices
        safety_notes.extend([
            "Always wear chemical-resistant gloves, protective eyewear, and long sleeves during spray applications.",
            "Verify product registration and label directions with your regional Ministry of Agriculture or Extension Office.",
            "Respect Pre-Harvest Intervals (PHI) and Re-Entry Intervals (REI) specified on commercial labels."
        ])

        # 3. Check Low Confidence Escalation
        low_confidence_flag = confidence < 0.45
        if low_confidence_flag:
            safety_notes.append(
                "WARNING: Low diagnostic confidence. Do not apply expensive synthetic chemical treatments without professional laboratory confirmation."
            )

        return {
            "is_safe": True,
            "safety_notes": safety_notes,
            "low_confidence_flag": low_confidence_flag,
            "treatment_information_count": len(filtered_treatments)
        }
