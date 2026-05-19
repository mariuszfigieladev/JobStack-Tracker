import os
import json
from bs4 import BeautifulSoup
from typing import Optional
from playwright.sync_api import sync_playwright

class JobScraper:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            from google import genai
            self.ai_client = genai.Client(api_key=self.api_key)
        else:
            self.ai_client = None

    def fetch_html(self, url: str) -> Optional[str]:
        print(f"DEBUG PLAYWRIGHT: Start fetching {url}", flush=True)
        try:
            with sync_playwright() as p:
                print("DEBUG PLAYWRIGHT: Launching Chromium...", flush=True)
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox", 
                        "--disable-setuid-sandbox", 
                        "--disable-dev-shm-usage"
                    ]
                )
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                print("DEBUG PLAYWRIGHT: Loading page...", flush=True)
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                html_content = page.content()
                browser.close()
                print("DEBUG PLAYWRIGHT: Success. Returning HTML.", flush=True)
                return html_content
        except Exception as e:
            print(f"DEBUG FETCH ERROR: {e}", flush=True)
            return None

    def clean_and_extract_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = soup.get_text(separator="\n")
        return "\n".join([line.strip() for line in text.splitlines() if line.strip()])

    def analyze_with_llm(self, raw_text: str) -> Optional[dict]:
        if not self.ai_client:
            print("DEBUG LLM: API key missing!", flush=True)
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
            print("DEBUG LLM: Sending request to Gemini...", flush=True)
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                ),
            )
            print("DEBUG LLM: Received response.", flush=True)
            return json.loads(response.text)
        except Exception as e:
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
            print("DEBUG SCRAPER: LLM returned None, running fallback.", flush=True)
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
    
    def generate_notebooklm_brief(self, data: dict) -> str:
        if not self.ai_client:
            return "ERROR: Gemini API key is missing."
        
        prompt = f"""
        Act as a Senior IT Recruiter. Analyze this job offer and prepare a structured, highly readable brief.
        This document will be fed into NotebookLM to generate an educational audio podcast for interview preparation.
        
        Company: {data.get('company_name')}
        Title: {data.get('title')}
        Tech Stack: {', '.join(data.get('tech_tags', []))}
        
        Raw Content:
        {data.get('raw_content')}
        
        Format strictly in Markdown. Include:
        1. Role Overview (TL;DR of the position)
        2. Core Responsibilities (Actionable list)
        3. Tech Stack Deep Dive (Why these tools matter for this role)
        4. Potential Interview Questions (Generate 5 hard technical/behavioral questions based on the requirements)
        """
        
        try:
            from google.genai import types
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            return response.text
        except Exception as e:
            return f"CRITICAL LLM ERROR: {str(e)}"