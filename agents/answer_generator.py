import re

class AnswerGenerator:
    """Simple rule-based answer generator for common application prompts."""

    SKILL_KEYWORDS = [
        "python", "sql", "excel", "product management", "analytics", "communication",
        "teamwork", "leadership", "data analysis", "project management", "reporting",
        "financial modeling", "forecasting", "presentation", "stakeholder"
    ]

    INTEREST_KEYWORDS = [
        "finance", "analytics", "data", "technology", "innovation", "growth", "strategy",
        "customer", "operations", "product"
    ]

    def generate(self, job_description: str) -> dict:
        text = job_description.strip()
        if not text:
            return {
                "why_interested": "I am excited by this opportunity and ready to contribute to a strong team.",
                "why_fit": "I bring relevant experience, a strong work ethic, and a willingness to learn.",
                "tell_us_about_yourself": "I am a motivated professional with a focus on delivering results and solving problems."
            }

        skills = self._extract_skills(text)
        interests = self._extract_focus(text)
        what_makes_fit = ", ".join(skills[:3]) if skills else "relevant skills and experience"
        interest_phrase = ", ".join(interests[:2]) if interests else "the goals described in this posting"

        return {
            "why_interested": (
                f"I am interested in this role because it aligns with my experience in {interest_phrase} "
                "and offers a chance to contribute to the business priorities described in the job posting."
            ),
            "why_fit": (
                f"I am a good fit because I have experience with {what_makes_fit}, "
                "I am comfortable working cross-functionally, and I am motivated to deliver strong outcomes."
            ),
            "tell_us_about_yourself": (
                "I am a driven professional who enjoys solving problems and working collaboratively. "
                "I focus on clear communication, execution, and continuous improvement, and I am eager to bring that mindset to this role."
            )
        }

    def _extract_skills(self, text: str) -> list:
        lower_text = text.lower()
        return [skill for skill in self.SKILL_KEYWORDS if skill in lower_text]

    def _extract_focus(self, text: str) -> list:
        lower_text = text.lower()
        return [keyword for keyword in self.INTEREST_KEYWORDS if keyword in lower_text]
