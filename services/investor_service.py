from sqlalchemy.orm import Session
from models import Investor
from schemas import investors as schemas


def create_investor(db: Session, investor: schemas.InvestorCreate):
    db_investor = Investor(**investor.model_dump())
    db.add(db_investor)
    db.commit()
    db.refresh(db_investor)
    return db_investor


def search_investors(db: Session, filters):
    query = db.query(Investor)
    # Apply filters
    return query.all()
