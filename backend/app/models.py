from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class JobOfferTagLink(SQLModel, table=True):
    __tablename__ = "job_offer_tag_link"
    job_offer_id: Optional[int] = Field(default=None, foreign_key="job_offers.id", primary_key=True)
    tech_tag_id: Optional[int] = Field(default=None, foreign_key="tech_tags.id", primary_key=True)

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    offers: List["JobOffer"] = Relationship(back_populates="company")

class TechTag(SQLModel, table=True):
    __tablename__ = "tech_tags"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    offers: List["JobOffer"] = Relationship(back_populates="tags", link_model=JobOfferTagLink)

class JobOffer(SQLModel, table=True):
    __tablename__ = "job_offers"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str = Field(unique=True)
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    currency: str = Field(default="PLN")
    application_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    raw_content: str
    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    company: Optional[Company] = Relationship(back_populates="offers")
    tags: List[TechTag] = Relationship(back_populates="offers", link_model=JobOfferTagLink)