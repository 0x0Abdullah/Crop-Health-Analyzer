from typing import Dict, Any, List

def verify_report_safety(report_text: str, state: Dict[str, Any]) -> str:
    """
    Final safety check on report markdown before displaying to user.
    Ensures mandatory safety disclaimers and warning banners.
    """
    disclaimer = (
        "\n\n---\n"
        "> ⚠️ **SAFETY & RESPONSIBILITY DISCLAIMER**  \n"
        "> *Crop Health Analyzer provides decision support recommendations based on computer vision, symptom matching, and verified agricultural extension knowledge base records. It does not replace certified professional laboratory diagnosis or licensed agronomic prescriptions. Always verify chemical product labels, application rates, and local regulations with your regional Agricultural Extension Service.*"
    )
    
    if "SAFETY & RESPONSIBILITY DISCLAIMER" not in report_text:
        report_text += disclaimer

    return report_text
