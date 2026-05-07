# Project Notes

## Current Goal
Pivot the Phase 1 AI Job Application Copilot toward URL scraping, job detail extraction, and application tracking.

## Current Phase
Phase 1: URL scraping and application tracker integration with resume support.

## Completed Setup
- Updated `app.py` to use `Scan Job URL` as the main workflow and remove sidebar profile fields.
- Added optional resume upload in a collapsed expander for later tailoring.
- Added improved `parsers/job_url_parser.py` with better extraction heuristics, junk text filtering, and section detection for job postings.
- Added scraping quality states: `success`, `partial`, and `failed`.
- Updated `app.py` to surface extraction source, extraction quality, extracted word count, and confidently extracted fields.
- Integrated Playwright browser-rendered scanning fallback for dynamic job sites in `parsers/job_url_parser.py`.
- Continued to save scraped job details into `data/applications_tracker.csv`.
- **Added Master Profile system** with `utils/profile_store.py` and new "Master Profile" tab in `app.py`.
  - Master Profile is **pre-populated with comprehensive defaults** in `data/profile.json` covering:
    - Contact info (with placeholders for private fields)
    - Education (degree, university, certifications)
    - Career preferences (target roles, locations, work authorization, salary)
    - Skills & expertise (technical, finance/analytics, tools/platforms)
    - Work experience, projects, and resume bullets
    - Reusable application answers (why company, why role, achievements, challenges, leadership)
  - Profile auto-loads on app startup from `data/profile.json`.
  - Profile persists edits to `data/profile.json` when "Save Profile" is clicked.
  - Buttons: **Save Profile**, **Load Profile**, **Restore Default** (reload template), **Clear Profile**.
  - Profile completeness checklist shows filled/missing fields percentage.

## Next Steps
- Enhance job site scraping coverage for larger enterprise and ATS-driven pages.
- Add browser automation scaffolding in Phase 2 for sites that require dynamic content rendering.
- Implement resume matching, tailored resume generation, and application workflow state updates.
- Extend tracker fields and CSV export features.
