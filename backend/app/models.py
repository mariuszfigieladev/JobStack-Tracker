from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    website: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship: one company can have multiple job offers
    offers: List["JobOffer"] = Relationship(back_populates="company")

class JobOffer(SQLModel, table=True):
    __tablename__ = "job_offers"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    url: str = Field(unique=True)  # Prevents scraping the exact same offer twice
    raw_content: str = Field(description="Full raw text scraped from the job posting")
    
    # Compensation details
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    currency: Optional[str] = Field(default="PLN")
    
    # Timeline & Notes
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None, description="Personal notes about the application process")

    # Foreign key and relationship to Company
    company_id: int = Field(foreign_key="companies.id")
    company: Company = Relationship(back_populates="offers")