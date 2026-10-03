from typing import Dict, Any, Optional
from src.config import SUPPORTED_CROP_NAMES

def validate_user_input(
    crop: str,
    symptoms_text: str,
    has_image: bool,
    image_validation_res: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validates crop, image, and symptoms input.
    Determines input mode: 'image_only', 'symptoms_only', 'combined', or 'invalid'.
    """
    issues = []
    
    # Validate crop selection
    if not crop or crop.strip() == "":
        issues.append("No crop selected. Please select a crop from the supported list.")
    elif crop not in SUPPORTED_CROP_NAMES:
        issues.append(f"Crop '{crop}' is not currently in the supported analysis scope.")

    # Validate image if present
    valid_image = False
    if has_image:
        if image_validation_res:
            if not image_validation_res.get("valid", False):
                issues.append(image_validation_res.get("error", "Invalid image provided."))
            else:
                valid_image = True
        else:
            valid_image = True

    # Validate symptoms description
    clean_symptoms = symptoms_text.strip() if symptoms_text else ""
    valid_symptoms = len(clean_symptoms) >= 5

    # Determine Input Mode
    if valid_image and valid_symptoms:
        input_mode = "combined"
    elif valid_image:
        input_mode = "image_only"
    elif valid_symptoms:
        input_mode = "symptoms_only"
    else:
        input_mode = "insufficient"
        if not has_image and len(clean_symptoms) < 5:
            issues.append("Please provide either a crop leaf image or describe observed symptoms (at least 5 characters).")

    is_valid = len(issues) == 0 and input_mode != "insufficient"

    return {
        "valid": is_valid,
        "input_mode": input_mode,
        "crop": crop,
        "has_image": valid_image,
        "has_symptoms": valid_symptoms,
        "symptoms": clean_symptoms,
        "issues": issues
    }
