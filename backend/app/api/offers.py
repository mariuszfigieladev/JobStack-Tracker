from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
import requests

from app.database import get_session
from app.models import Company, JobOffer, TechTag, JobOfferTagLink

router = APIRouter(prefix="/offers", tags=["Offers"])

SCRAPER_SERVICE_URL = "http://scraper:8001/scrape"

# Wymuszamy, aby Swagger używał ładnego pola JSON do wklejania URL
class ScrapeRequest(BaseModel):
    url: str

@router.post("/scrape")
def scrape_and_store_offer(request: ScrapeRequest, db: Session = Depends(get_session)):
    # 1. Pobranie danych ze scrapera (zwiększony timeout do 60 sekund!)
    try:
        response = requests.post(SCRAPER_SERVICE_URL, json={"url": request.url}, timeout=60.0)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f"Scraper rejected the request. Status: {response.status_code}, Info: {response.text}"
            )
            
        scraped_data = response.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Scraper took too long (over 60 seconds). Try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper connection error: {str(e)}")

    # 2. Pobranie lub stworzenie firmy
    company_name = scraped_data.get("company_name", "Unknown")
    company = db.exec(select(Company).where(Company.name == company_name)).first()
    if not company:
        company = Company(name=company_name)
        db.add(company)
        db.flush()

    # 3. Stworzenie oferty pracy
    new_offer = JobOffer(
        title=scraped_data.get("title"),
        url=scraped_data.get("url"),
        salary_min=scraped_data.get("salary_min"),
        salary_max=scraped_data.get("salary_max"),
        currency=scraped_data.get("currency", "PLN"),
        raw_content=scraped_data.get("raw_content", ""),
        company_id=company.id
    )
    db.add(new_offer)
    db.flush()

    # 4. Mapowanie tagów technologicznych (Many-to-Many)
    requirements = scraped_data.get("requirements", [])
    for req in requirements:
        req_clean = req.lower().strip()
        if not req_clean:
            continue
            
        tag = db.exec(select(TechTag).where(TechTag.name == req_clean)).first()
        if not tag:
            tag = TechTag(name=req_clean)
            db.add(tag)
            db.flush()
            
        link = JobOfferTagLink(job_offer_id=new_offer.id, tech_tag_id=tag.id)
        db.add(link)

    # 5. Zapisanie transakcji
    db.commit()
    db.refresh(new_offer)

    return {"status": "success", "inserted_id": new_offer.id, "data": scraped_data}