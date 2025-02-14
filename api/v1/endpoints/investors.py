from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Union
import models
import schemas
from database import get_db
import crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=None)
def create_investor(investor: schemas.InvestorCreate, db: Session = Depends(get_db)):
    try:
        return crud.investor.create(db=db, obj_in=investor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=None)
def read_investors(
        db: Session = Depends(get_db),
        page: int = Query(1, gt=0, description="Page number"),
        per_page: int = Query(50, gt=0, le=100, description="Number of items per page"),
):
    try:
        total = db.query(models.Investor).count()
        skip = (page - 1) * per_page
        investors = crud.investor.get_multi(
            db=db,
            skip=skip,
            limit=per_page,
        )
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": -(-total // per_page),
            "results": investors,
        }
    except Exception as e:
        logger.error(f"Error fetching investors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def normalize_enum_value(value: str) -> str:
    if not value:
        return value
    if isinstance(value, str):
        return value.title().replace('_', ' ')
    return value


def string_to_float(value: str):
    if value == "$1B+":
        return 1000000000, float('inf')
    if value == "$100M - $500M":
        return 100000000, 500000000
    if value == "$500M - $1B":
        return 500000000, 1000000000
    if value == "$25M - $100M":
        return 25000000, 100000000
    if value == "$0 - $25M":
        return 1, 25000000
    if value == "$10M - $25M":
        return 10000000, 25000000
    if value == "$100M+":
        return 100000000, float('inf')
    if value == "$1M - $10M":
        return 1000000, 10000000
    if value == "$0 - $1M":
        return 1, 1000000
    if value == "$5M - $20M":
        return 5000000, 20000000
    if value == "$20M+":
        return 20000000, float('inf')
    if value == "$1M - $5M":
        return 1000000, 5000000
    if value == "$250K - $1M":
        return 250000, 1000000
    if value == "$0 - $250K":
        return 0, 250000
    if value == "1 - 10":
        return 1, 9.99
    if value == "10 - 20":
        return 10, 19.99
    if value == "20 - 30":
        return 20, 29.99
    if value == "30 - 40":
        return 30, 40


def apply_contact_filters(query, email=None, phone=None, address=None):
    if email:
        if email.lower() == "has_email":
            query = query.filter(models.Investor.email.isnot(None), models.Investor.email != 'NaN')
        elif email.lower() == "no_email":
            query = query.filter(or_(models.Investor.email.is_(None), models.Investor.email == 'NaN'))

    if phone:
        if phone.lower() == "has_phone":
            query = query.filter(models.Investor.phone.isnot(None), models.Investor.phone != 'NaN')
        elif phone.lower() == "no_phone":
            query = query.filter(or_(models.Investor.phone.is_(None), models.Investor.phone == 'NaN'))

    if address:
        if address.lower() == "has_address":
            query = query.filter(models.Investor.address.isnot(None), models.Investor.address != 'NaN')
        elif address.lower() == "no_address":
            query = query.filter(or_(models.Investor.address.is_(None), models.Investor.address == 'NaN'))

    return query


@router.get("/search")
async def search_investors_get(
        search_term: Optional[str] = None,
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100),
        email: Optional[str] = Query(None),
        phone: Optional[str] = Query(None),
        address: Optional[str] = Query(None),
        cities: Optional[List[str]] = Query(None),
        states: Optional[List[str]] = Query(None),
        countries: Optional[List[str]] = Query(None),
        industries: Optional[List[str]] = Query(None),
        geographic_preferences: Optional[List[str]] = Query(None),
        fund_types: Optional[List[str]] = Query(None),
        stages: Optional[List[str]] = Query(None),
        assets_under_management: Optional[List[str]] = Query(None),
        minimum_investment: Optional[List[str]] = Query(None),
        maximum_investment: Optional[List[str]] = Query(None),
        title: Optional[List[str]] = Query(None),
        number_of_investors: Optional[List[str]] = Query(None),
        gender: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    try:
        query = db.query(models.Investor)

        if search_term:
            search = f"%{search_term}%"
            query = query.filter(
                models.Investor.first_name.ilike(search) |
                models.Investor.last_name.ilike(search) |
                models.Investor.firm_name.ilike(search)
            )

        query = apply_contact_filters(query, email, phone, address)

        if cities:
            query = query.filter(models.Investor.city.in_(cities))
        if gender:
            query = query.filter(models.Investor.gender == gender)
        if states:
            query = query.filter(models.Investor.state.in_(states))

        if countries:
            query = query.filter(models.Investor.country.in_(countries))

        if industries:
            query = query.filter(models.Investor.industry_preferences.overlap(industries))

        if fund_types:
            query = query.filter(models.Investor.type_of_firm.in_(fund_types))

        if stages:
            query = query.filter(models.Investor.stage_preferences.overlap(stages))

        if geographic_preferences:
            query = query.filter(models.Investor.geographic_preferences.overlap(geographic_preferences))

        if assets_under_management:
            conditions = []
            for range_value in assets_under_management:
                lower, upper = string_to_float(range_value)
                conditions.append(models.Investor.capital_managed.between(lower, upper))
            if conditions:
                query = query.filter(or_(*conditions))

        if minimum_investment:
            conditions = []
            for range_value in minimum_investment:
                lower, upper = string_to_float(range_value)
                conditions.append(models.Investor.min_investment.between(lower, upper))
            if conditions:
                query = query.filter(or_(*conditions))

        if maximum_investment:
            conditions = []
            for range_value in maximum_investment:
                lower, upper = string_to_float(range_value)
                conditions.append(models.Investor.max_investment.between(lower, upper))
            if conditions:
                query = query.filter(or_(*conditions))

        if title:
            query = query.filter(models.Investor.contact_title.in_(title if isinstance(title, list) else [title]))

        if number_of_investors:
            conditions = []
            for range_value in number_of_investors:
                try:
                    lower, upper = string_to_float(range_value)
                    conditions.append(
                        and_(
                            models.Investor.number_of_investors >= lower,
                            models.Investor.number_of_investors <= upper
                        )
                    )
                except Exception as e:
                    logger.error(f"Error parsing number_of_investors range: {e}")
                    continue
            if conditions:
                query = query.filter(or_(*conditions))

        total = query.count()
        skip = (page - 1) * per_page
        results = query.offset(skip).limit(per_page).all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": -(-total // per_page),
            "results": [crud.investor.to_dict(r) for r in results]
        }

    except Exception as e:
        logger.error(f"Error searching investors: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{investor_id}", response_model=None)
def read_investor(investor_id: int, db: Session = Depends(get_db)):
    try:
        db_investor = crud.investor.get(db, id=investor_id)
        if db_investor is None:
            raise HTTPException(status_code=404, detail="Investor not found")
        return db_investor
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{investor_id}", response_model=None)
def update_investor(investor_id: int, investor: schemas.InvestorCreate, db: Session = Depends(get_db)):
    try:
        db_investor = crud.investor.update(db, id=investor_id, obj_in=investor)
        if db_investor is None:
            raise HTTPException(status_code=404, detail="Investor not found")
        return db_investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{investor_id}", response_model=None)
def delete_investor(investor_id: int, db: Session = Depends(get_db)):
    try:
        db_investor = crud.investor.delete(db, id=investor_id)
        if db_investor is None:
            raise HTTPException(status_code=404, detail="Investor not found")
        return db_investor
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
