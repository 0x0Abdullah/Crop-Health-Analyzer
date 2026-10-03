import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from src.config import KNOWLEDGE_DIR

logger = logging.getLogger("rag_loader")

def load_knowledge_documents() -> List[Dict[str, Any]]:
    """Loads knowledge records from data/knowledge/*.json files."""
    documents = []
    if not KNOWLEDGE_DIR.exists():
        logger.warning(f"Knowledge directory {KNOWLEDGE_DIR} does not exist.")
        return documents

    for json_file in KNOWLEDGE_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    documents.extend(data)
                elif isinstance(data, dict):
                    documents.append(data)
        except Exception as e:
            logger.error(f"Error loading knowledge file {json_file}: {e}")

    logger.info(f"Loaded {len(documents)} agricultural knowledge records.")
    return documents
