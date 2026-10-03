import logging
from typing import Dict, Any
from src.llm.client import LLMClient

logger = logging.getLogger("report_agent")

class ReportAgent:
    """
    Report Generation Agent:
    Uses LLM client (or grounded generator) to synthesize workflow state
    into a structured crop health report.
    """
    def __init__(self):
        self.llm_client = LLMClient()

    def run(self, workflow_state: Dict[str, Any]) -> str:
        try:
            report_text = self.llm_client.generate_report(workflow_state)
            return report_text
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return "# Crop Health Analysis Report\n\nReport generation encountered an issue. Please review individual section cards above."
