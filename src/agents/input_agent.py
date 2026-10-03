import logging
from typing import Dict, Any, Optional
from src.utils.validation import validate_user_input
from src.utils.image_utils import validate_image_file

logger = logging.getLogger("input_agent")

class InputAgent:
    """
    Input Validation Agent:
    Validates crop selection, image file integrity, symptoms text length,
    and returns a structured initial state.
    """
    def run(
        self,
        crop: str,
        symptoms: str,
        image_bytes: Optional[bytes] = None,
        image_name: Optional[str] = None
    ) -> Dict[str, Any]:
        has_image = image_bytes is not None and len(image_bytes) > 0
        img_val_res = None
        
        if has_image and image_name:
            img_val_res = validate_image_file(image_bytes, image_name)

        val_res = validate_user_input(
            crop=crop,
            symptoms_text=symptoms,
            has_image=has_image,
            image_validation_res=img_val_res
        )

        return {
            "valid": val_res["valid"],
            "input_mode": val_res["input_mode"],
            "crop": crop,
            "has_image": val_res["has_image"],
            "has_symptoms": val_res["has_symptoms"],
            "symptoms": val_res["symptoms"],
            "image_bytes": image_bytes,
            "image_name": image_name,
            "image_validation": img_val_res,
            "issues": val_res["issues"]
        }
