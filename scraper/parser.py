import os
import json
from bs4 import BeautifulSoup
import requests
from typing import Optional

class JobScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Logowanie stanu klucza przy starcie
        print(f"DEBUG INIT: Czy klucz API jest wczytany? -> {bool(self.api_key)}", flush=True)
        
        if self.api_key:
            from google import genai
            self.ai_client = genai.Client(api_key=self.api_key)
        else:
            self.ai_client = None

    def fetch_html(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"DEBUG FETCH ERROR: {e}", flush=True)
            return None

    def clean_and_extract_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator="\n")
        return "\n".join([line.strip() for line in text.splitlines() if line.strip()])

    def analyze_with_llm(self, raw_text: str) -> Optional[dict]:
        if not self.ai_client:
            print("DEBUG LLM: Brak zainicjalizowanego ai_client (brak klucza API w kontenerze)!", flush=True)
            return None
        
        prompt = f"""
        Analyze the following raw text from a job posting and extract structural data.
        Return ONLY a JSON object matching this exact schema:
        {{
            "title": "Exact job title, e.g. Senior AI Engineer",
            "company_name": "Cleaned company name, e.g. Alten",
            "salary_min": 6000 or null,
            "salary_max": 10000 or null,
            "currency": "PLN",
            "requirements": ["python", "fastapi", "docker"]
        }}
        
        Text to analyze:
        {raw_text}
        """
        
        try:
            from google.genai import types
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            # Wyciągamy ukryty błąd na wierzch logów Dockera
            print(f"CRITICAL LLM ERROR: {str(e)}", flush=True)
            return None

    def scrape_offer(self, url: str) -> Optional[dict]:
        html_content = self.fetch_html(url)
        soup = BeautifulSoup(html_content if html_content else "", "html.parser")
        raw_text = self.clean_and_extract_text(soup) if html_content else ""
        
        llm_data = self.analyze_with_llm(raw_text) if raw_text else None
        
        if llm_data:
            result = llm_data
        else:
            print("DEBUG SCRAPER: LLM zwrócił None, uruchamiam fallback do pustych wartości.", flush=True)
            result = {
                "title": soup.find("title").get_text().strip() if soup.find("title") else "Unknown",
                "company_name": "Unknown",
                "salary_min": None,
                "salary_max": None,
                "currency": "PLN",
                "requirements": []
            }
            
        result["url"] = url
        result["raw_content"] = raw_text if raw_text else "Failed to fetch HTML content"
        return result