import re
from typing import Dict, List, Tuple
from utils.profile_store import load_profile

class ProfileMatcher:
    """Matches job requirements against user profile to identify fit and gaps."""

    def __init__(self):
        self.profile = load_profile()

    def match_job(self, job_data: Dict) -> Dict:
        """
        Match job requirements against profile.

        Args:
            job_data: Dictionary containing job details from scanning

        Returns:
            Dictionary with match analysis results
        """
        job_description = job_data.get("job_description", "").lower()
        job_title = job_data.get("role_title", "").lower()

        # Extract skills from job description
        job_skills = self._extract_job_skills(job_description)

        # Match against profile sections
        technical_matches = self._match_skills(
            job_skills, self.profile.get("technical_skills", "").lower()
        )
        finance_matches = self._match_skills(
            job_skills, self.profile.get("finance_analytics_skills", "").lower()
        )
        tools_matches = self._match_skills(
            job_skills, self.profile.get("tools_platforms", "").lower()
        )

        # Combine all skill matches
        all_matching_skills = technical_matches + finance_matches + tools_matches
        all_matching_skills = list(dict.fromkeys(all_matching_skills))  # Remove duplicates

        # Find missing skills
        missing_skills = [skill for skill in job_skills if skill not in all_matching_skills]

        # Match projects and experience
        relevant_projects = self._find_relevant_projects(job_description)
        relevant_bullets = self._find_relevant_bullets(job_description)

        # Check role relevance
        role_relevance = self._check_role_relevance(job_title)

        # Calculate overall match score
        match_score = self._calculate_match_score(
            all_matching_skills, missing_skills, role_relevance, job_skills
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            all_matching_skills, missing_skills, relevant_projects, relevant_bullets
        )

        # Extract likely keywords
        recruiter_keywords = self._extract_recruiter_keywords(job_description, all_matching_skills)

        return {
            "match_score": match_score,
            "matching_skills": all_matching_skills,
            "missing_skills": missing_skills,
            "relevant_projects": relevant_projects,
            "relevant_bullets": relevant_bullets,
            "role_relevance": role_relevance,
            "recommendations": recommendations,
            "recruiter_keywords": recruiter_keywords,
            "strongest_fit_areas": self._identify_strongest_fits(all_matching_skills, role_relevance),
        }

    def _extract_job_skills(self, job_description: str) -> List[str]:
        """Extract skills mentioned in job description."""
        # Common skill patterns
        skill_patterns = [
            r'\b(python|sql|excel|r|tableau|power bi|pandas|numpy|scikit-learn)\b',
            r'\b(financial modeling|forecasting|budgeting|variance analysis|roi|p&l)\b',
            r'\b(salesforce|sap|oracle|workday|jira|looker|aws|azure|gcp)\b',
            r'\b(communication|leadership|project management|stakeholder management)\b',
            r'\b(data analysis|analytics|reporting|visualization|dashboard)\b',
            r'\b(statistics|machine learning|data science|business intelligence)\b',
        ]

        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            skills.extend([match.lower() for match in matches])

        return list(dict.fromkeys(skills))  # Remove duplicates

    def _match_skills(self, job_skills: List[str], profile_skills_text: str) -> List[str]:
        """Find matching skills between job and profile."""
        if not profile_skills_text:
            return []

        profile_skills = [skill.strip().lower() for skill in profile_skills_text.split(',')]
        matches = []

        for job_skill in job_skills:
            # Check for exact matches or partial matches
            for profile_skill in profile_skills:
                if job_skill in profile_skill or profile_skill in job_skill:
                    matches.append(job_skill)
                    break

        return list(dict.fromkeys(matches))

    def _find_relevant_projects(self, job_description: str) -> List[str]:
        """Find most relevant projects from profile based on job description."""
        projects_text = self.profile.get("projects", "")
        if not projects_text:
            return []

        projects = [proj.strip() for proj in projects_text.split('|') if proj.strip()]
        relevant = []

        # Keywords that indicate project relevance
        relevance_keywords = [
            'dashboard', 'reporting', 'automation', 'analysis', 'model', 'forecast',
            'migration', 'data', 'financial', 'budget', 'variance', 'tableau',
            'python', 'sql', 'excel', 'process', 'improvement'
        ]

        for project in projects:
            project_lower = project.lower()
            if any(keyword in project_lower for keyword in relevance_keywords):
                if any(keyword in job_description for keyword in relevance_keywords):
                    relevant.append(project)

        return relevant[:3]  # Return top 3 most relevant

    def _find_relevant_bullets(self, job_description: str) -> List[str]:
        """Find most relevant resume bullets based on job description."""
        bullets_text = self.profile.get("resume_bullets", "")
        if not bullets_text:
            return []

        # Split bullets by bullet points or newlines
        bullets = []
        for line in bullets_text.split('\n'):
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                bullets.append(line[1:].strip())
            elif line:
                bullets.append(line)

        relevant = []
        relevance_keywords = [
            'automated', 'reporting', 'dashboard', 'analysis', 'model', 'forecast',
            'migration', 'data', 'financial', 'budget', 'variance', 'tableau',
            'python', 'sql', 'excel', 'process', 'improvement', 'led', 'team',
            'mentored', 'developed', 'created', 'implemented'
        ]

        for bullet in bullets:
            bullet_lower = bullet.lower()
            if any(keyword in bullet_lower for keyword in relevance_keywords):
                if any(keyword in job_description for keyword in relevance_keywords):
                    relevant.append(bullet)

        return relevant[:4]  # Return top 4 most relevant

    def _check_role_relevance(self, job_title: str) -> Dict:
        """Check how well the job title matches target roles."""
        target_roles = self.profile.get("target_roles", "").lower()
        if not target_roles:
            return {"relevant": False, "matched_roles": []}

        target_role_list = [role.strip() for role in target_roles.split(',')]
        matched_roles = []

        for target_role in target_role_list:
            if target_role in job_title or any(word in job_title for word in target_role.split()):
                matched_roles.append(target_role.title())

        return {
            "relevant": len(matched_roles) > 0,
            "matched_roles": matched_roles
        }

    def _calculate_match_score(self, matching_skills: List[str], missing_skills: List[str],
                             role_relevance: Dict, job_skills: List[str]) -> int:
        """Calculate overall match score (0-100)."""
        if not job_skills:
            return 50  # Neutral score if no skills detected

        # Base score from skill matching
        skill_match_ratio = len(matching_skills) / len(job_skills)
        skill_score = skill_match_ratio * 60  # 60% weight on skills

        # Role relevance bonus
        role_bonus = 20 if role_relevance.get("relevant", False) else 0

        # Experience/projects bonus (assume good if we have relevant content)
        experience_bonus = 10 if (self.profile.get("work_experience") and
                                self.profile.get("projects")) else 0

        # Penalty for missing critical skills
        missing_penalty = min(len(missing_skills) * 5, 20)

        total_score = skill_score + role_bonus + experience_bonus - missing_penalty
        return max(0, min(100, int(total_score)))

    def _generate_recommendations(self, matching_skills: List[str], missing_skills: List[str],
                                relevant_projects: List[str], relevant_bullets: List[str]) -> List[str]:
        """Generate recommendations for the application."""
        recommendations = []

        if matching_skills:
            recommendations.append(f"Highlight your expertise in: {', '.join(matching_skills[:3])}")

        if relevant_projects:
            recommendations.append("Emphasize these relevant projects in your application")

        if relevant_bullets:
            recommendations.append("Use these achievement-focused bullet points in your resume/cover letter")

        if missing_skills:
            recommendations.append(f"Consider addressing skill gaps in: {', '.join(missing_skills[:2])}")

        # Leadership and communication recommendations
        if 'communication' in matching_skills or 'leadership' in matching_skills:
            recommendations.append("Emphasize your leadership and communication experience")

        return recommendations

    def _extract_recruiter_keywords(self, job_description: str, matching_skills: List[str]) -> List[str]:
        """Extract likely ATS/recruiter keywords from job description."""
        keywords = []

        # Add matching skills
        keywords.extend(matching_skills)

        # Look for common job keywords
        common_keywords = [
            'analysis', 'reporting', 'financial', 'data', 'business', 'management',
            'excel', 'sql', 'python', 'tableau', 'dashboard', 'forecasting', 'budgeting'
        ]

        for keyword in common_keywords:
            if keyword in job_description:
                keywords.append(keyword)

        return list(dict.fromkeys(keywords))[:8]  # Return top 8 unique keywords

    def _identify_strongest_fits(self, matching_skills: List[str], role_relevance: Dict) -> List[str]:
        """Identify the strongest fit areas."""
        fits = []

        if role_relevance.get("relevant"):
            fits.append("Role alignment with your target positions")

        if any(skill in ['python', 'sql', 'excel'] for skill in matching_skills):
            fits.append("Technical skills match")

        if any(skill in ['financial modeling', 'forecasting', 'budgeting'] for skill in matching_skills):
            fits.append("Finance and analytics expertise")

        if any(skill in ['tableau', 'power bi', 'reporting'] for skill in matching_skills):
            fits.append("Data visualization and reporting capabilities")

        if not fits:
            fits.append("General analytical and problem-solving skills")

        return fits