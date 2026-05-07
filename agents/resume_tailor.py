class ResumeTailor:
    """Simple rule-based resume tailoring suggestion generator."""

    SKILL_KEYWORDS = [
        "python",
        "sql",
        "excel",
        "analytics",
        "data analysis",
        "project management",
        "communication",
        "leadership",
        "reporting",
        "financial modeling",
        "forecasting",
        "presentation",
        "stakeholder",
    ]

    def suggest(self, resume_text: str, job_description: str) -> dict:
        suggestions = []
        fields_review = []
        lower_resume = resume_text.lower() if resume_text else ""
        lower_job = job_description.lower() if job_description else ""

        if not resume_text:
            suggestions.append("Upload a resume to get focused tailoring suggestions.")
            fields_review.append("Resume content")

        for skill in self.SKILL_KEYWORDS:
            if skill in lower_job and skill not in lower_resume:
                suggestions.append(f"Consider adding experience with {skill} to your resume.")

        if "project" in lower_job and "project" not in lower_resume:
            suggestions.append("Include specific project examples that illustrate your experience.")

        if "lead" in lower_job and "lead" not in lower_resume:
            suggestions.append("Highlight leadership or collaboration experiences where relevant.")

        if not lower_job:
            fields_review.append("Job description details")

        if not suggestions:
            suggestions.append(
                "Your resume appears to cover many job keywords; review for clarity, metrics, and business impact."
            )

        if "location" not in lower_job and "remote" not in lower_job:
            fields_review.append("Location or work arrangement")

        if "company" not in lower_job:
            fields_review.append("Company-specific context")

        return {
            "suggestions": suggestions,
            "fields_review": list(dict.fromkeys(fields_review)),
        }
