from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class AnalysisRecord:
    id: Optional[int] = None
    session_id: str = ""
    crop: str = ""
    input_mode: str = ""
    symptoms: str = ""
    has_image: bool = False
    result_condition: str = ""
    confidence: float = 0.0
    severity: str = "Unknown"
    report_json: str = "{}"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ChatMessageRecord:
    id: Optional[int] = None
    analysis_id: Optional[int] = None
    session_id: str = ""
    role: str = "" # 'user' or 'assistant'
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class EvidenceRecord:
    id: Optional[int] = None
    analysis_id: Optional[int] = None
    source: str = ""
    title: str = ""
    content: str = ""
    url: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
