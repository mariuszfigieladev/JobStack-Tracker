from sqlmodel import Session, select
from app.models import Company, JobOffer, TechTag, JobOfferTagLink

def create_job_offer_with_company(session: Session, offer_dict: dict, company_name: str) -> JobOffer:
    requirements = offer_dict.pop("requirements", [])
    print(f"DEBUG BACKEND: Otrzymane wymagania z LLM -> {requirements}", flush=True)
    
    company = session.exec(select(Company).where(Company.name == company_name)).first()
    if not company:
        company = Company(name=company_name)
        session.add(company)
        session.commit()
        session.refresh(company)
        
    offer = JobOffer(**offer_dict, company_id=company.id)
    session.add(offer)
    session.commit()
    session.refresh(offer)
    
    for req in requirements:
        req_clean = req.strip().lower()
        
        tag = session.exec(select(TechTag).where(TechTag.name == req_clean)).first()
        if not tag:
            tag = TechTag(name=req_clean)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            
        link_exists = session.exec(
            select(JobOfferTagLink).where(
                JobOfferTagLink.job_offer_id == offer.id,
                JobOfferTagLink.tech_tag_id == tag.id
            )
        ).first()
        
        if not link_exists:
            link = JobOfferTagLink(job_offer_id=offer.id, tech_tag_id=tag.id)
            session.add(link)
        
    session.commit()
    session.refresh(offer)
    return offer