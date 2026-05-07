class ResumeMatcher:
    """Stub agent for matching resumes to job descriptions."""

    def match(self, resume_text: str, job_description: str) -> dict:
        return {
            "score": 0,
            "highlights": [],
            "recommendations": []
        }
