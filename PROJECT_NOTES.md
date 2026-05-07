# Project Notes

## Current Goal
Build a comprehensive AI-driven job application copilot that scans job URLs, matches against user profile, and tracks applications.

## Current Phase
Phase 1: Core profile management, job scanning, and profile-to-job matching with source-of-truth architecture.

## Architecture Principles
- **Single Source of Truth**: `data/profile.json` is the only source for user profile data.
- **No Fake Data**: Profile system never displays or loads hardcoded fake example data.
- **Fallback Template**: `FALLBACK_DEFAULT` in `profile_store.py` contains only generic placeholders (e.g., "[Your Name]"), never specific professional examples.
- **Auto-Loading**: Profile automatically loads from `data/profile.json` on every app start.
- **Transparent**: Debug line on Master Profile page shows profile source.

## Completed Setup
- Updated `app.py` to use `Scan Job URL` as the main workflow and remove sidebar profile fields.
- Added optional resume upload in a collapsed expander for later tailoring.
- Added improved `parsers/job_url_parser.py` with better extraction heuristics, junk text filtering, and section detection for job postings.
- Added scraping quality states: `success`, `partial`, and `failed`.
- Updated `app.py` to surface extraction source, extraction quality, extracted word count, and confidently extracted fields.
- Integrated Playwright browser-rendered scanning fallback for dynamic job sites in `parsers/job_url_parser.py`.
- Continued to save scraped job details into `data/applications_tracker.csv`.
- **Added Profile Match Engine** with `agents/profile_matcher.py` that compares scanned jobs against saved master profile.
  - Matches job requirements against: technical_skills, finance_analytics_skills, tools_platforms, projects, resume_bullets, target_roles.
  - Generates: matching/missing skills, relevant projects, resume bullets, leadership relevance, overall match score (0-100).
  - **Profile Match Analysis section** added to app after job scanning with:
    - Match score with color-coded feedback (excellent/good/moderate/limited)
    - Matching skills, missing skills, strongest fit areas
    - Role relevance, relevant projects to highlight, key resume bullets
    - Application recommendations and likely recruiter keywords
  - Match results saved to application tracker CSV (match_score, matching_skills, missing_skills, relevant_projects, strongest_fits).
- **Fixed Master Profile Source-of-Truth Issue**:
  - Clarified that `data/profile.json` is the only source of truth for user profile.
  - Removed misleading message claiming "pre-populated with placeholder values".
  - Added debug line showing profile is loaded from `data/profile.json`.
  - Verified `FALLBACK_DEFAULT` contains only generic placeholders, never fake professional content.
  - Updated placeholder examples in UI (e.g., "Excel, SQL, Tableau" instead of "Salesforce, SAP, Jira").
  - Profile auto-loads on every app start from persistent storage.
- **Revised Master Profile schema**:
  - Contact information now includes only full name, email, phone, and LinkedIn URL.
  - Added a new Links / Portfolio section for GitHub URL and Multi-Asset Portfolio Analytics Website URL.
  - Updated education to support both bachelor’s and master’s degrees, removing the certifications field.
  - Career preferences now use US Citizen authorization and target locations only include Los Angeles and Newport Beach.
  - Profile loading and saving updated to support the new nested profile structure.
- **Added Resume Tailoring Engine**:
  - Generates a tailored resume based on uploaded resume text, scanned job description, and saved master profile.
  - Builds a summary of matched keywords, emphasized projects, recommended edits, and missing qualifications.
  - Saves tailored resume exports to `exports/tailored_resumes/` with `company_role_date_tailored_resume` naming.
- Provides export buttons for DOCX and optional PDF via `docx2pdf`.
- Preserves the original resume DOCX layout and formatting while emphasizing existing matched keywords.
- Keeps analysis and tailoring notes in the app UI only, not inside the resume file.


## Next Steps
- Enhance job site scraping coverage for larger enterprise and ATS-driven pages.
- Add browser automation scaffolding in Phase 2 for sites that require dynamic content rendering.
- Implement resume matching, tailored resume generation, and application workflow state updates.
- Extend tracker fields and CSV export features.
