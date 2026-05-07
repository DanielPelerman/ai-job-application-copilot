import csv
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from parsers.job_url_parser import JobURLParser
from parsers.resume_parser import ResumeParser
from agents.resume_tailor import ResumeTailor
from agents.profile_matcher import ProfileMatcher
from utils.profile_store import load_profile, save_profile, clear_profile, calculate_completeness, restore_default_profile

TRACKER_FILE = Path("data/applications_tracker.csv")
TRACKER_FIELDS = [
    "company",
    "role_title",
    "location",
    "job_url",
    "job_description",
    "detected_keywords",
    "match_score",
    "matching_skills",
    "missing_skills",
    "relevant_projects",
    "strongest_fits",
    "application_status",
    "saved_at",
]

st.set_page_config(page_title="AI Job Application Copilot", page_icon="💼")

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
    st.session_state.resume_filename = ""
    st.session_state.resume_docx_bytes = None
if "job_details" not in st.session_state:
    st.session_state.job_details = {}
if "tracker_rows" not in st.session_state:
    st.session_state.tracker_rows = []
if "manual_description" not in st.session_state:
    st.session_state.manual_description = ""
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()


def load_application_tracker():
    if not TRACKER_FILE.exists():
        return []
    with TRACKER_FILE.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def save_application_tracker(application_data: dict):
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not TRACKER_FILE.exists()
    with TRACKER_FILE.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=TRACKER_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(application_data)


def extract_role_title(job_description: str, job_url: str) -> str:
    lines = [line.strip() for line in job_description.splitlines() if line.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line) < 120:
            return first_line
    path_parts = [part for part in urlparse(job_url).path.split("/") if part]
    if path_parts:
        return path_parts[-1].replace("-", " ").replace("_", " ").title()
    return "Unknown Role"


def extract_location(job_description: str) -> str:
    patterns = [r"Location:\s*(.+)", r"Based in\s*(.+)", r"(Remote|Hybrid)"]
    for pattern in patterns:
        match = re.search(pattern, job_description, re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.groups() else match.group(0).strip()
    return "Not specified"


def parse_job_details(scrape_result: dict, fallback_description: str = "") -> dict:
    description_text = scrape_result.get("description_text", "")
    source = scrape_result.get("source", "static scraper")
    if scrape_result.get("scrape_status") != "success" and fallback_description.strip():
        description_text = fallback_description.strip()
        source = "manual fallback"

    title = scrape_result.get("title") or extract_role_title(description_text, scrape_result.get("url", ""))
    company = scrape_result.get("company") or "Unknown"
    location = scrape_result.get("location") or extract_location(description_text)
    extracted_keywords = scrape_result.get("extracted_keywords", "")
    word_count = len(description_text.split()) if description_text else 0

    analysis = {}
    if description_text:
        from agents.job_analyzer import JobAnalyzer

        analyzer = JobAnalyzer()
        analysis = analyzer.analyze(description_text)
        if not extracted_keywords:
            extracted_keywords = ", ".join(
                list(dict.fromkeys(
                    analysis.get("role_keywords", [])
                    + analysis.get("required_skills", [])
                    + analysis.get("preferred_skills", [])
                ))
            )

    confident_fields = []
    if scrape_result.get("title"):
        confident_fields.append("title")
    if scrape_result.get("company"):
        confident_fields.append("company")
    if scrape_result.get("location") and scrape_result.get("location") != "Not specified":
        confident_fields.append("location")
    if word_count >= 80:
        confident_fields.append("description")

    # Profile matching
    profile_match = {}
    if description_text:
        matcher = ProfileMatcher()
        profile_match = matcher.match_job({
            "job_description": description_text,
            "role_title": title,
            "company": company
        })

    return {
        "company": company,
        "role_title": title,
        "location": location,
        "job_url": scrape_result.get("url", ""),
        "job_description": description_text,
        "detected_keywords": extracted_keywords,
        "scrape_status": scrape_result.get("scrape_status", "failed"),
        "source": source,
        "error_message": scrape_result.get("error_message", ""),
        "application_status": "Not started",
        "analysis": analysis,
        "word_count": word_count,
        "confident_fields": confident_fields,
        "profile_match": profile_match,
    }


def format_tracker_row(details: dict) -> dict:
    profile_match = details.get("profile_match", {})
    return {
        "company": details.get("company", ""),
        "role_title": details.get("role_title", ""),
        "location": details.get("location", ""),
        "job_url": details.get("job_url", ""),
        "job_description": details.get("job_description", ""),
        "detected_keywords": details.get("detected_keywords", ""),
        "match_score": profile_match.get("match_score", 0),
        "matching_skills": ", ".join(profile_match.get("matching_skills", [])),
        "missing_skills": ", ".join(profile_match.get("missing_skills", [])),
        "relevant_projects": "; ".join(profile_match.get("relevant_projects", [])),
        "strongest_fits": ", ".join(profile_match.get("strongest_fit_areas", [])),
        "application_status": details.get("application_status", "Saved"),
        "saved_at": datetime.utcnow().isoformat(),
    }


st.title("AI Job Application Copilot")
st.markdown(
    "Some job sites load descriptions dynamically. Phase 2 will use Playwright browser automation to scan those pages more accurately."
)

# Main tabs
tab_job_app, tab_master_profile = st.tabs(["Job Application", "Master Profile"])

with st.sidebar:
    with st.expander("Upload your resume for later tailoring"):
        resume_file = st.file_uploader("Upload your resume (DOCX only)", type=["docx"])
        if resume_file is not None:
            resume_bytes = resume_file.read()
            if resume_file.name != st.session_state.resume_filename or resume_bytes != st.session_state.resume_docx_bytes:
                parser = ResumeParser()
                st.session_state.resume_text = parser.parse(resume_bytes, resume_file.name)
                st.session_state.resume_filename = resume_file.name
                st.session_state.resume_docx_bytes = resume_bytes

        if st.session_state.resume_text:
            st.markdown("**Parsed resume preview**")
            st.write(st.session_state.resume_text[:800] + ("..." if len(st.session_state.resume_text) > 800 else ""))

with tab_job_app:
    st.subheader("Job / Application URL")
    job_url = st.text_input("Job/Application URL", value=st.session_state.job_details.get("job_url", ""))

    with st.expander("Manual fallback if URL scan fails"):
        st.session_state.manual_description = st.text_area(
            "Paste the job description here",
            value=st.session_state.manual_description,
            height=230,
        )

    col1, col2 = st.columns(2)
    with col1:
        scan_job = st.button("Scan Job URL")
    with col2:
        save_application = st.button("Save Application")

    if scan_job:
        if not job_url.strip():
            st.warning("Please enter a job or application URL before scanning.")
        else:
            parser = JobURLParser()
            scrape_result = parser.scrape(job_url)
            st.session_state.job_details = parse_job_details(scrape_result, st.session_state.manual_description)

            if scrape_result.get("scrape_status") == "success":
                st.success("Job details scraped and stored.")
            elif scrape_result.get("scrape_status") == "partial":
                st.warning("Partial extraction completed. This page may require browser automation for a fuller scan.")
                if scrape_result.get("error_message"):
                    st.info(scrape_result.get("error_message"))
            else:
                st.warning("Job URL scraping failed. Use the manual fallback below if needed.")
                st.error(scrape_result.get("error_message", "Unknown error."))

    if save_application:
        if not st.session_state.job_details.get("job_url"):
            st.warning("Please scan a job URL before saving the application.")
        else:
            tracker_row = format_tracker_row(st.session_state.job_details)
            save_application_tracker(tracker_row)
            st.session_state.tracker_rows = load_application_tracker()
            st.success("Application saved to tracker CSV.")

    if not st.session_state.tracker_rows:
        st.session_state.tracker_rows = load_application_tracker()

    if st.session_state.job_details:
        st.subheader("Job Details")
        details = st.session_state.job_details
        st.markdown(f"**Company:** {details.get('company', '')}")
        st.markdown(f"**Role title:** {details.get('role_title', '')}")
        st.markdown(f"**Location:** {details.get('location', '')}")
        st.markdown(f"**Job URL:** {details.get('job_url', '')}")
        st.markdown(f"**Extraction source:** {details.get('source', '')}")
        st.markdown(f"**Extraction quality:** {details.get('scrape_status', '')}")
        st.markdown(f"**Word count:** {details.get('word_count', 0)}")
        confidently = details.get('confident_fields', [])
        st.markdown(f"**Confidently extracted:** {', '.join(confidently) if confidently else 'None'}")
        st.markdown(f"**Detected keywords:** {details.get('detected_keywords', '')}")
        if details.get("scrape_status") != "success":
            st.markdown(f"**Scrape error:** {details.get('error_message', '')}")
        if details.get("scrape_status") == "partial":
            st.warning("This site may require browser automation for a more complete scan.")
        st.markdown(f"**Application status:** {details.get('application_status', 'Not started')}")

        st.markdown("---")
        st.markdown("**Job description preview**")
        st.write(details.get("job_description", "")[:1200] + ("..." if len(details.get("job_description", "")) > 1200 else ""))

        # Profile Match Analysis
        profile_match = details.get("profile_match", {})
        if profile_match:
            st.subheader("Profile Match Analysis")

            # Match Score
            match_score = profile_match.get("match_score", 0)
            st.markdown(f"**Overall Match Score: {match_score}%**")
            if match_score >= 80:
                st.success("Excellent match! Your profile strongly aligns with this role.")
            elif match_score >= 60:
                st.info("Good match with some areas to emphasize.")
            elif match_score >= 40:
                st.warning("Moderate match - consider highlighting transferable skills.")
            else:
                st.error("Limited match - focus on relevant experience and skills.")

            col1, col2 = st.columns(2)

            with col1:
                # Matching Skills
                matching_skills = profile_match.get("matching_skills", [])
                if matching_skills:
                    st.markdown("**✅ Matching Skills**")
                    for skill in matching_skills[:6]:
                        st.markdown(f"• {skill.title()}")
                    if len(matching_skills) > 6:
                        st.markdown(f"*...and {len(matching_skills) - 6} more*")
                else:
                    st.markdown("**✅ Matching Skills**")
                    st.write("No direct skill matches detected.")

                # Strongest Fit Areas
                strongest_fits = profile_match.get("strongest_fit_areas", [])
                if strongest_fits:
                    st.markdown("**💪 Strongest Fit Areas**")
                    for fit in strongest_fits:
                        st.markdown(f"• {fit}")

            with col2:
                # Missing Skills
                missing_skills = profile_match.get("missing_skills", [])
                if missing_skills:
                    st.markdown("**❌ Skills to Address**")
                    for skill in missing_skills[:4]:
                        st.markdown(f"• {skill.title()}")
                    if len(missing_skills) > 4:
                        st.markdown(f"*...and {len(missing_skills) - 4} more*")
                else:
                    st.markdown("**❌ Skills to Address**")
                    st.write("No major skill gaps detected.")

                # Role Relevance
                role_relevance = profile_match.get("role_relevance", {})
                if role_relevance.get("relevant"):
                    st.markdown("**🎯 Role Relevance**")
                    matched_roles = role_relevance.get("matched_roles", [])
                    if matched_roles:
                        st.markdown(f"Matches your target: {', '.join(matched_roles)}")
                    else:
                        st.markdown("Aligns with your career goals")
                else:
                    st.markdown("**🎯 Role Relevance**")
                    st.write("Consider if this aligns with your target roles")

            # Relevant Projects
            relevant_projects = profile_match.get("relevant_projects", [])
            if relevant_projects:
                st.markdown("**🚀 Relevant Projects to Highlight**")
                for project in relevant_projects:
                    st.markdown(f"• {project}")

            # Relevant Resume Bullets
            relevant_bullets = profile_match.get("relevant_bullets", [])
            if relevant_bullets:
                st.markdown("**📋 Key Resume Bullets to Use**")
                for bullet in relevant_bullets[:3]:
                    st.markdown(f"• {bullet}")

            # Recommendations
            recommendations = profile_match.get("recommendations", [])
            if recommendations:
                st.markdown("**💡 Application Recommendations**")
                for rec in recommendations:
                    st.markdown(f"• {rec}")

            # Recruiter Keywords
            recruiter_keywords = profile_match.get("recruiter_keywords", [])
            if recruiter_keywords:
                st.markdown("**🔍 Likely Recruiter Keywords**")
                st.write(", ".join(recruiter_keywords))

            st.markdown("---")

        st.subheader("Application Prep")
        analysis = details.get("analysis", {})
        st.markdown("**Key job requirements**")
        if analysis.get("requirements"):
            for requirement in analysis.get("requirements", [])[:8]:
                st.markdown(f"- {requirement}")
        elif analysis.get("responsibilities"):
            for requirement in analysis.get("responsibilities", [])[:6]:
                st.markdown(f"- {requirement}")
        else:
            st.write("No key requirements detected yet.")

        st.markdown("**Resume tailoring suggestions**")
        tailor = ResumeTailor()
        suggestions = tailor.suggest(st.session_state.resume_text, details.get("job_description", ""))
        for suggestion in suggestions.get("suggestions", []):
            st.markdown(f"- {suggestion}")

        st.markdown("**Fields to review later**")
        if suggestions.get("fields_review"):
            for field in suggestions.get("fields_review", []):
                st.markdown(f"- {field}")
        else:
            st.write("No review fields identified yet.")

        st.markdown("---")
        st.subheader("Tailored Resume Generation")
        if not st.session_state.resume_docx_bytes:
            st.info("Upload your resume as a DOCX file in the sidebar to enable tailored resume generation.")
        else:
            if st.button("Generate Tailored Resume", key="generate_tailored_resume_btn"):
                tailored_result = tailor.generate_tailored_resume(
                    resume_docx_bytes=st.session_state.resume_docx_bytes,
                    resume_text=st.session_state.resume_text,
                    job_description=details.get("job_description", ""),
                    profile=st.session_state.profile,
                    company=details.get("company", "Company"),
                    role_title=details.get("role_title", "Role"),
                    original_filename=st.session_state.resume_filename,
                )
                st.session_state.tailored_resume = tailored_result
                st.success("Tailored resume generated and saved to exports/tailored_resumes.")

        if st.session_state.get("tailored_resume"):
            tr = st.session_state.tailored_resume
            st.subheader("Tailoring Summary")
            st.markdown(f"**Resume Match Score:** {tr.get('match_score', 0)}%")

            matched_keywords = tr.get("matched_keywords", [])
            if matched_keywords:
                st.markdown("**Matched Keywords**")
                st.write(", ".join(matched_keywords))

            emphasized_projects = tr.get("emphasized_projects", [])
            if emphasized_projects:
                st.markdown("**Emphasized Projects**")
                for project in emphasized_projects:
                    st.markdown(f"- {project}")

            recommended_edits = tr.get("recommended_edits", [])
            if recommended_edits:
                st.markdown("**Recommended Edits**")
                for edit in recommended_edits:
                    st.markdown(f"- {edit}")

            missing_qualifications = tr.get("missing_qualifications", [])
            if missing_qualifications:
                st.markdown("**Missing Qualifications**")
                for missing in missing_qualifications[:8]:
                    st.markdown(f"- {missing}")
                if len(missing_qualifications) > 8:
                    st.markdown(f"*...and {len(missing_qualifications) - 8} more*")

            st.markdown("---")
            st.markdown("**Download tailored resume**")
            download_col1, download_col2 = st.columns(2)

            if tr.get("docx_bytes"):
                download_col1.download_button(
                    label="Download DOCX",
                    data=tr["docx_bytes"],
                    file_name=tr["docx_filename"],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                download_col1.warning("DOCX export is unavailable. Ensure python-docx is installed and the uploaded file is valid.")

            if tr.get("pdf_bytes"):
                download_col2.download_button(
                    label="Download PDF",
                    data=tr["pdf_bytes"],
                    file_name=tr["pdf_filename"],
                    mime="application/pdf",
                )
            else:
                download_col2.warning("PDF export is unavailable. Install docx2pdf and ensure it is supported on your system.")

            st.markdown(f"**Saved path:** `{tr.get('directory', '')}`")

    st.subheader("Application Tracker")
    if st.session_state.tracker_rows:
        st.dataframe(st.session_state.tracker_rows)
    else:
        st.write("No saved applications yet.")

with tab_master_profile:
    st.header("Master Profile")
    st.markdown(
        "Edit your profile information below and click **Save Profile** to persist changes. Your profile is stored in `data/profile.json`."
    )
    
    # Debug info showing profile source
    st.caption("✓ Profile loaded from: `data/profile.json`")

    profile = st.session_state.profile

    st.subheader("Contact Information")
    col1, col2 = st.columns(2)
    with col1:
        profile["contact_info"]["full_name"] = st.text_input(
            "Full Name", value=profile.get("contact_info", {}).get("full_name", "")
        )
        profile["contact_info"]["email"] = st.text_input(
            "Email", value=profile.get("contact_info", {}).get("email", "")
        )
    with col2:
        profile["contact_info"]["phone"] = st.text_input(
            "Phone", value=profile.get("contact_info", {}).get("phone", "")
        )
        profile["contact_info"]["linkedin"] = st.text_input(
            "LinkedIn URL", value=profile.get("contact_info", {}).get("linkedin", "")
        )

    st.subheader("Links / Portfolio")
    profile["links_portfolio"]["github_url"] = st.text_input(
        "GitHub URL",
        value=profile.get("links_portfolio", {}).get("github_url", ""),
    )
    profile["links_portfolio"]["multi_asset_portfolio_url"] = st.text_input(
        "Multi-Asset Portfolio Analytics Website URL",
        value=profile.get("links_portfolio", {}).get("multi_asset_portfolio_url", ""),
    )

    st.subheader("Education")
    st.markdown("**Bachelor’s Degree**")
    bat_col1, bat_col2 = st.columns(2)
    with bat_col1:
        profile["education"]["bachelors"]["degree"] = st.text_input(
            "Bachelor’s Degree",
            value=profile.get("education", {}).get("bachelors", {}).get("degree", ""),
        )
        profile["education"]["bachelors"]["field_of_study"] = st.text_input(
            "Bachelor’s Field of Study",
            value=profile.get("education", {}).get("bachelors", {}).get("field_of_study", ""),
        )
    with bat_col2:
        profile["education"]["bachelors"]["university"] = st.text_input(
            "Bachelor’s University",
            value=profile.get("education", {}).get("bachelors", {}).get("university", ""),
        )
        profile["education"]["bachelors"]["graduation_year"] = st.text_input(
            "Bachelor’s Graduation Year",
            value=profile.get("education", {}).get("bachelors", {}).get("graduation_year", ""),
        )

    st.markdown("**Master’s Degree**")
    mag_col1, mag_col2 = st.columns(2)
    with mag_col1:
        profile["education"]["masters"]["degree"] = st.text_input(
            "Master’s Degree",
            value=profile.get("education", {}).get("masters", {}).get("degree", ""),
        )
        profile["education"]["masters"]["field_of_study"] = st.text_input(
            "Master’s Field of Study",
            value=profile.get("education", {}).get("masters", {}).get("field_of_study", ""),
        )
    with mag_col2:
        profile["education"]["masters"]["university"] = st.text_input(
            "Master’s University",
            value=profile.get("education", {}).get("masters", {}).get("university", ""),
        )
        profile["education"]["masters"]["graduation_year"] = st.text_input(
            "Master’s Graduation Year",
            value=profile.get("education", {}).get("masters", {}).get("graduation_year", ""),
        )

    st.subheader("Career Preferences")
    col1, col2 = st.columns(2)
    with col1:
        profile["target_roles"] = st.text_input(
            "Target Roles (comma-separated, e.g., 'Data Analyst, Business Analyst')",
            value=profile.get("target_roles", ""),
        )
    with col2:
        profile["target_locations"] = st.text_input(
            "Target Locations (comma-separated, e.g., 'Los Angeles, Newport Beach')",
            value=profile.get("target_locations", ""),
        )

    profile["work_authorization"] = st.text_input(
        "Work Authorization Status (e.g., 'US Citizen')",
        value=profile.get("work_authorization", ""),
    )
    profile["salary_expectations"] = st.text_input(
        "Salary Expectations (e.g., '$80K - $120K')",
        value=profile.get("salary_expectations", ""),
    )

    st.subheader("Skills & Expertise")
    profile["technical_skills"] = st.text_area(
        "Technical Skills (comma-separated, e.g., 'Python, SQL, Excel, Tableau')",
        value=profile.get("technical_skills", ""),
        height=100,
    )

    profile["finance_analytics_skills"] = st.text_area(
        "Finance & Analytics Skills (comma-separated, e.g., 'Financial Modeling, Budgeting, Data Analysis')",
        value=profile.get("finance_analytics_skills", ""),
        height=100,
    )

    profile["tools_platforms"] = st.text_area(
        "Tools & Platforms (comma-separated, e.g., 'Excel, SQL, Tableau, Python')",
        value=profile.get("tools_platforms", ""),
        height=80,
    )

    st.subheader("Background & Experience")
    profile["work_experience"] = st.text_area(
        "Work Experience Summary (roles, companies, years, key achievements)",
        value=profile.get("work_experience", ""),
        height=150,
    )

    profile["projects"] = st.text_area(
        "Notable Projects (describe key projects you've led or contributed to)",
        value=profile.get("projects", ""),
        height=150,
    )

    profile["resume_bullets"] = st.text_area(
        "Key Resume Bullets (your strongest professional highlights)",
        value=profile.get("resume_bullets", ""),
        height=150,
    )

    st.subheader("Reusable Application Answers")
    st.markdown(
        "_Pre-write answers to common application questions. These will help you tailor responses quickly._"
    )

    profile["reusable_application_answers"]["why_this_company"] = st.text_area(
        "Why are you interested in this company?",
        value=profile.get("reusable_application_answers", {}).get("why_this_company", ""),
        height=100,
    )

    profile["reusable_application_answers"]["why_this_role"] = st.text_area(
        "Why are you interested in this role?",
        value=profile.get("reusable_application_answers", {}).get("why_this_role", ""),
        height=100,
    )

    profile["reusable_application_answers"]["biggest_achievement"] = st.text_area(
        "What's your biggest professional achievement?",
        value=profile.get("reusable_application_answers", {}).get("biggest_achievement", ""),
        height=100,
    )

    profile["reusable_application_answers"]["challenge_overcome"] = st.text_area(
        "Tell us about a challenge you overcame.",
        value=profile.get("reusable_application_answers", {}).get("challenge_overcome", ""),
        height=100,
    )

    profile["reusable_application_answers"]["team_collaboration"] = st.text_area(
        "Describe your experience working in teams.",
        value=profile.get("reusable_application_answers", {}).get("team_collaboration", ""),
        height=100,
    )

    profile["reusable_application_answers"]["leadership_experience"] = st.text_area(
        "Describe any leadership experience.",
        value=profile.get("reusable_application_answers", {}).get("leadership_experience", ""),
        height=100,
    )

    st.markdown("---")
    st.subheader("Profile Actions")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💾 Save Profile", key="save_profile_btn"):
            st.session_state.profile = profile
            if save_profile(profile):
                st.success("Profile saved successfully!")
                st.session_state.profile_saved = True
            else:
                st.error("Failed to save profile.")

    with col2:
        if st.button("🔄 Load Profile", key="load_profile_btn"):
            st.session_state.profile = load_profile()
            st.success("Profile loaded from disk.")
            st.rerun()

    with col3:
        if st.button("↺ Restore Default", key="restore_profile_btn"):
            st.session_state.profile = restore_default_profile()
            st.success("Profile restored to defaults.")
            st.rerun()

    with col4:
        if st.button("🗑️ Clear Profile", key="clear_profile_btn"):
            if st.session_state.get("confirm_clear_profile"):
                st.session_state.profile = clear_profile()
                st.session_state.confirm_clear_profile = False
                st.success("Profile cleared.")
                st.rerun()
            else:
                st.session_state.confirm_clear_profile = True
                st.warning("Click again to confirm clearing the profile.")

    st.markdown("---")
    st.subheader("Profile Completeness")

    completeness = calculate_completeness(st.session_state.profile)
    pct = completeness["percentage"]
    filled = completeness["filled_fields"]
    total = completeness["total_fields"]

    st.progress(pct / 100)
    st.markdown(f"**Completeness: {pct}% ({filled}/{total} fields filled)**")

    if completeness["missing_fields"] and len(completeness["missing_fields"]) <= 10:
        st.markdown("**Missing or incomplete fields:**")
        for field in completeness["missing_fields"]:
            st.markdown(f"- {field}")
    elif completeness["missing_fields"]:
        st.markdown(f"**{len(completeness['missing_fields'])} fields are missing or incomplete. Edit above to complete your profile.**")
