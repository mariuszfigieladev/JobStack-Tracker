from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

class JobOfferTagLink(SQLModel, table=True):
    __tablename__ = "job_offer_tag_link"
    job_offer_id: Optional[int] = Field(default=None, foreign_key="job_offers.id", primary_key=True)
    tech_tag_id: Optional[int] = Field(default=None, foreign_key="tech_tags.id", primary_key=True)

class TechTag(SQLModel, table=True):
    __tablename__ = "tech_tags"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    
    offers: List["JobOffer"] = Relationship(back_populates="tags", link_model=JobOfferTagLink)

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    website: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    offers: List["JobOffer"] = Relationship(back_populates="company")

class JobOffer(SQLModel, table=True):
    __tablename__ = "job_offers"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    url: str = Field(unique=True)
    raw_content: str = Field(description="Full raw text scraped from the job posting")
    
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    currency: Optional[str] = Field(default="PLN")
    
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(default=None)

    company_id: int = Field(foreign_key="companies.id")
    
    company: Company = Relationship(back_populates="offers")
    tags: List[TechTag] = Relationship(back_populates="offers", link_model=JobOfferTagLink)