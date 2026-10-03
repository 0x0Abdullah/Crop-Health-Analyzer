import io
import logging
from typing import Any, Dict

import numpy as np
from PIL import Image

logger = logging.getLogger("image_utils")

MAX_FILE_SIZE_MB = 8
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def _estimate_sharpness(gray: np.ndarray) -> float:
    """Estimate sharpness without OpenCV using a discrete Laplacian."""
    gray = gray.astype(np.float32, copy=False)
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    lap = (
        gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
        - 4.0 * gray[1:-1, 1:-1]
    )
    return float(np.var(lap))


def validate_image_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Validate uploaded images using Pillow/NumPy only.

    OpenCV is intentionally not required here. This keeps image validation
    portable on Windows systems where native OpenCV DLLs can be blocked by
    Application Control policies.
    """
    result: Dict[str, Any] = {
        "valid": True,
        "error": None,
        "width": 0,
        "height": 0,
        "format": "",
        "quality": "good",
        "sharpness_score": None,
        "brightness_score": None,
    }

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        result["valid"] = False
        result["error"] = f"Unsupported file extension '.{ext}'. Supported formats: JPG, JPEG, PNG."
        return result

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        result["valid"] = False
        result["error"] = f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB."
        return result

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
        result["width"], result["height"] = image.size
        result["format"] = image.format or ext.upper()
    except Exception as exc:
        logger.warning("Corrupted image upload: %s", exc)
        result["valid"] = False
        result["error"] = "The uploaded file is corrupted or not a valid readable image."
        return result

    if result["width"] < 128 or result["height"] < 128:
        result["valid"] = False
        result["error"] = (
            f"Image resolution ({result['width']}x{result['height']}) is too low for analysis. "
            "Minimum required is 128x128."
        )
        return result

    try:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        gray = np.dot(rgb[..., :3], np.array([0.299, 0.587, 0.114], dtype=np.float32))
        sharpness = _estimate_sharpness(gray)
        brightness = float(np.mean(gray))

        result["sharpness_score"] = round(sharpness, 2)
        result["brightness_score"] = round(brightness, 2)

        if sharpness < 20.0:
            result["quality"] = "blurry"
            result["quality_warning"] = (
                "Image appears significantly blurry. Higher resolution leaf close-up recommended."
            )
        elif brightness < 25.0:
            result["quality"] = "dark"
            result["quality_warning"] = "Image appears too dark. Clear daylight lighting recommended."
        elif brightness > 235.0:
            result["quality"] = "overexposed"
            result["quality_warning"] = "Image appears overexposed with extreme glare."
    except Exception as exc:
        logger.debug("Image quality analysis skipped: %s", exc)

    return result


def load_image_as_pil(file_bytes: bytes) -> Image.Image:
    """Load image bytes into a normalized RGB Pillow image."""
    img = Image.open(io.BytesIO(file_bytes))
    img.load()
    return img.convert("RGB")
