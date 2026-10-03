"""Regression tests for bugs found while auditing the app."""
from tests import _env  # noqa: F401  (throw-away DB, must come before any src import)
import json
import tempfile
import unittest
from pathlib import Path

from src.agents.risk_agent import RiskSeverityAgent
from src.agents.symptom_agent import SymptomAgent
from src.database.db import init_db
from src.database.repository import DatabaseRepository
from src.llm.client import LLMClient
from src.ui.pages.analyze import build_symptom_text
from src.workflow.pipeline import CropDoctorPipeline

ROOT = Path(__file__).resolve().parents[1]


class SymptomMatchingTests(unittest.TestCase):
    def test_whole_plant_is_not_a_hole(self):
        out = SymptomAgent().run("Affected part: whole plant.", "Tomato")["observed_symptoms"]
        self.assertNotIn("Insect feeding holes or defoliation", out)

    def test_word_boundaries(self):
        a = SymptomAgent()
        self.assertEqual(a.run("spring rains during planting", "Tomato")["observed_symptoms"][0][:7], "General")
        self.assertIn("Insect feeding holes or defoliation", a.run("holes in the leaves", "Tomato")["observed_symptoms"])

    def test_new_symptoms_recognised(self):
        out = SymptomAgent().run("Stem lesions; fruit damage; root problems; rapid spreading", "Tomato")["observed_symptoms"]
        for expected in ("Stem or leaf lesions", "Fruit damage or rot", "Root problems or rot", "Rapidly spreading symptoms"):
            self.assertIn(expected, out)


class FormTextTests(unittest.TestCase):
    def test_no_boilerplate_when_nothing_entered(self):
        self.assertEqual(build_symptom_text([], "", "Not sure", "Not sure"), "")

    def test_only_meaningful_context_is_added(self):
        t = build_symptom_text(["Brown spots"], "rings", "Quickly", "Leaves")
        self.assertIn("Brown spots", t); self.assertIn("Spreading rapidly", t); self.assertIn("leaves", t)
        self.assertNotIn("First noticed", t)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        db = Path(tempfile.mkdtemp()) / "t.db"
        init_db(db)
        self.repo = DatabaseRepository(db)
        self.pipe = CropDoctorPipeline(db_repo=self.repo)

    def test_empty_input_is_rejected(self):
        res = self.pipe.run("Tomato", "", session_id="s")
        self.assertFalse(res["validation"]["valid"])
        self.assertNotIn("analysis_id", res)

    def test_state_has_no_image_bytes_and_prompt_is_small(self):
        data = (ROOT / "data/sample/apple_scab.png").read_bytes()
        res = self.pipe.run("Apple", "", image_bytes=data, image_bytes_list=[data], image_name="a.png", session_id="s")
        self.assertNotIn("image_bytes", res["validation"])
        self.assertLess(len(json.dumps(res, default=str)), 200_000)
        self.assertLess(len(LLMClient()._report_prompt(res)), 20_000)

    def test_confidence_is_real_and_no_false_low_confidence_warning(self):
        res = self.pipe.run("Tomato", "brown spots with concentric rings on lower leaves", session_id="s")
        self.assertGreater(self.repo.get_analysis_by_id(res["analysis_id"])["confidence"], 0.45)
        self.assertFalse(any("Low diagnostic" in n for n in res["safety_result"]["safety_notes"]))

    def test_photo_without_disease_signal_is_not_a_diagnosis(self):
        fusion = RiskSeverityAgent().run(
            "Tomato", {"available": True, "predictions": [{"label": "Healthy Tomato Leaf", "confidence": 1.0}]},
            {"observed_symptoms": []}, [{"condition": "Early Blight", "score": 0.2}])["evidence_fusion"]
        self.assertEqual(fusion["top_condition"], "No clear problem detected")
        self.assertNotEqual(fusion["evidence_level"], "Moderate evidence")

    def test_vague_text_is_limited_evidence(self):
        res = self.pipe.run("Tomato", "looks sick", session_id="s")
        self.assertEqual(res["evidence_fusion"]["evidence_level"], "Limited evidence")


class AssistantFallbackTests(unittest.TestCase):
    def test_intents_use_the_assessment(self):
        db = Path(tempfile.mkdtemp()) / "t.db"; init_db(db)
        res = CropDoctorPipeline(db_repo=DatabaseRepository(db)).run("Tomato", "brown spots with rings", session_id="s")
        ctx = {"crop": "Tomato", "has_analysis": True, "result_condition": "Early Blight", "severity": "Moderate",
               "evidence_level": "Moderate evidence", "symptoms": "brown spots", "management_guidance": res["management_guidance"],
               "retrieved_evidence": res["retrieved_evidence"]}
        c = LLMClient()
        self.assertIn("start here", c.generate_chat_response("what should I do first?", ctx, []))
        self.assertIn("Lower-impact", c.generate_chat_response("any organic options?", ctx, []))
        self.assertIn("won't guess", c.generate_chat_response("which fungicide dose?", {**ctx, "management_guidance": {}, "retrieved_evidence": []}, []) )

    def test_general_question_without_assessment_uses_knowledge_base(self):
        self.assertIn("knowledge base", LLMClient().generate_chat_response("what is powdery mildew on grapes", {}, []).lower())

    def test_no_dose_invented_and_api_key_never_in_url(self):
        c = LLMClient(provider="gemini", api_key="secret-key-123456", model="m")
        self.assertTrue(c.is_configured())
        self.assertNotIn("secret", str(c.describe()))


if __name__ == "__main__":
    unittest.main()
