import os
from bs4 import BeautifulSoup
import requests
from typing import Optional, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class ScrapedJobOffer(BaseModel):
    title: str = Field(description="Exact job title, e.g. Senior AI Engineer")
    company_name: str = Field(description="Cleaned company name, e.g. Alten")
    salary_min: Optional[int] = Field(None, description="Minimum salary, null if not specified")
    salary_max: Optional[int] = Field(None, description="Maximum salary, null if not specified")
    currency: Optional[str] = Field("PLN", description="Currency code, e.g. PLN, EUR, USD")
    requirements: List[str] = Field(description="List of key technologies and requirements found in text, e.g. ['Python', 'FastAPI', 'Docker']")

class JobScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        api_key = os.getenv("GEMINI_API_KEY")
        self.ai_client = genai.Client(api_key=api_key) if api_key else None

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
        return "\n".join([line.strip() for line in text.splitlines() if line.strip()])

    def analyze_with_llm(self, raw_text: str) -> Optional[ScrapedJobOffer]:
        if not self.ai_client:
            return None
        
        prompt = f"Analyze the following raw text from a job posting and extract structural data:\n\n{raw_text}"
        
        try:
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ScrapedJobOffer,
                    temperature=0.1
                ),
            )
            return ScrapedJobOffer.model_validate_json(response.text)
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return None

    def scrape_offer(self, url: str) -> Optional[dict]:
        html_content = self.fetch_html(url)
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        raw_text = self.clean_and_extract_text(soup)
        
        llm_data = self.analyze_with_llm(raw_text)
        
        if llm_data:
            result = llm_data.model_dump()
        else:
            result = {
                "title": soup.find("title").get_text().strip() if soup.find("title") else "Unknown",
                "company_name": "Unknown",
                "salary_min": None,
                "salary_max": None,
                "currency": "PLN",
                "requirements": []
            }
            
        result["url"] = url
        result["raw_content"] = raw_text
        return result