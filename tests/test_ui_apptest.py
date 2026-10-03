"""UI smoke/flow tests using Streamlit's AppTest (no browser needed)."""
from tests import _env  # noqa: F401  (throw-away DB, must come before any src import)
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
PAGES = ["home", "analyze", "plants", "history", "assistant", "learn", "settings", "about"]


def fresh() -> AppTest:
    from src.ui.state import get_services
    get_services.clear()
    return AppTest.from_file(APP, default_timeout=60).run()


class UiTests(unittest.TestCase):
    def test_every_page_renders_without_exceptions(self):
        at = fresh()
        self.assertEqual(len(at.exception), 0)
        for page in PAGES:
            at.session_state["page"] = page
            at.run()
            self.assertEqual(len(at.exception), 0, f"{page}: {[e.value for e in at.exception]}")

    def test_language_option_removed_from_settings(self):
        at = fresh()
        at.session_state["page"] = "settings"; at.run()
        labels = [w.label for w in at.radio] + [w.label for w in at.selectbox]
        self.assertFalse(any("language" in str(l).lower() for l in labels))

    def test_theme_setting_applies_and_persists(self):
        at = fresh()
        at.session_state["page"] = "settings"; at.run()
        theme = next(r for r in at.radio if r.label == "Theme")
        theme.set_value("Dark").run()
        css = " ".join(m.value for m in at.markdown if "<style>" in m.value)
        self.assertIn("color-scheme:dark", css)
        self.assertNotIn("prefers-color-scheme", css)       # explicit Dark must not depend on the OS
        # a new session (browser refresh) restores it from the database
        again = fresh()
        css2 = " ".join(m.value for m in again.markdown if "<style>" in m.value)
        self.assertIn("color-scheme:dark", css2)
        again.session_state["page"] = "settings"; again.run()
        next(r for r in again.radio if r.label == "Theme").set_value("System").run()

    def test_system_theme_follows_os(self):
        from src.ui.theme import build_css
        css = build_css("System")
        self.assertIn("@media (prefers-color-scheme: dark)", css)
        self.assertIn("color-scheme:light", css)

    def test_theme_defines_every_color_via_variables_for_both_palettes(self):
        from src.ui.theme import LIGHT, DARK
        self.assertEqual(set(LIGHT), set(DARK))

    def test_empty_analysis_is_blocked(self):
        at = fresh()
        at.session_state["page"] = "analyze"; at.run()
        next(b for b in at.button if "Analyze crop" in b.label).click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertIsNone(at.session_state["current_analysis"] if "current_analysis" in at.session_state else None)
        self.assertTrue(any("Nothing to analyze" in str(e.value) for e in at.get("html")))

    def test_symptom_analysis_flow_opens_results(self):
        at = fresh()
        at.session_state["page"] = "analyze"; at.run()
        at.multiselect(key="an_symptoms").set_value(["Brown spots"]).run()
        next(b for b in at.button if "Analyze crop" in b.label).click().run()
        self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])
        self.assertEqual(at.session_state["page"], "history")
        self.assertEqual(at.session_state["current_analysis"]["crop"], "Tomato")
        self.assertGreater(at.session_state["current_analysis"]["analysis_id"], 0)

    def test_assistant_answers_quick_question(self):
        at = fresh()
        at.session_state["page"] = "assistant"; at.run()
        next(b for b in at.button if "What should I do first" in b.label).click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any(m.role == "assistant" if hasattr(m, "role") else True for m in at.chat_message))
        self.assertGreaterEqual(len(at.session_state["chat_messages"]), 2)


if __name__ == "__main__":
    unittest.main()
