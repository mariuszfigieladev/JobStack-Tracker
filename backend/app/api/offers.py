from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select, func
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from typing import Optional, List
import requests

from app.database import get_session
from app.models import Company, JobOffer, TechTag, JobOfferTagLink

router = APIRouter(prefix="/offers", tags=["Offers"])

SCRAPER_SERVICE_URL = "http://scraper:8001/scrape"

class ScrapeRequest(BaseModel):
    url: str

class OfferUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    title: Optional[str] = None

@router.post("/scrape")
def scrape_and_store_offer(request: ScrapeRequest, db: Session = Depends(get_session)):
    try:
        response = requests.post(SCRAPER_SERVICE_URL, json={"url": request.url}, timeout=60.0)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f"Scraper rejected the request. Status: {response.status_code}"
            )
        scraped_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper connection error: {str(e)}")

    company_name = scraped_data.get("company_name", "Unknown")
    company = db.exec(select(Company).where(Company.name == company_name)).first()
    if not company:
        company = Company(name=company_name)
        db.add(company)
        db.flush()

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

    db.commit()
    db.refresh(new_offer)
    return {"status": "success", "inserted_id": new_offer.id}

@router.get("/analytics/top-tags")
def get_top_tech_tags(limit: int = 10, db: Session = Depends(get_session)):
    statement = (
        select(TechTag.name, func.count(JobOfferTagLink.job_offer_id))
        .join(JobOfferTagLink, TechTag.id == JobOfferTagLink.tech_tag_id)
        .group_by(TechTag.id)
        .order_by(func.count(JobOfferTagLink.job_offer_id).desc())
        .limit(limit)
    )
    results = db.exec(statement).all()
    return [{"tag": row[0], "count": row[1]} for row in results]

@router.get("/{offer_id}/notebooklm", response_class=PlainTextResponse)
def get_offer_for_notebooklm(offer_id: int, db: Session = Depends(get_session)):
    offer = db.get(JobOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
        
    company_name = offer.company.name if offer.company else "Unknown"
    tags_list = [tag.name for tag in offer.tags]
    
    payload = {
        "company_name": company_name,
        "title": offer.title,
        "tech_tags": tags_list,
        "raw_content": offer.raw_content
    }
    
    try:
        response = requests.post("http://scraper:8001/generate-brief", json=payload, timeout=60.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Scraper LLM generation failed")
            
        return response.json().get("brief", "Error extracting brief from response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[dict])
def get_offers(skip: int = 0, limit: int = 50, db: Session = Depends(get_session)):
    statement = select(JobOffer).order_by(JobOffer.application_date.desc()).offset(skip).limit(limit)
    offers = db.exec(statement).all()
    
    result = []
    for offer in offers:
        company_name = offer.company.name if offer.company else "Unknown"
        result.append({
            "id": offer.id,
            "title": offer.title,
            "url": offer.url,
            "company_name": company_name,
            "application_date": offer.application_date,
            "tech_tag_ids": [tag.id for tag in offer.tags],
            "tech_tags": [tag.name for tag in offer.tags],
            "raw_content": offer.raw_content
        })
    return result

@router.patch("/{offer_id}")
def update_offer(offer_id: int, request: OfferUpdateRequest, db: Session = Depends(get_session)):
    offer = db.get(JobOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
        
    if request.company_name:
        company_name_clean = request.company_name.strip()
        # Szukamy firmy o takiej nazwie lub tworzymy nową
        company = db.exec(select(Company).where(Company.name == company_name_clean)).first()
        if not company:
            company = Company(name=company_name_clean)
            db.add(company)
            db.flush()
            
        # Aktualizujemy klucz obcy oraz wymuszamy odświeżenie relacji obiektowej
        offer.company_id = company.id
        offer.company = company
        flag_modified(offer, "company_id")
        
    if request.title:
        offer.title = request.title.strip()
        flag_modified(offer, "title")
        
    db.add(offer)
    db.commit()
    db.refresh(offer)
    
    return {
        "status": "updated", 
        "offer_id": offer.id, 
        "new_company": offer.company.name if offer.company else "Unknown"
    }