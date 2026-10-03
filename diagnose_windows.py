"""Basic local environment diagnostic for Crop Health Analyzer."""
import importlib.util
import sys

print(f"Python: {sys.version}")
for name in ("streamlit", "PIL", "numpy", "requests"):
    print(f"{name}: {'installed' if importlib.util.find_spec(name) else 'MISSING'}")
print("OpenCV/cv2: NOT REQUIRED by this application")
