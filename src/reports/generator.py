from typing import Dict, Any
from src.agents.report_agent import ReportAgent

def generate_crop_health_report(workflow_state: Dict[str, Any]) -> str:
    agent = ReportAgent()
    return agent.run(workflow_state)
