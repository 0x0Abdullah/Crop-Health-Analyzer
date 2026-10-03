import logging
from typing import Dict, Any, List
from src.rag.retriever import retrieve_agricultural_evidence

logger = logging.getLogger("knowledge_agent")

class KnowledgeAgent:
    """
    RAG Knowledge Agent:
    Retrieves grounded evidence from knowledge base given crop, vision predictions,
    and symptom findings.
    """
    def run(self, crop: str, symptoms: str = "", vision_label: str = "") -> List[Dict[str, Any]]:
        try:
            evidence = retrieve_agricultural_evidence(
                crop=crop,
                symptoms=symptoms,
                vision_label=vision_label,
                top_k=4
            )
            return evidence
        except Exception as e:
            logger.error(f"KnowledgeAgent retrieval failed: {e}")
            return []
