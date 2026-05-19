from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select, func
from pydantic import BaseModel
import requests

from app.database import get_session
from app.models import Company, JobOffer, TechTag, JobOfferTagLink

router = APIRouter(prefix="/offers", tags=["Offers"])

SCRAPER_SERVICE_URL = "http://scraper:8001/scrape"

class ScrapeRequest(BaseModel):
    url: str

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
    
    markdown_template = f"""# JOB OFFER BRIEF: {offer.title}
## COMPANY
{company_name}

## METADATA
- **URL:** {offer.url}
- **Salary Minimum:** {offer.salary_min if offer.salary_min else "Not specified"}
- **Salary Maximum:** {offer.salary_max if offer.salary_max else "Not specified"}
- **Currency:** {offer.currency}

## KEY TECHNOLOGIES & REQUIREMENTS
{", ".join(tags_list) if tags_list else "None extracted"}

---

## FULL RAW CONTENT
{offer.raw_content}
"""
    return markdown_template