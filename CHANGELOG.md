# Changelog

All notable changes to the **PromptLab_AlignCV** project are documented here.

## [2026-11-20] Milestone 2 — Production Prototype, Evaluation & Cloud Preparation
### Added
- **2-Step Final Prompt Chain (`prompts/final/P1.txt`, `P2.txt`):** Structured separation of concerns between objective ATS Rubric Scoring (`P1`) and anti-hallucination STAR bullet rewriting (`P2`).
- **Prompt Iteration History (`prompts/v1/`, `v2/`, `v3/`):** Full evolutionary progression from unstructured baseline to 40/30/20/10 rubric and dual-stage chained inference.
- **Test Results & Documentation (`test-results/`):** Added `test_results.csv` and comprehensive `test_summary.md` detailing the 12-case evaluation suite (83.3% pass rate, honest documentation of Hinglish and ultra-short input edge failure modes).
- **Security & Secrets Fallback:** Updated `code/app.py` with multi-tier API key resolution supporting Streamlit Cloud Secrets (`st.secrets["GEMINI_API_KEY"]`) and local environment variables (`os.getenv("GEMINI_API_KEY")`).
- **Path Resolution Hardening:** Configured `code/app.py` with dynamic `PROJECT_ROOT` resolution via `pathlib.Path` to eliminate working-directory dependency and ensure seamless local and cloud deployment.
- **Clean Git Protection:** Configured comprehensive `.gitignore` strictly excluding virtual environments, cache files, secrets, and local personal assignment screenshots.

### Changed
- Refactored `code/app.py` JSON parser to safely strip markdown code fences prior to deserialization and handle error payloads gracefully.
- Expanded `README.md` with comprehensive architectural diagrams, installation guides, execution modes, security details, and testing summaries.

---

## [2026-10-09] Milestone 1 — Problem Identification & Baseline
### Added
- Selected Problem C9 (Resume Feedback against a Job Description) from SCSE4041 Appendix A.
- Formulated stakeholder requirements, user personas, and initial baseline 0-shot prompt (`v1/baseline.txt`).
- Defined initial project scope and repository layout.
