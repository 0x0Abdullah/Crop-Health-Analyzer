import unittest
import tempfile
from pathlib import Path
from src.database.db import init_db
from src.database.repository import DatabaseRepository
from src.workflow.pipeline import CropDoctorPipeline

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_crop_doctor.db"
        init_db(self.db_path)
        self.db_repo = DatabaseRepository(db_path=self.db_path)
        self.pipeline = CropDoctorPipeline(db_repo=self.db_repo)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_symptom_only_pipeline_flow(self):
        result = self.pipeline.run(
            crop="Tomato",
            symptoms="Lower leaves showing brown target spots with concentric rings and yellow margins.",
            session_id="test_wf_session"
        )
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual(result["input_mode"], "symptoms_only")
        self.assertEqual(result["evidence_fusion"]["top_condition"], "Early Blight")
        self.assertGreater(result["evidence_fusion"]["confidence"], 0.60)
        self.assertIn("Crop Health Analyzer", result["final_report"])
        self.assertGreater(result["analysis_id"], 0)

if __name__ == "__main__":
    unittest.main()
