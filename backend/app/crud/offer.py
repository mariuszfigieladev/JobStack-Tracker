from sqlmodel import Session, select
from app.models import Company, JobOffer

def create_job_offer_with_company(session: Session, offer_data: dict, company_name: str) -> JobOffer:
    # 1. Check if the company already exists
    statement = select(Company).where(Company.name == company_name)
    company = session.exec(statement).first()

    # 2. If it doesn't exist, create a new one
    if not company:
        company = Company(name=company_name)
        session.add(company)
        session.commit()
        session.refresh(company)

    # 3. Create the job offer and link it to the company
    db_offer = JobOffer(**offer_data, company_id=company.id)
    session.add(db_offer)
    session.commit()
    session.refresh(db_offer)
    
    return db_offer