from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from parser import JobScraper

app = FastAPI(title="JobStack Scraper API")
scraper = JobScraper()

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape")
def run_scraper(request: ScrapeRequest):
    data = scraper.scrape_offer(request.url)
    if not data:
        raise HTTPException(status_code=400, detail="Failed to scrape URL")
    return data