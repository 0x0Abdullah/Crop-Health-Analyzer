import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("symptom_agent")

# (key, regex, display name). Patterns are anchored on word starts so that, for example,
# "whole plant" no longer matches "hole" and "spring" no longer matches "ring".
SYMPTOM_PATTERNS = [
    ("yellow", r"\byellow", "Yellowing leaves / Chlorosis"),
    ("spot", r"\bspot", "Foliar leaf spots / Lesions"),
    ("lesion", r"\blesion", "Stem or leaf lesions"),
    ("brown", r"\bbrown", "Brown necrotic spots or leaf margins"),
    ("black", r"\bblack", "Black rot or target ring lesions"),
    ("wilt", r"\bwilt", "Wilting foliage or vascular collapse"),
    ("curl", r"\bcurl", "Upward or inward leaf curling"),
    ("rust", r"\brust", "Powdery rust pustules"),
    ("mold", r"\bmou?ld", "Mold / Fungal mycelium coating"),
    ("hole", r"\bholes?\b|\bholed\b", "Insect feeding holes or defoliation"),
    ("stunt", r"\bstunt", "Stunted growth / dwarfing"),
    ("drop", r"\b(leaf|leaves|fruit)\s+drop|\bdropp(ed|ing)\b|\bdrop(s)?\b", "Premature leaf drop"),
    ("ring", r"\brings?\b", "Concentric target rings"),
    ("water", r"\bwater[- ]?soak|\bwatery\b", "Water-soaked dark lesions"),
    ("powder", r"\bpowder|\bwhite (coating|film|patch)", "White powdery mildew coating"),
    ("fruit", r"\bfruit (damage|rot|lesion|spot)|\brotting fruit|\bfruit\b.*\b(rot|damage|crack)", "Fruit damage or rot"),
    ("root", r"\broot (problem|rot|damage)|\brotten roots?|\broots?\b.*\b(rot|brown|decay)", "Root problems or rot"),
    ("rapid", r"\b(rapid|rapidly|quick|quickly|fast|sudden|suddenly)\b", "Rapidly spreading symptoms"),
]
_COMPILED = [(k, re.compile(rx, re.I), name) for k, rx, name in SYMPTOM_PATTERNS]

# Backward-compatible mapping for any external callers that imported the old dict.
KEYWORD_SYMPTOM_MAP = {k: name for k, _, name in SYMPTOM_PATTERNS}

_FUNGAL_KEYS = {"yellow", "brown", "spot", "lesion", "black", "ring", "mold", "powder", "rust"}


class SymptomAgent:
    """
    Symptom Agent:
    Interprets user symptom text description, extracts key observed symptoms,
    identifies disease categories, and notes missing useful info.
    """
    def run(self, symptoms_text: str, crop: str) -> Dict[str, Any]:
        if not symptoms_text or len(symptoms_text.strip()) < 3:
            return {
                "observed_symptoms": [],
                "possible_categories": [],
                "missing_information": [
                    "Leaf color changes",
                    "Spot appearance or target rings",
                    "Affected plant parts (lower vs upper leaves)"
                ]
            }

        text = symptoms_text.strip()
        text_lower = text.lower()
        extracted: List[str] = []
        categories = []

        def add_category(label: str) -> None:
            if label not in categories:
                categories.append(label)

        for key, rx, symptom_name in _COMPILED:
            if rx.search(text):
                if symptom_name not in extracted:
                    extracted.append(symptom_name)
                if key in _FUNGAL_KEYS:
                    add_category("Leaf Disease / Fungal or Bacterial Pathogen")
                if key in ("curl", "stunt"):
                    add_category("Viral Disease or Insect Vector Impact")
                if key in ("wilt", "water", "root"):
                    add_category("Water Mold / Vascular Disease / Soil Wetness")
                if key == "hole":
                    add_category("Pest Damage / Chewing Insects")

        if not extracted:
            extracted.append(f"General reported symptoms: '{text}'")

        missing = []
        if "lower" not in text_lower and "upper" not in text_lower:
            missing.append("Location of symptoms on canopy (lower vs upper leaves)")
        if "water" not in text_lower and "rain" not in text_lower and "irrigation" not in text_lower:
            missing.append("Irrigation method (overhead vs drip)")

        return {
            "observed_symptoms": extracted,
            "possible_categories": categories if categories else ["General Crop Stress"],
            "missing_information": missing,
            "raw_text": text
        }
