from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Optional
from pydantic import BaseModel, HttpUrl
from app.database import get_session
from app.crud.offer import create_job_offer_with_company

router = APIRouter(prefix="/offers", tags=["Job Offers"])

# Pydantic schema for incoming request validation
class JobOfferCreate(BaseModel):
    company_name: str
    title: str
    url: str
    raw_content: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = "PLN"
    notes: Optional[str] = None

class ScrapeRequest(BaseModel):
    url: str

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_manual_offer(offer_input: JobOfferCreate, session: Session = Depends(get_session)):
    """
    Manually add a job offer and automatically handle company creation/linking.
    """
    # Convert Pydantic model to dictionary excluding company_name for the CRUD layer
    offer_dict = offer_input.model_dump()
    company_name = offer_dict.pop("company_name")
    
    try:
        new_offer = create_job_offer_with_company(session, offer_dict, company_name)
        return {"message": "Job offer saved successfully", "offer_id": new_offer.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save job offer. URL might be duplicated. Error: {str(e)}"
        )

@router.post("/scrape", status_code=status.HTTP_202_ACCEPTED)
def scrape_and_add_offer(request: ScrapeRequest):
    """
    Endpoint dedicated for the BeautifulSoup scraper. 
    Currently a placeholder for Step 3.
    """
    return {
        "message": "Scraping task accepted", 
        "target_url": request.url,
        "status": "Pending implementation of the BeautifulSoup module"
    }