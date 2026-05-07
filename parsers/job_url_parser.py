import re

import requests
from bs4 import BeautifulSoup

from agents.job_analyzer import JobAnalyzer

class JobURLParser:
    """Parser for extracting job information from a job or application URL."""

    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
    )

    SECTION_KEYWORDS = [
        "responsibilities",
        "qualifications",
        "requirements",
        "preferred qualifications",
        "about the role",
        "what you’ll do",
        "what youll do",
        "skills",
        "education",
        "experience",
        "role",
        "responsible",
    ]

    JUNK_PHRASES = [
        "sign in",
        "log in",
        "register",
        "privacy policy",
        "terms of use",
        "cookie policy",
        "apply now",
        "save job",
        "share",
        "back to jobs",
        "job alert",
        "search",
        "follow us",
        "email address",
    ]

    def scrape(self, url: str) -> dict:
        static_result = self._static_scrape(url)
        if static_result["scrape_status"] == "success":
            return static_result

        rendered_result = self._rendered_scrape(url, static_result.get("description_text", ""))
        if rendered_result["scrape_status"] in {"success", "partial"}:
            return rendered_result

        if static_result.get("description_text"):
            static_result["error_message"] = (
                f"Playwright fallback failed: {rendered_result.get('error_message', '')}".strip()
            )
            return static_result

        return rendered_result

    def _static_scrape(self, url: str) -> dict:
        try:
            response = requests.get(url, headers={"User-Agent": self.USER_AGENT}, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            self._cleanup_soup(soup)

            visible_text = self._extract_visible_text(soup)
            section_text = self._extract_job_sections(soup, visible_text)
            description_text = (section_text or visible_text).strip()

            if not description_text:
                raise ValueError("No visible job description text could be extracted from the URL.")

            title = self._extract_title(soup, description_text)
            company = self._extract_company(soup, description_text)
            location = self._extract_location(description_text)

            analyzer = JobAnalyzer()
            analysis = analyzer.analyze(description_text)
            extracted_keywords = ", ".join(
                list(dict.fromkeys(
                    analysis.get("role_keywords", [])
                    + analysis.get("required_skills", [])
                    + analysis.get("preferred_skills", [])
                ))
            )

            word_count = len(description_text.split())
            scrape_status = "success" if word_count >= 100 else "partial"

            return {
                "url": url,
                "title": title,
                "company": company,
                "location": location,
                "description_text": description_text,
                "extracted_keywords": extracted_keywords,
                "scrape_status": scrape_status,
                "source": "static scraper",
                "error_message": "",
            }
        except Exception as exc:
            return {
                "url": url,
                "title": "",
                "company": "",
                "location": "",
                "description_text": "",
                "extracted_keywords": "",
                "scrape_status": "failed",
                "source": "static scraper",
                "error_message": str(exc),
            }

    def _rendered_scrape(self, url: str, fallback_text: str) -> dict:
        try:
            from browser.browser_scanner import scan_rendered_page
        except ImportError:
            return {
                "url": url,
                "title": "",
                "company": "",
                "location": "",
                "description_text": fallback_text,
                "extracted_keywords": "",
                "scrape_status": "failed",
                "source": "static scraper",
                "error_message": "Playwright is not installed.",
            }

        rendered = scan_rendered_page(url)
        if rendered["status"] == "failed":
            return {
                "url": url,
                "title": "",
                "company": "",
                "location": "",
                "description_text": fallback_text,
                "extracted_keywords": "",
                "scrape_status": "failed",
                "source": "static scraper",
                "error_message": rendered["error_message"],
            }

        description_text = rendered["body_text"].strip() or fallback_text.strip()
        if not description_text:
            return {
                "url": url,
                "title": "",
                "company": "",
                "location": "",
                "description_text": "",
                "extracted_keywords": "",
                "scrape_status": "failed",
                "source": "playwright rendered scan",
                "error_message": "Rendered browser scan returned no visible text.",
            }

        title = rendered["title"] or self._extract_title(BeautifulSoup(rendered["body_text"], "html.parser"), description_text)
        company = self._extract_company(None, description_text)
        location = self._extract_location(description_text)

        analyzer = JobAnalyzer()
        analysis = analyzer.analyze(description_text)
        extracted_keywords = ", ".join(
            list(dict.fromkeys(
                analysis.get("role_keywords", [])
                + analysis.get("required_skills", [])
                + analysis.get("preferred_skills", [])
            ))
        )

        scrape_status = "success" if rendered["word_count"] >= 100 else "partial"

        return {
            "url": url,
            "title": title,
            "company": company,
            "location": location,
            "description_text": description_text,
            "extracted_keywords": extracted_keywords,
            "scrape_status": scrape_status,
            "source": "playwright rendered scan",
            "error_message": rendered["error_message"],
        }

    def _cleanup_soup(self, soup: BeautifulSoup):
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "svg", "canvas", "img", "button", "input"]):
            tag.decompose()

    def _extract_visible_text(self, soup: BeautifulSoup) -> str:
        lines = []
        for line in soup.get_text(separator="\n").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = stripped.lower()
            if any(phrase in low for phrase in self.JUNK_PHRASES):
                continue
            if len(stripped) < 4:
                continue
            lines.append(stripped)
        return "\n".join(lines)

    def _extract_job_sections(self, soup: BeautifulSoup, fallback_text: str) -> str:
        sections = []
        keyword_pattern = re.compile("|".join([re.escape(keyword) for keyword in self.SECTION_KEYWORDS]), re.I)

        for header in soup.find_all(re.compile(r"^h[1-6]$")):
            heading_text = header.get_text(separator=" ").strip()
            if keyword_pattern.search(heading_text):
                sections.append(self._collect_section_text(header))

        if sections:
            return "\n\n".join([section for section in sections if section.strip()])

        containers = [
            *soup.find_all(attrs={"class": re.compile("|".join(self.SECTION_KEYWORDS), re.I)}),
            *soup.find_all(attrs={"id": re.compile("|".join(self.SECTION_KEYWORDS), re.I)}),
        ]
        for container in containers:
            text = container.get_text(separator=" ").strip()
            if len(text.split()) >= 20:
                sections.append(text)

        if sections:
            return "\n\n".join(sections)

        return fallback_text

    def _collect_section_text(self, header):
        text_parts = [header.get_text(separator=" ").strip()]
        for sibling in header.find_next_siblings():
            if sibling.name and re.match(r"^h[1-6]$", sibling.name, re.I):
                break
            if sibling.name in ["p", "ul", "ol", "div", "section"]:
                segment = sibling.get_text(separator=" ").strip()
                if segment:
                    text_parts.append(segment)
        return "\n".join(text_parts)

    def _extract_title(self, soup: BeautifulSoup, text: str) -> str:
        title_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if title_tag and title_tag.get("content"):
            return title_tag["content"].strip()

        if soup.title and soup.title.string:
            return soup.title.string.strip()

        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        lines = [line for line in text.splitlines() if line]
        return lines[0].strip() if lines else "Unknown Title"

    def _extract_company(self, soup, text: str) -> str:
        if soup is not None:
            company_tag = soup.find("meta", property="og:site_name")
            if company_tag and company_tag.get("content"):
                return company_tag["content"].strip()

            author_tag = soup.find("meta", attrs={"name": "author"})
            if author_tag and author_tag.get("content"):
                return author_tag["content"].strip()

        for pattern in [r"Company:\s*(.+)", r"Employer:\s*(.+)", r"at\s+([A-Z][A-Za-z0-9 &]+)"]:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return "Unknown"

    def _extract_location(self, text: str) -> str:
        for pattern in [r"Location:\s*(.+)", r"Based in\s*(.+)", r"(Remote|Hybrid)"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip() if match.groups() else match.group(0).strip()
        return "Not specified"
