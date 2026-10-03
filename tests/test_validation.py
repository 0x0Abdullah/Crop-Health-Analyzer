import unittest
from src.utils.validation import validate_user_input

class TestValidation(unittest.TestCase):
    def test_valid_symptoms_only(self):
        res = validate_user_input(
            crop="Tomato",
            symptoms_text="Yellowing lower leaves with dark brown concentric target spots.",
            has_image=False
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["input_mode"], "symptoms_only")
        self.assertEqual(res["crop"], "Tomato")

    def test_missing_crop_and_symptoms(self):
        res = validate_user_input(
            crop="",
            symptoms_text="",
            has_image=False
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["input_mode"], "insufficient")
        self.assertGreater(len(res["issues"]), 0)

    def test_unsupported_crop(self):
        res = validate_user_input(
            crop="DragonFruitUnregistered",
            symptoms_text="Some symptoms text here",
            has_image=False
        )
        self.assertFalse(res["valid"])
        self.assertTrue(any("not currently in the supported" in issue for issue in res["issues"]))

if __name__ == "__main__":
    unittest.main()
