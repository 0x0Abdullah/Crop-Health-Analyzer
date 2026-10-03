import logging
from typing import Dict, Any, Optional
from src.utils.image_utils import load_image_as_pil
from src.vision.predictor import analyze_plant_image

logger = logging.getLogger("vision_agent")

class VisionAgent:
    """
    Vision Agent:
    Preprocesses uploaded plant image, executes vision classifier,
    and produces structured vision predictions.
    """
    def run(self, crop: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        if not image_bytes:
            return {
                "available": False,
                "predictions": [],
                "top_prediction": None,
                "image_quality": "none",
                "supported": False,
                "note": "No image provided for vision analysis."
            }

        try:
            pil_img = load_image_as_pil(image_bytes)
            analysis = analyze_plant_image(pil_img, crop)
            return analysis
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {
                "available": False,
                "error": str(e),
                "predictions": [],
                "top_prediction": None,
                "image_quality": "error",
                "supported": False
            }

    def run_many(self, crop: str, image_bytes_list):
        """Analyze each supplied image independently and return a weighted evidence fusion."""
        analyses=[]
        for i,b in enumerate(image_bytes_list[:4]):
            result=self.run(crop,b)
            result["image_index"]=i
            analyses.append(result)
        preds={}
        for a in analyses:
            quality=a.get("image_quality")
            weight=1.0 if quality=="good" else 0.5
            for pred in a.get("predictions",[]):
                label=pred.get("label","")
                preds[label]=preds.get(label,0.0)+float(pred.get("confidence",0.0))*weight
        ranked=sorted(preds.items(),key=lambda x:x[1],reverse=True)
        combined=[{"label":label,"support_score":round(score,3)} for label,score in ranked[:4]]
        top=combined[0] if combined else None
        return {"available":bool(analyses),"mode":"Multi-image feature analysis","images":analyses,"predictions":combined,"top_prediction":{"label":top["label"],"confidence":top["support_score"]} if top else None,"image_quality":"good" if any(a.get("image_quality")=="good" for a in analyses) else "uncertain","supported":bool(analyses)}
