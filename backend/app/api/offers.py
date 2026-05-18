from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import requests
from app.database import get_session
from app.crud.offer import create_job_offer_with_company
from app.models import JobOffer

router = APIRouter(prefix="/offers", tags=["Job Offers"])

class TagRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CompanyRead(BaseModel):
    id: int
    name: str
    website: Optional[str] = None

    class Config:
        from_attributes = True

class JobOfferRead(BaseModel):
    id: int
    title: str
    url: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str
    applied_at: datetime
    notes: Optional[str] = None
    company: CompanyRead
    tags: List[TagRead]

    class Config:
        from_attributes = True

class JobOfferCreate(BaseModel):
    company_name: str
    title: str
    url: str
    raw_content: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = "PLN"
    notes: Optional[str] = None
    requirements: Optional[List[str]] = []

class ScrapeRequest(BaseModel):
    url: str

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_manual_offer(offer_input: JobOfferCreate, session: Session = Depends(get_session)):
    offer_dict = offer_input.model_dump()
    company_name = offer_dict.pop("company_name")
    
    try:
        new_offer = create_job_offer_with_company(session, offer_dict, company_name)
        return {"message": "Job offer saved successfully", "offer_id": new_offer.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save job offer. Error: {str(e)}"
        )

@router.post("/scrape", response_model=dict, status_code=status.HTTP_201_CREATED)
def scrape_and_add_offer(request: ScrapeRequest, session: Session = Depends(get_session)):
    try:
        scraper_response = requests.post("http://scraper:8001/scrape", json={"url": request.url}, timeout=15)
        scraper_response.raise_for_status()
        scraped_data = scraper_response.json()
        
        company_name = scraped_data.pop("company_name")
        new_offer = create_job_offer_with_company(session, scraped_data, company_name)
        
        return {"message": "Job offer scraped and saved", "offer_id": new_offer.id}
    except requests.RequestException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Scraper service error: {e}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[JobOfferRead])
def get_all_offers(session: Session = Depends(get_session)):
    # Używamy joinedload, aby załadować relacje Many-to-One (company) oraz Many-to-Many (tags)
    statement = select(JobOffer).options(
        joinedload(JobOffer.company),
        joinedload(JobOffer.tags)
    )
    offers = session.exec(statement).unique().all()
    return offers