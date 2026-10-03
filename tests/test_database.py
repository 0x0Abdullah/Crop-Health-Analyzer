import unittest
import tempfile
from pathlib import Path
from src.database.db import init_db
from src.database.repository import DatabaseRepository
from src.database.models import AnalysisRecord, ChatMessageRecord

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_crop_doctor.db"
        init_db(self.db_path)
        self.repo = DatabaseRepository(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_analysis(self):
        rec = AnalysisRecord(
            session_id="test_session_123",
            crop="Tomato",
            input_mode="symptoms_only",
            symptoms="Yellowing leaves with target spots",
            has_image=False,
            result_condition="Early Blight",
            confidence=0.82,
            severity="Moderate",
            report_json="# Test Report"
        )
        evidence = [{"source": "FAO Test", "title": "Test Rec", "content": "Evidence text", "url": "https://test.org"}]
        
        analysis_id = self.repo.save_analysis(rec, evidence)
        self.assertGreater(analysis_id, 0)

        history = self.repo.get_analysis_history(limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["crop"], "Tomato")
        self.assertEqual(history[0]["result_condition"], "Early Blight")

        fetched = self.repo.get_analysis_by_id(analysis_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(len(fetched["evidence"]), 1)
        self.assertEqual(fetched["evidence"][0]["source"], "FAO Test")

    def test_chat_message_persistence(self):
        msg = ChatMessageRecord(
            session_id="test_session_123",
            role="assistant",
            message="Test assistant response"
        )
        msg_id = self.repo.save_chat_message(msg)
        self.assertGreater(msg_id, 0)

        messages = self.repo.get_chat_messages("test_session_123")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["message"], "Test assistant response")

if __name__ == "__main__":
    unittest.main()
