import unittest
from io import BytesIO

from PIL import Image

from src.utils.image_utils import validate_image_file
from src.vision.preprocessing import preprocess_leaf_image


class TestImagePortability(unittest.TestCase):
    def test_image_stack_does_not_require_cv2(self):
        image = Image.new("RGB", (256, 256), (80, 150, 70))
        buf = BytesIO()
        image.save(buf, format="PNG")
        payload = buf.getvalue()

        result = validate_image_file(payload, "leaf.png")
        self.assertTrue(result["valid"])
        self.assertEqual(result["format"], "PNG")

        features = preprocess_leaf_image(image)
        self.assertIn("green_ratio", features)
        self.assertIn("lesion_ratio", features)


if __name__ == "__main__":
    unittest.main()
