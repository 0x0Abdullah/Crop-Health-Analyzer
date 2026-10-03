"""Shared test environment: a throw-away database, no real LLM (imported before any src module)."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["CROP_DB_PATH"] = str(Path(tempfile.mkdtemp(prefix="cha_tests_")) / "tests.db")
os.environ.pop("LLM_API_KEY", None)           # tests must never call a real LLM
os.environ["LLM_PROVIDER"] = "fallback"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
