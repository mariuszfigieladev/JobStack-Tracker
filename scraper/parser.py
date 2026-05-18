import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }

    def fetch_html(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def clean_and_extract_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join([line for line in lines if line])

    def scrape_offer(self, url: str) -> Optional[Dict]:
        if "linkedin.com" in url:
            pass

        html_content = self.fetch_html(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        
        title = soup.find("title")
        title_text = title.get_text().strip() if title else "Unknown Position"

        og_company = soup.find("meta", property="og:site_name")
        company_name = og_company["content"].strip() if og_company else "Unknown Company"

        raw_text = self.clean_and_extract_text(soup)

        return {
            "title": title_text,
            "company_name": company_name,
            "url": url,
            "raw_content": raw_text,
            "salary_min": None,
            "salary_max": None,
            "currency": "PLN"
        }