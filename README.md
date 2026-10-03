# 🌱 Crop Health Analyzer — Agricultural Decision Support System

[![Python](https://img.shields.io/badge/Python-3.9+-2D6A4F.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An AI-powered agricultural decision-support web application built with **Python and Streamlit**. The system assists farmers, agronomists, and researchers by analyzing crop health problems through:

1. **Crop/leaf image upload** (Computer Vision feature analysis)
2. **Symptom text description** (NLP symptom extraction & categorization)
3. **Combined image + symptoms**
4. **Retrieval-Augmented Generation (RAG)** grounded in FAO & Extension Service Knowledge Base
5. **Multi-Agent Workflow Pipeline** with Safety Verification & Integrated Pest Management (IPM) focus

> ⚠️ **SAFETY NOTICE:** Crop Health Analyzer provides agricultural decision support, not a guaranteed medical-style diagnosis system or unrestricted pesticide prescription generator. Always verify recommendations against product labels and local agricultural extension guidelines.

---

## ✨ What's new in 2.0

- **Dark mode that actually works.** Light, Dark or *System* (follows your device). Every colour is a theme variable, and every widget — buttons, dropdowns, file uploader, camera, expanders, chat, date picker — is themed from the same palette, so text can never end up the same colour as its background. Verified automatically: every visible piece of text on every page was measured at ≥ 4.5:1 contrast in all three modes.
- **Upgraded Settings** (saved automatically, remembered after restart): theme, text size, reduce motion, default crop, due-reminders on Home, photo technical details, auto-open results, save-chats toggle; AI engine status; data export (JSON) and safe deletion; install-as-app instructions. The non-functional *Language* and *Units* options were removed.
- **Rebuilt Analyze flow:** instant photo previews with quality feedback, "analyze anyway" for poor photos, camera toggle, plant linking, and no more empty/fake analyses.
- **Results & History:** structured results (what to do / why / sources / full report), downloadable report, saved-assessment viewer with delete, CSV export and a corrected compare view.
- **Plants:** health timelines, working reminders (mark done / delete, overdue highlighting), delete with confirmation, one-click *Analyze this plant*.
- **Assistant:** quick questions, an offline assistant that uses your assessment and the knowledge base, both sides of the chat saved.
- **Learn:** disease library built from the knowledge base, photo tips and glossary.
- **Mobile-friendly** scrollable navigation, persistent page on refresh, scroll-to-top on page change.

See `FIXES.md` for the full list of bugs fixed.

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      Streamlit UI    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Input Agent       │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │  Vision Agent   │        │ Symptom Agent   │
        └────────┬────────┘        └────────┬────────┘
                 └─────────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │   Evidence Fusion    │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │   RAG Knowledge      │
                    │      Agent           │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Risk / Severity      │
                    │ Agent                │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ IPM / Treatment      │
                    │ Agent                │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Safety Verification  │
                    └──────────┬───────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Report Agent / LLM   │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
        ┌─────────────────┐       ┌─────────────────┐
        │ Short-Term      │       │ SQLite Database │
        │ Memory          │       │                 │
        └─────────────────┘       └─────────────────┘
```

---

## 📁 Recommended Folder Structure

```text
crop-health-analyzer/
│
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment variables template
│
├── .streamlit/
│   └── config.toml             # Streamlit theme & UI settings
│
├── src/
│   ├── config.py               # App configuration & supported crops
│   ├── database/               # SQLite connection, models, repository
│   │   ├── db.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── agents/                 # Multi-agent components
│   │   ├── input_agent.py
│   │   ├── vision_agent.py
│   │   ├── symptom_agent.py
│   │   ├── knowledge_agent.py
│   │   ├── risk_agent.py
│   │   ├── treatment_agent.py
│   │   ├── safety_agent.py
│   │   └── report_agent.py
│   ├── workflow/               # State & Orchestration pipeline
│   │   ├── state.py
│   │   └── pipeline.py
│   ├── vision/                 # Image preprocessing & predictor
│   │   ├── preprocessing.py
│   │   ├── model.py
│   │   └── predictor.py
│   ├── rag/                    # Loader, chunker, embeddings, vector store
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── llm/                    # LLM client & grounded fallback
│   │   └── client.py
│   ├── memory/                 # Active session short-term memory
│   │   └── short_term.py
│   ├── safety/                 # Safety verification & disclaimers
│   │   └── verifier.py
│   ├── reports/                # Report generation templates
│   │   └── generator.py
│   └── utils/                  # Image, validation, formatting utils
│       ├── image_utils.py
│       ├── validation.py
│       └── formatting.py
│
├── data/
│   ├── knowledge/              # Grounded disease & IPM JSON records
│   └── crops/                  # Supported crops metadata
│
├── database/
│   └── crop_doctor.db          # Persistent SQLite database
│
└── tests/                      # Automated test suite
    ├── test_validation.py
    ├── test_database.py
    ├── test_rag.py
    ├── test_agents.py
    ├── test_workflow.py
    ├── test_settings_and_repository.py
    ├── test_regressions.py
    └── test_ui_apptest.py
```

---

## ⚡ Quick Start & Installation

### 1. Clone & Setup Environment
```bash
# Create Virtual Environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

> **AI model:** the default hosted model is `gemini-flash-latest` (Google retired `gemini-1.5-flash`). Without an API key the app uses its built-in knowledge-grounded assistant. Tested with Streamlit 1.64.

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```

The web UI will open automatically in your default browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Tests use a throw-away database and never call a real LLM. Either runner works:
```bash
python -m unittest discover -s tests      # or:  pytest
```
The suite covers the agents, RAG, database, settings persistence, regression tests for the bugs listed in `FIXES.md`, and Streamlit `AppTest` UI flows.

---

## ☁️ Streamlit Community Cloud Deployment Guide

1. Push your repository to GitHub.
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **New App**, choose your repository and branch.
4. Set Main file path to: `app.py`.
5. Add any optional secrets (e.g. `LLM_API_KEY`, `LLM_MODEL`) under **Advanced Settings** -> **Secrets**.
6. Click **Deploy**!

---

## 📜 License & Disclaimers

This software is released under the MIT License. Agricultural recommendations are intended strictly for educational and decision-support purposes.
