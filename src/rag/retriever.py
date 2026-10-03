from typing import List, Dict, Any, Optional
import logging
from src.rag.vector_store import AgriculturalVectorStore

logger = logging.getLogger("rag_retriever")

_global_vector_store = None

def get_vector_store() -> AgriculturalVectorStore:
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = AgriculturalVectorStore()
        _global_vector_store.build_index()
    return _global_vector_store

def retrieve_agricultural_evidence(
    crop: str,
    symptoms: str = "",
    vision_label: str = "",
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Retrieves grounded evidence from knowledge base based on crop, symptoms, and vision predictions.
    """
    store = get_vector_store()
    
    # Construct rich query
    query_parts = [f"Crop: {crop}"]
    if vision_label:
        query_parts.append(f"Condition: {vision_label}")
    if symptoms:
        query_parts.append(f"Symptoms: {symptoms}")
        
    full_query = " ".join(query_parts)
    
    results = store.similarity_search(query=full_query, crop_filter=crop, top_k=top_k)
    return results
