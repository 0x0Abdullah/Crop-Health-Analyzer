import unittest
from src.agents.input_agent import InputAgent
from src.agents.symptom_agent import SymptomAgent
from src.agents.risk_agent import RiskSeverityAgent
from src.agents.safety_agent import SafetyVerificationAgent

class TestAgents(unittest.TestCase):
    def test_input_agent(self):
        agent = InputAgent()
        res = agent.run(crop="Tomato", symptoms="Concentric ring spots on lower leaves")
        self.assertTrue(res["valid"])
        self.assertEqual(res["input_mode"], "symptoms_only")

    def test_symptom_agent(self):
        agent = SymptomAgent()
        res = agent.run("Yellowing leaves with curling and brown spots", crop="Tomato")
        self.assertIn("Yellowing leaves / Chlorosis", res["observed_symptoms"])
        self.assertIn("Upward or inward leaf curling", res["observed_symptoms"])

    def test_risk_severity_agent(self):
        agent = RiskSeverityAgent()
        retrieved_evidence = [{
            "condition": "Early Blight",
            "score": 0.85,
            "crop": "Tomato"
        }]
        res = agent.run(
            crop="Tomato",
            vision_result={"available": False, "predictions": []},
            symptom_result={"observed_symptoms": ["concentric spots"]},
            retrieved_evidence=retrieved_evidence
        )
        self.assertEqual(res["evidence_fusion"]["top_condition"], "Early Blight")
        self.assertGreater(res["evidence_fusion"]["confidence"], 0.70)

    def test_safety_agent(self):
        agent = SafetyVerificationAgent()
        mgmt = {"verified_treatments": ["Fixed Copper Soap", "DDT_unlabeled_chemical"]}
        res = agent.run(
            crop="Tomato",
            condition="Early Blight",
            confidence=0.80,
            management_guidance=mgmt,
            retrieved_evidence=[]
        )
        self.assertTrue(res["is_safe"])
        # Unsafe chemical should be filtered
        self.assertNotIn("DDT_unlabeled_chemical", mgmt["verified_treatments"])

if __name__ == "__main__":
    unittest.main()
