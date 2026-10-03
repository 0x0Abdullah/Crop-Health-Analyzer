from typing import Dict, Any
from PIL import Image
from src.vision.model import PlantVisionClassifier

_global_vision_classifier = None

def get_vision_classifier() -> PlantVisionClassifier:
    global _global_vision_classifier
    if _global_vision_classifier is None:
        _global_vision_classifier = PlantVisionClassifier()
    return _global_vision_classifier

def analyze_plant_image(image: Image.Image, crop: str) -> Dict[str, Any]:
    """Helper function to execute vision analysis on an image."""
    classifier = get_vision_classifier()
    return classifier.predict(image, crop)
