import logging
from typing import Dict, Any, Optional, Callable, List
from src.workflow.state import create_initial_workflow_state
from src.agents.input_agent import InputAgent
from src.agents.vision_agent import VisionAgent
from src.agents.symptom_agent import SymptomAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.risk_agent import RiskSeverityAgent
from src.agents.treatment_agent import TreatmentIPMAgent
from src.agents.safety_agent import SafetyVerificationAgent
from src.agents.report_agent import ReportAgent
from src.safety.verifier import verify_report_safety
from src.database.repository import DatabaseRepository
from src.database.models import AnalysisRecord
from src.memory.short_term import ShortTermMemoryManager

logger = logging.getLogger("workflow_pipeline")

class CropDoctorPipeline:
    """
    Central Agentic AI Workflow Orchestrator for Crop Health Analyzer.
    Executes agents sequentially in a stateful pipeline.
    """
    def __init__(self, db_repo: Optional[DatabaseRepository] = None):
        self.input_agent = InputAgent()
        self.vision_agent = VisionAgent()
        self.symptom_agent = SymptomAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.risk_agent = RiskSeverityAgent()
        self.treatment_agent = TreatmentIPMAgent()
        self.safety_agent = SafetyVerificationAgent()
        self.report_agent = ReportAgent()
        self.db_repo = db_repo or DatabaseRepository()

    def run(
        self,
        crop: str,
        symptoms: str,
        image_bytes: Optional[bytes] = None,
        image_bytes_list: Optional[List[bytes]] = None,
        image_name: Optional[str] = None,
        environment: Optional[Dict[str, Any]] = None,
        plant_id: Optional[int] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        image_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Runs the complete end-to-end multi-agent crop health analysis workflow.
        """
        def update_progress(msg: str, pct: float):
            if progress_callback:
                progress_callback(msg, pct)

        state = create_initial_workflow_state(
            session_id=session_id or ShortTermMemoryManager.get_session_id(),
            crop=crop,
            symptoms=symptoms,
            has_image=image_bytes is not None
        )

        # Stage 1: Input Validation Agent
        update_progress("✓ Validating crop input & image integrity...", 0.10)
        val_res = self.input_agent.run(
            crop=crop,
            symptoms=symptoms,
            image_bytes=image_bytes,
            image_name=image_name
        )
        # Raw image bytes must not live in the shared state: the state is serialised into LLM prompts
        # and kept in the browser session, and a multi-MB payload breaks both.
        state["validation"] = {k: v for k, v in val_res.items() if k != "image_bytes"}
        state["input_mode"] = val_res["input_mode"]

        if not val_res["valid"]:
            state["errors"] = val_res["issues"]
            state["final_report"] = f"### ⚠️ Input Validation Issues\n\n" + "\n".join([f"* {issue}" for issue in val_res["issues"]])
            return state

        # Stage 2: Computer Vision Agent
        update_progress("✓ Executing Computer Vision feature analysis...", 0.25)
        if val_res["has_image"]:
            if image_bytes_list and len(image_bytes_list) > 1:
                vis_res = self.vision_agent.run_many(crop=crop, image_bytes_list=image_bytes_list)
            else:
                vis_res = self.vision_agent.run(crop=crop, image_bytes=image_bytes)
        else:
            vis_res = {"available": False, "predictions": [], "note": "No image provided."}
        state["vision_result"] = vis_res

        # Stage 3: Symptom Analysis Agent
        update_progress("✓ Analyzing reported symptoms & patterns...", 0.40)
        sympt_res = self.symptom_agent.run(symptoms_text=symptoms, crop=crop)
        state["symptom_result"] = sympt_res

        # Stage 4: Knowledge Agent (RAG)
        update_progress("✓ Retrieving grounded agricultural knowledge (RAG)...", 0.55)
        vis_top_label = vis_res.get("top_prediction", {}).get("label", "") if vis_res.get("available") else ""
        evidence = self.knowledge_agent.run(crop=crop, symptoms=symptoms, vision_label=vis_top_label)
        state["retrieved_evidence"] = evidence

        # Stage 5: Risk & Severity Agent (Evidence Fusion)
        update_progress("✓ Evaluating evidence fusion & risk severity...", 0.70)
        risk_res = self.risk_agent.run(
            crop=crop,
            vision_result=vis_res,
            symptom_result=sympt_res,
            retrieved_evidence=evidence
        )
        state["evidence_fusion"] = risk_res["evidence_fusion"]
        state["risk_assessment"] = risk_res["risk_assessment"]
        if risk_res["evidence_fusion"].get("no_signal"):
            evidence = []                      # nothing identified -> don't present unrelated disease records as sources
            state["retrieved_evidence"] = []

        # Stage 6: Treatment & IPM Agent
        update_progress("✓ Synthesizing IPM & non-chemical guidance...", 0.80)
        top_cond = risk_res["evidence_fusion"]["top_condition"]
        mgmt_res = self.treatment_agent.run(crop=crop, condition=top_cond, retrieved_evidence=evidence)
        state["management_guidance"] = mgmt_res

        # Stage 7: Safety & Verification Agent
        update_progress("✓ Executing safety verification checks...", 0.90)
        evidence_level = risk_res["evidence_fusion"].get("evidence_level", "Insufficient evidence")
        conf = float(risk_res["evidence_fusion"].get("confidence", 0.0) or 0.0)
        if evidence_level in ("Limited evidence", "Insufficient evidence"):
            conf = min(conf, 0.44)  # keep the low-confidence safeguard for genuinely weak evidence only
        safety_res = self.safety_agent.run(
            crop=crop,
            condition=top_cond,
            confidence=conf,
            management_guidance=mgmt_res,
            retrieved_evidence=evidence
        )
        state["safety_result"] = safety_res

        # Stage 8: Generative AI Report Agent
        update_progress("✓ Generating structured crop health report...", 0.95)
        raw_report = self.report_agent.run(state)
        final_verified_report = verify_report_safety(raw_report, state)
        state["final_report"] = final_verified_report

        # Stage 9: Persistence (SQLite & Session Memory)
        update_progress("✓ Storing analysis record in SQLite database...", 1.00)
        analysis_rec = AnalysisRecord(
            session_id=state["session_id"],
            crop=crop,
            input_mode=state["input_mode"],
            symptoms=symptoms,
            has_image=val_res["has_image"],
            result_condition=top_cond,
            confidence=conf,
            severity=risk_res["risk_assessment"]["severity"],
            report_json=final_verified_report,
        )
        analysis_id = self.db_repo.save_analysis(analysis_rec, evidence, plant_id=plant_id, environment=environment, evidence_level=evidence_level, image_metadata=(image_metadata if image_metadata else ([val_res.get("image_validation") or {}] if val_res.get("has_image") else [])))
        state["analysis_id"] = analysis_id
        state["environment"] = environment or {}
        state["plant_id"] = plant_id
        state["evidence_fusion"]["evidence_level"] = evidence_level

        # Update Session Memory
        ShortTermMemoryManager.set_current_analysis(state)

        return state
