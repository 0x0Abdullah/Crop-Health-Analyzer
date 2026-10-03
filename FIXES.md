# Crop Health Analyzer - Fixes Applied

## Version 2.0 — UI/UX overhaul and functional audit

### Dark theme
- **Root cause:** only a few widgets were re-coloured for dark mode while Streamlit's own light colours stayed on the rest (nav buttons, uploader, camera, dropdown arrows, tooltips, alerts) and the disclaimer box used a light background with light text. Streamlit 1.5x also no longer exposes the `data-baseweb` hooks the old CSS targeted.
- New design-token theme (`src/ui/theme.py`): one set of CSS variables, two palettes, all widgets styled from them. Tables, alerts and badges are our own themed HTML (no canvas dataframes or pre-coloured alerts).
- Light / Dark / System (follows OS). Contrast of all visible text measured ≥ 4.5:1 on every page in all modes, on desktop and mobile.

### Settings
- Removed *Language* (changed nothing) and *Units* (nothing used them).
- Added persistent settings (SQLite `settings` table, validated on load), appearance controls, real preferences, AI-engine status, JSON export, guarded deletion, restore-defaults, install instructions.
- Settings sections no longer jump back to the first tab on every change (Streamlit tabs reset on rerun; replaced with a state-backed selector, also on Learn and Results).

### Functional bugs fixed
- "Continue with available evidence" on poor photos never ran the analysis (checkbox triggered a rerun that lost the form submit).
- Photo previews/quality feedback were hidden behind the form submit and never seen; the uploader claimed 200 MB while the app accepts 8 MB.
- Submitting with nothing entered produced a made-up result (form always added boilerplate text; "Whole plant" matched the keyword "hole").
- Symptom keyword matching now uses word boundaries ("spring"/"ring", "trust"/"rust"…) and recognises stem lesions, fruit damage, root problems and rapid spreading (previously "rapid spreading" never raised severity).
- Evidence fusion counted retrieved records as corroboration even with no symptoms and a "healthy" photo, so photo-only runs claimed *moderate evidence* for a disease. Now: healthy photo without symptoms → "No clear problem detected"; unrecognised free text → limited evidence.
- Confidence was hard-coded to 0.0: every report carried a "low confidence" warning and the DB stored 0.0.
- The pipeline state kept raw image bytes and serialised them into LLM prompts (~3.3 MB); prompts are now compact (~4 KB).
- LLM: retired default model `gemini-1.5-flash` replaced; Gemini key sent in a header instead of the URL; proper system instruction and history handling; the AI-unavailable case is reported in the UI.
- Chat: only assistant messages were saved (now both, honouring the new setting); offline assistant rewritten (intent-aware, uses the assessment and knowledge base, never invents doses).
- Compare view had Previous/Current defaults reversed; saved assessments could not be opened; the full written report was never shown or downloadable.
- Reminders could not be completed or deleted and showed "plant #id"; plants could not be deleted; SQLite foreign keys were never enforced (cascade deletes silently did nothing).
- "Install App" button did nothing (Streamlit does not run scripts/handlers from `st.markdown`; `manifest.json`/`sw.js` were never served). Removed the dead button and files; browser install instructions added to Settings.
- Streamlit config: `enableCORS=false` with XSRF protection caused a security warning; fixed. Navigation no longer stacks 8 buttons vertically on phones; page now persists on refresh and scrolls to top on change.

### Windows Application Control (DLL blocked) — scikit-learn removed
- `ImportError: DLL load failed while importing _radius_neighbors_classmode: An Application Control policy has blocked this file.` came from scikit-learn's compiled extensions, which a locked-down Windows policy blocks (same class of problem as the earlier OpenCV fix).
- The knowledge search now uses a built-in pure-Python TF-IDF + cosine implementation (`src/rag/embeddings.py`) with the same defaults as scikit-learn (bigrams, English stop words, smoothed IDF, L2 norm). Retrieval rankings were verified identical on test queries.
- `scikit-learn` and the unused `pandas` were removed from `requirements.txt`. The app now needs only streamlit, pillow, numpy, python-dotenv and requests. The full test suite passes with `sklearn` made un-importable.

### Tests
- 13 → 42 automated tests (settings, repository, regressions, UI flows). All pass under both `pytest` and `unittest`.

---

## Earlier fixes
- Fixed the `NameError: name 'Optional' is not defined` error in `src/rag/vector_store.py`.
- Hardened the TF-IDF/RAG pipeline against empty queries, empty indexes, invalid `top_k`, and malformed knowledge fields.
- Normalized knowledge-base list/string fields so malformed optional JSON fields do not crash indexing.
- Added safer vector-store initialization and error handling.
- Fixed chat history handling for Gemini/OpenAI requests so previous messages can be included.
- Fixed SQLite chat persistence so both user and assistant messages are stored.
- Removed generated Python `__pycache__` files from the deliverable.
- Existing automated tests were run: 12/12 passed.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

If you use an LLM provider, configure the variables in `.env` based on `.env.example`.

- Removed the hard runtime dependency on OpenCV (`cv2`) from image validation and visual preprocessing.
- Replaced the OpenCV-only color/sharpness operations with Pillow/NumPy implementations.
- Removed `opencv-python-headless` from `requirements.txt` so Windows Application Control policies that block `cv2` DLLs do not prevent startup.
- Added a portability regression test that imports the image utilities without requiring `cv2`.
