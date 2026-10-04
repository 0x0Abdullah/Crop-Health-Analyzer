import unittest

from src.utils.installer import (
    generate_desktop_app_zip,
    generate_mobile_shortcut_html,
    generate_mobile_url_shortcut,
    generate_windows_launcher_bat,
)


class InstallerUtilsTests(unittest.TestCase):
    def test_generate_windows_launcher_bat(self):
        content = generate_windows_launcher_bat("http://localhost:8501")
        self.assertIsInstance(content, bytes)
        text = content.decode("utf-8")
        self.assertIn("chrome.exe --app=", text)
        self.assertIn("http://localhost:8501", text)

    def test_generate_mobile_shortcut_html(self):
        content = generate_mobile_shortcut_html("http://localhost:8501")
        self.assertIsInstance(content, bytes)
        text = content.decode("utf-8")
        self.assertIn("apple-mobile-web-app-capable", text)
        self.assertIn("Crop Health Analyzer", text)

    def test_generate_mobile_url_shortcut(self):
        content = generate_mobile_url_shortcut("http://localhost:8501")
        self.assertIsInstance(content, bytes)
        text = content.decode("utf-8")
        self.assertIn("[InternetShortcut]", text)
        self.assertIn("URL=http://localhost:8501", text)

    def test_generate_desktop_app_zip(self):
        content = generate_desktop_app_zip("http://localhost:8501")
        self.assertIsInstance(content, bytes)
        self.assertTrue(len(content) > 100)


if __name__ == "__main__":
    unittest.main()
