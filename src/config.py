import os
import json
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Base Directory Setup (relative, Streamlit Community Cloud safe)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CROPS_DIR = DATA_DIR / "crops"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = Path(os.getenv("CROP_DB_PATH")) if os.getenv("CROP_DB_PATH") else DATABASE_DIR / "crop_doctor.db"

# Ensure directories exist
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Application Settings
APP_TITLE = "Crop Health Analyzer"
APP_SUBTITLE = "AI-powered crop health analysis and agricultural guidance."
APP_VERSION = "2.0.0"
DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.55"))

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "fallback").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
# gemini-1.5-flash was retired by Google; "gemini-flash-latest" always points at the current Flash model.
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-latest")

# Feature Flags
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

# Load Supported Crops
def get_supported_crops():
    crop_file = CROPS_DIR / "crops.json"
    if crop_file.exists():
        with open(crop_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"id": "tomato", "name": "Tomato", "supported": True},
        {"id": "potato", "name": "Potato", "supported": True},
        {"id": "corn", "name": "Corn (Maize)", "supported": True},
        {"id": "rice", "name": "Rice", "supported": True},
        {"id": "apple", "name": "Apple", "supported": True},
        {"id": "grape", "name": "Grape", "supported": True},
        {"id": "wheat", "name": "Wheat", "supported": True},
        {"id": "cotton", "name": "Cotton", "supported": True},
        {"id": "pepper", "name": "Bell Pepper / Chili", "supported": True},
        {"id": "strawberry", "name": "Strawberry", "supported": True}
    ]

SUPPORTED_CROPS = get_supported_crops()
SUPPORTED_CROP_NAMES = [crop["name"] for crop in SUPPORTED_CROPS if crop.get("supported", True)]
