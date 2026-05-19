from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select, func, delete
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
    raw_content: Optional[str] = None

class OfferUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    title: Optional[str] = None
    tech_tags: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

@router.post("/scrape")
def scrape_and_store_offer(request: ScrapeRequest, db: Session = Depends(get_session)):
    try:
        payload = {"url": request.url, "raw_content": request.raw_content}
        response = requests.post(SCRAPER_SERVICE_URL, json=payload, timeout=60.0)
        
        if response.status_code != 200:
            scraped_data = {
                "title": "Protected Offer",
                "company_name": "Unknown",
                "salary_min": None,
                "salary_max": None,
                "currency": "PLN",
                "requirements": [],
                "raw_content": f"Failed to fetch content directly (Status {response.status_code})."
            }
        else:
            scraped_data = response.json()
            
    except Exception as e:
        scraped_data = {
            "title": "Connection Failure",
            "company_name": "Unknown",
            "salary_min": None,
            "salary_max": None,
            "currency": "PLN",
            "requirements": [],
            "raw_content": f"Scraper connection error: {str(e)}."
        }

    company_name = scraped_data.get("company_name") or "Unknown"
    company = db.exec(select(Company).where(Company.name == company_name)).first()
    if not company:
        company = Company(name=company_name)
        db.add(company)
        db.flush()

    new_offer = JobOffer(
        title=scraped_data.get("title") or "Unknown Title",
        url=request.url,
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
        if not req_clean: continue
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

@router.get("", response_model=List[dict])
def get_offers(skip: int = 0, limit: int = 50, db: Session = Depends(get_session)):
    statement = select(JobOffer).order_by(JobOffer.application_date.desc()).offset(skip).limit(limit)
    offers = db.exec(statement).all()
    
    result = []
    for offer in offers:
        result.append({
            "id": offer.id,
            "title": offer.title,
            "url": offer.url,
            "company_name": offer.company.name if offer.company else "Unknown",
            "salary_min": offer.salary_min,
            "salary_max": offer.salary_max,
            "currency": offer.currency,
            "application_date": offer.application_date,
            "tech_tags": [tag.name for tag in offer.tags],
            "raw_content": offer.raw_content
        })
    return result

@router.patch("/{offer_id}")
def update_offer(offer_id: int, request: OfferUpdateRequest, db: Session = Depends(get_session)):
    offer = db.get(JobOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
        
    if request.company_name is not None:
        company_name_clean = request.company_name.strip()
        company = db.exec(select(Company).where(Company.name == company_name_clean)).first()
        if not company:
            company = Company(name=company_name_clean)
            db.add(company)
            db.flush()
        offer.company_id = company.id
        offer.company = company
        flag_modified(offer, "company_id")
        
    if request.title is not None:
        offer.title = request.title.strip()
        flag_modified(offer, "title")
        
    # Salary explicitly handles None
    if request.salary_min is not None or "salary_min" in request.model_dump(exclude_unset=True):
        offer.salary_min = request.salary_min
        flag_modified(offer, "salary_min")
        
    if request.salary_max is not None or "salary_max" in request.model_dump(exclude_unset=True):
        offer.salary_max = request.salary_max
        flag_modified(offer, "salary_max")
        
    if request.tech_tags is not None:
        db.exec(delete(JobOfferTagLink).where(JobOfferTagLink.job_offer_id == offer.id))
        for tag_name in request.tech_tags:
            tag_clean = tag_name.strip().lower()
            if not tag_clean: continue
            tag = db.exec(select(TechTag).where(TechTag.name == tag_clean)).first()
            if not tag:
                tag = TechTag(name=tag_clean)
                db.add(tag)
                db.flush()
            link = JobOfferTagLink(job_offer_id=offer.id, tech_tag_id=tag.id)
            db.add(link)
            
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return {"status": "updated"}

@router.get("/{offer_id}/notebooklm", response_class=PlainTextResponse)
def get_offer_for_notebooklm(offer_id: int, db: Session = Depends(get_session)):
    offer = db.get(JobOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Job offer not found")
    
    payload = {
        "company_name": offer.company.name if offer.company else "Unknown",
        "title": offer.title,
        "tech_tags": [tag.name for tag in offer.tags],
        "raw_content": offer.raw_content
    }
    
    try:
        response = requests.post("http://scraper:8001/generate-brief", json=payload, timeout=60.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Scraper LLM failed")
        return response.json().get("brief", "Error extracting brief")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))