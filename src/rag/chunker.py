from typing import Any, Dict, List


def _as_list(value: Any) -> List[str]:
    """Normalize a JSON field that may be a list, string, null, or another value."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def chunk_knowledge_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform structured knowledge records into searchable chunks."""
    chunks: List[Dict[str, Any]] = []

    for doc in records:
        if not isinstance(doc, dict):
            continue

        doc_id = str(doc.get("id", "UNKNOWN"))
        crop = str(doc.get("crop", ""))
        condition = str(doc.get("condition", ""))
        source = str(doc.get("source", "Agricultural Extension Source"))
        title = str(doc.get("title", ""))
        url = str(doc.get("url", ""))
        content = str(doc.get("content", ""))

        symptoms_str = ", ".join(_as_list(doc.get("symptoms")))
        ipm_str = "; ".join(_as_list(doc.get("ipm")))
        prevention_str = "; ".join(_as_list(doc.get("prevention")))
        bio_str = "; ".join(_as_list(doc.get("biological_controls")))
        treatments_str = "; ".join(_as_list(doc.get("verified_treatments")))

        full_text = (
            f"Crop: {crop} | Condition: {condition} | Title: {title}\n"
            f"Description & Biology: {content}\n"
            f"Symptoms: {symptoms_str}\n"
            f"IPM Recommendations: {ipm_str}\n"
            f"Prevention & Cultural Practices: {prevention_str}\n"
            f"Biological Controls: {bio_str}\n"
            f"Verified Treatments: {treatments_str}"
        )

        chunks.append({
            "chunk_id": f"{doc_id}_main",
            "doc_id": doc_id,
            "crop": crop,
            "condition": condition,
            "source": source,
            "title": title,
            "url": url,
            "text": full_text,
            "raw_record": doc,
        })

    return chunks
