import json
from pathlib import Path

PROFILE_FILE = Path("data/profile.json")

FALLBACK_DEFAULT = {
    "contact_info": {
        "full_name": "[Your Name]",
        "email": "[your.email@example.com]",
        "phone": "[Your Phone Number]",
        "linkedin": "",
    },
    "links_portfolio": {
        "github_url": "",
        "multi_asset_portfolio_url": "",
    },
    "education": {
        "bachelors": {
            "degree": "",
            "field_of_study": "",
            "university": "",
            "graduation_year": "",
        },
        "masters": {
            "degree": "",
            "field_of_study": "",
            "university": "",
            "graduation_year": "",
        },
    },
    "target_roles": "",
    "target_locations": "",
    "work_authorization": "",
    "salary_expectations": "",
    "technical_skills": "",
    "finance_analytics_skills": "",
    "tools_platforms": "",
    "projects": "",
    "work_experience": "",
    "resume_bullets": "",
    "reusable_application_answers": {
        "why_this_company": "",
        "why_this_role": "",
        "biggest_achievement": "",
        "challenge_overcome": "",
        "team_collaboration": "",
        "leadership_experience": "",
    },
}


def _merge_profile_defaults(profile: dict, default: dict) -> dict:
    for key, value in default.items():
        if key not in profile:
            profile[key] = json.loads(json.dumps(value))
        elif isinstance(value, dict) and isinstance(profile.get(key), dict):
            profile[key] = _merge_profile_defaults(profile[key], value)
    return profile


def _ensure_profile_file_exists():
    """Ensure profile.json exists. If not, create a minimal blank profile."""
    if not PROFILE_FILE.exists():
        PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with PROFILE_FILE.open("w", encoding="utf-8") as f:
                json.dump(FALLBACK_DEFAULT, f, indent=2, ensure_ascii=False)
        except IOError:
            pass


def load_profile() -> dict:
    """Load profile from profile.json. Creates file if it doesn't exist."""
    _ensure_profile_file_exists()

    if not PROFILE_FILE.exists():
        return json.loads(json.dumps(FALLBACK_DEFAULT))

    try:
        with PROFILE_FILE.open("r", encoding="utf-8") as f:
            profile = json.load(f)
            profile = _merge_profile_defaults(profile, FALLBACK_DEFAULT)
            return profile
    except (json.JSONDecodeError, IOError):
        return json.loads(json.dumps(FALLBACK_DEFAULT))


def save_profile(profile: dict) -> bool:
    """Save profile to profile.json. Returns True on success, False on failure."""
    try:
        PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PROFILE_FILE.open("w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def get_default_profile() -> dict:
    """Load the default profile from profile.json."""
    _ensure_profile_file_exists()
    return load_profile()


def restore_default_profile() -> dict:
    """Restore the default profile and save it."""
    default_profile = get_default_profile()
    save_profile(default_profile)
    return default_profile


def clear_profile() -> dict:
    """Clear profile data and return default empty profile."""
    try:
        if PROFILE_FILE.exists():
            PROFILE_FILE.unlink()
    except IOError:
        pass
    return json.loads(json.dumps(FALLBACK_DEFAULT))


def calculate_completeness(profile: dict) -> dict:
    """Calculate profile completeness percentage and list missing fields."""
    total_fields = 0
    filled_fields = 0
    missing_fields = []

    contact_fields = ["full_name", "email", "phone", "linkedin"]
    for field in contact_fields:
        total_fields += 1
        value = profile.get("contact_info", {}).get(field, "")
        if value and str(value).strip():
            filled_fields += 1
        else:
            missing_fields.append(f"contact_info.{field}")

    links_fields = ["github_url", "multi_asset_portfolio_url"]
    for field in links_fields:
        total_fields += 1
        value = profile.get("links_portfolio", {}).get(field, "")
        if value and str(value).strip():
            filled_fields += 1
        else:
            missing_fields.append(f"links_portfolio.{field}")

    education_fields = [
        ("bachelors", "degree"),
        ("bachelors", "field_of_study"),
        ("bachelors", "university"),
        ("bachelors", "graduation_year"),
        ("masters", "degree"),
        ("masters", "field_of_study"),
        ("masters", "university"),
        ("masters", "graduation_year"),
    ]
    for section, field in education_fields:
        total_fields += 1
        value = profile.get("education", {}).get(section, {}).get(field, "")
        if value and str(value).strip():
            filled_fields += 1
        else:
            missing_fields.append(f"education.{section}.{field}")

    main_fields = [
        "target_roles",
        "target_locations",
        "work_authorization",
        "technical_skills",
        "finance_analytics_skills",
        "work_experience",
    ]
    for field in main_fields:
        total_fields += 1
        value = profile.get(field, "")
        if value and str(value).strip():
            filled_fields += 1
        else:
            missing_fields.append(field)

    answer_fields = [
        "why_this_company",
        "why_this_role",
        "biggest_achievement",
        "challenge_overcome",
    ]
    for field in answer_fields:
        total_fields += 1
        value = profile.get("reusable_application_answers", {}).get(field, "")
        if value and str(value).strip():
            filled_fields += 1
        else:
            missing_fields.append(f"reusable_application_answers.{field}")

    completeness_pct = int((filled_fields / total_fields * 100)) if total_fields > 0 else 0

    return {
        "percentage": completeness_pct,
        "filled_fields": filled_fields,
        "total_fields": total_fields,
        "missing_fields": missing_fields,
    }
