import re

class JobAnalyzer:
    """Simple rule-based job description analyzer."""

    ROLE_KEYWORDS = [
        "analyst", "engineer", "developer", "manager", "specialist", "consultant",
        "scientist", "coordinator", "director", "associate", "administrator", "architect",
        "advisor", "lead", "strategist", "intern", "internship", "vice president",
        "vp", "sr", "senior", "junior", "staff"
    ]

    SKILL_KEYWORDS = [
        "python", "sql", "excel", "power bi", "tableau", "data analysis", "machine learning",
        "project management", "communication", "financial modeling", "budgeting", "forecasting",
        "analytics", "reporting", "statistics", "presentation", "leadership", "stakeholder",
        "java", "javascript", "aws", "azure", "gcp", "crm", "salesforce", "scrum",
        "agile", "data visualization", "research", "modeling", "cloud", "product management"
    ]

    RESPONSIBILITY_WORDS = [
        "lead", "manage", "develop", "design", "analyze", "support", "coordinate",
        "implement", "drive", "deliver", "maintain", "improve", "present", "build",
        "execute", "own", "monitor", "partner"
    ]

    REQUIREMENT_MARKERS = [
        "required", "must have", "minimum", "essential", "qualification", "qualifications",
        "experience", "education", "preferred", "nice to have", "nice-to-have"
    ]

    FINANCE_ANALYTICS_KEYWORDS = [
        "finance", "financial", "analytics", "analysis", "budget", "forecast",
        "metric", "reporting", "cash", "investment", "valuation", "roi"
    ]

    def analyze(self, job_description: str) -> dict:
        text = job_description.strip()
        lower_text = text.lower()

        return {
            "role_keywords": self._extract_role_keywords(lower_text),
            "responsibilities": self._extract_responsibilities(text),
            "required_skills": self._extract_skills(lower_text, required=True),
            "preferred_skills": self._extract_skills(lower_text, required=False),
            "requirements": self._extract_requirements(text),
            "keywords": self._extract_keywords(lower_text),
            "finance_analytics_relevance": self._finance_analytics_relevance(lower_text),
        }

    def _extract_role_keywords(self, lower_text: str) -> list:
        matches = [keyword for keyword in self.ROLE_KEYWORDS if keyword in lower_text]
        if matches:
            return list(dict.fromkeys(matches))

        first_line = lower_text.splitlines()[0] if lower_text else ""
        return [first_line] if first_line else []

    def _extract_responsibilities(self, text: str) -> list:
        lines = re.split(r"[\r\n]+", text)
        responsibilities = []
        for line in lines:
            cleaned = line.strip(" •-\t")
            if len(cleaned) < 20:
                continue
            lower_line = cleaned.lower()
            if any(word in lower_line for word in self.RESPONSIBILITY_WORDS):
                responsibilities.append(cleaned)
            elif any(marker in lower_line for marker in ["responsible for", "will", "you will", "you are responsible"]):
                responsibilities.append(cleaned)
            if len(responsibilities) >= 10:
                break
        return responsibilities

    def _extract_skills(self, lower_text: str, required: bool = True) -> list:
        section = self._extract_section(lower_text, required)
        skills = [skill for skill in self.SKILL_KEYWORDS if skill in section]
        if skills:
            return list(dict.fromkeys(skills))

        if required:
            return [skill for skill in self.SKILL_KEYWORDS if skill in lower_text]
        return []

    def _extract_requirements(self, text: str) -> list:
        lines = re.split(r"[\r\n]+", text)
        requirements = []
        for line in lines:
            cleaned = line.strip(" •-\t")
            lower_line = cleaned.lower()
            if len(cleaned) < 15:
                continue
            if any(marker in lower_line for marker in self.REQUIREMENT_MARKERS):
                requirements.append(cleaned)
            if len(requirements) >= 12:
                break
        return requirements

    def _extract_section(self, lower_text: str, required: bool) -> str:
        if required:
            markers = ["required", "must have", "minimum", "essential", "qualification"]
        else:
            markers = ["preferred", "nice to have", "nice-to-have", "plus"]
        for marker in markers:
            if marker in lower_text:
                start = lower_text.index(marker)
                return lower_text[start:start + 1000]
        return ""

    def _extract_keywords(self, lower_text: str) -> list:
        keywords = [keyword for keyword in self.ROLE_KEYWORDS + self.SKILL_KEYWORDS if keyword in lower_text]
        return list(dict.fromkeys(keywords))

    def _finance_analytics_relevance(self, lower_text: str) -> bool:
        return any(keyword in lower_text for keyword in self.FINANCE_ANALYTICS_KEYWORDS)
