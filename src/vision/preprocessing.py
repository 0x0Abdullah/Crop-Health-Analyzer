import logging
from typing import Any, Dict, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger("vision_preprocessing")


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """Convert uint8 RGB pixels to HSV ranges compatible with OpenCV-style thresholds.

    H is returned in [0, 179], S and V in [0, 255]. Implemented with NumPy so
    the application does not require native OpenCV DLLs.
    """
    arr = rgb.astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    maxc = np.max(arr, axis=-1)
    minc = np.min(arr, axis=-1)
    delta = maxc - minc

    h = np.zeros_like(maxc)
    nonzero = delta > 1e-7

    rc = ((g - b) / np.maximum(delta, 1e-7)) % 6.0
    gc = ((b - r) / np.maximum(delta, 1e-7)) + 2.0
    bc = ((r - g) / np.maximum(delta, 1e-7)) + 4.0
    h = np.where((maxc == r) & nonzero, rc, h)
    h = np.where((maxc == g) & nonzero, gc, h)
    h = np.where((maxc == b) & nonzero, bc, h)
    h = h * 30.0  # 360 degrees -> OpenCV's 0..179

    s = np.where(maxc > 1e-7, delta / np.maximum(maxc, 1e-7), 0.0) * 255.0
    v = maxc * 255.0
    return np.stack((h, s, v), axis=-1)


def preprocess_leaf_image(image: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> Dict[str, Any]:
    """Preprocess a leaf image and extract lightweight visual features."""
    rgb_img = image.convert("RGB")
    resized_img = rgb_img.resize(target_size, Image.Resampling.BILINEAR)
    img_array = np.asarray(resized_img, dtype=np.float32) / 255.0

    rgb_array = np.asarray(rgb_img, dtype=np.uint8)
    hsv = _rgb_to_hsv(rgb_array)

    green_mask = (
        (hsv[..., 0] >= 30)
        & (hsv[..., 0] <= 85)
        & (hsv[..., 1] >= 40)
        & (hsv[..., 1] <= 255)
        & (hsv[..., 2] >= 40)
        & (hsv[..., 2] <= 255)
    )
    brown_mask = (
        (hsv[..., 0] >= 10)
        & (hsv[..., 0] <= 30)
        & (hsv[..., 1] >= 30)
        & (hsv[..., 1] <= 255)
        & (hsv[..., 2] >= 30)
        & (hsv[..., 2] <= 255)
    )

    total = float(hsv.shape[0] * hsv.shape[1])
    green_ratio = float(np.sum(green_mask) / total)
    lesion_ratio = float(np.sum(brown_mask) / total)

    return {
        "resized_pil": resized_img,
        "normalized_tensor": img_array,
        "green_ratio": green_ratio,
        "lesion_ratio": lesion_ratio,
        "original_size": image.size,
    }
