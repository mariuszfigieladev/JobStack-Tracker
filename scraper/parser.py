import os
import json
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        api_key = os.getenv("GEMINI_API_KEY")
        self.ai_client = genai.Client(api_key=api_key) if api_key else None

    def scrape_offer(self, url: str, raw_content: str = None) -> dict:
        if raw_content:
            text_content = raw_content
        else:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text(separator='\n', strip=True)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return None

        if not self.ai_client:
            return {
                "title": "Fallback Title",
                "company_name": "Unknown",
                "salary_min": None,
                "salary_max": None,
                "currency": "PLN",
                "requirements": [],
                "raw_content": text_content[:2000]
            }

        prompt = f"""
        Extract the following structured information from this job offer text.
        URL: {url}
        
        Text Content:
        {text_content}
        
        Return STRICTLY a JSON object with this exact schema:
        {{
            "title": "Job Title String",
            "company_name": "Company Name String or Unknown",
            "salary_min": integer_or_null,
            "salary_max": integer_or_null,
            "currency": "PLN/EUR/USD etc",
            "requirements": ["tech1", "tech2", "framework1"],
            "raw_content": "Full raw text content cleaned up slightly"
        }}
        """

        try:
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
            print(f"LLM extraction error: {e}")
            return None

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
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            return response.text
        except Exception as e:
            return f"CRITICAL LLM ERROR: {str(e)}"