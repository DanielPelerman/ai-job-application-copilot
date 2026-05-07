def scan_rendered_page(url: str) -> dict:
    """Render a page with Playwright and extract visible body text."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "title": "",
            "body_text": "",
            "word_count": 0,
            "status": "failed",
            "error_message": "Playwright is not installed. Install playwright to enable browser-based URL scanning.",
        }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)
            try:
                page.wait_for_load_state("networkidle", timeout=12000)
            except Exception:
                pass
            body_text = page.locator("body").inner_text() or ""
            title = page.title() or ""
            browser.close()

        word_count = len(body_text.split())
        status = "success" if word_count >= 100 else "partial"

        return {
            "title": title,
            "body_text": body_text,
            "word_count": word_count,
            "status": status,
            "error_message": "",
        }
    except Exception as exc:
        return {
            "title": "",
            "body_text": "",
            "word_count": 0,
            "status": "failed",
            "error_message": f"Playwright scan failed: {exc}",
        }
