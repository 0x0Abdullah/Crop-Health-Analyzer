from tests import _env  # noqa: F401  (throw-away DB, must come before any src import)
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src.database.db import init_db
from src.database.repository import DatabaseRepository
from src.settings import DEFAULTS, load_settings, reset_settings, sanitize, save_setting


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.db = Path(tempfile.mkdtemp()) / "t.db"
        init_db(self.db)
        self.repo = DatabaseRepository(self.db)

    def test_defaults_when_empty(self):
        self.assertEqual(load_settings(self.repo), DEFAULTS)

    def test_language_and_units_are_gone(self):
        self.assertNotIn("language", DEFAULTS)
        self.assertNotIn("units", DEFAULTS)

    def test_roundtrip_and_persistence(self):
        save_setting(self.repo, "theme", "Dark")
        save_setting(self.repo, "text_size", "Large")
        fresh = DatabaseRepository(self.db)           # a "new session"
        s = load_settings(fresh)
        self.assertEqual((s["theme"], s["text_size"]), ("Dark", "Large"))

    def test_invalid_values_fall_back(self):
        self.assertEqual(sanitize({"theme": "Neon", "reduce_motion": "yes", "bogus": 1})["theme"], "System")
        self.assertIs(sanitize({"reduce_motion": "yes"})["reduce_motion"], False)
        self.assertEqual(sanitize({"default_crop": "Moon Cabbage"}, crops=["Tomato"])["default_crop"], "")
        with self.assertRaises(KeyError):
            save_setting(self.repo, "language", "French")

    def test_reset(self):
        save_setting(self.repo, "theme", "Dark")
        reset_settings(self.repo)
        self.assertEqual(load_settings(self.repo)["theme"], "System")


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.db = Path(tempfile.mkdtemp()) / "t.db"
        init_db(self.db)
        self.repo = DatabaseRepository(self.db)

    def test_reminders_have_plant_names_and_due_filter(self):
        pid = self.repo.create_plant("Backyard", "Tomato")
        self.repo.create_reminder(pid, (date.today() - timedelta(days=1)).isoformat(), "late")
        self.repo.create_reminder(pid, (date.today() + timedelta(days=5)).isoformat(), "later")
        self.assertEqual({r["plant_name"] for r in self.repo.get_reminders()}, {"Backyard"})
        self.assertEqual([r["note"] for r in self.repo.get_due_reminders()], ["late"])
        rid = self.repo.get_due_reminders()[0]["id"]
        self.repo.complete_reminder(rid)
        self.assertEqual(self.repo.get_due_reminders(), [])

    def test_delete_plant_cascades_reminders_but_keeps_assessments(self):
        from src.workflow.pipeline import CropDoctorPipeline
        pid = self.repo.create_plant("P", "Tomato")
        self.repo.create_reminder(pid, date.today().isoformat(), "x")
        res = CropDoctorPipeline(db_repo=self.repo).run("Tomato", "brown spots with rings", plant_id=pid, session_id="s")
        self.repo.delete_plant(pid)
        self.assertEqual(self.repo.get_reminders(), [])
        self.assertIsNone(self.repo.get_analysis_by_id(res["analysis_id"])["plant_id"])

    def test_delete_analysis_and_export(self):
        from src.workflow.pipeline import CropDoctorPipeline
        res = CropDoctorPipeline(db_repo=self.repo).run("Tomato", "yellow leaves and brown spots", session_id="s")
        self.assertEqual(self.repo.get_counts()["assessments"], 1)
        self.assertEqual(len(self.repo.export_all()["analyses"]), 1)
        self.repo.delete_analysis(res["analysis_id"])
        self.assertEqual(self.repo.get_counts()["assessments"], 0)
        self.assertEqual(self.repo.export_all()["evidence"], [])


if __name__ == "__main__":
    unittest.main()
