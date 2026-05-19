from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from parser import JobScraper

app = FastAPI(title="Scraper API")
scraper = JobScraper()

class ScrapeRequest(BaseModel):
    url: str

class BriefRequest(BaseModel):
    company_name: str
    title: str
    tech_tags: List[str]
    raw_content: str

@app.post("/scrape")
def scrape_endpoint(request: ScrapeRequest):
    result = scraper.scrape_offer(request.url)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to scrape URL")
    return result

@app.post("/generate-brief")
def generate_brief_endpoint(request: BriefRequest):
    brief_text = scraper.generate_notebooklm_brief(request.model_dump())
    return {"brief": brief_text}