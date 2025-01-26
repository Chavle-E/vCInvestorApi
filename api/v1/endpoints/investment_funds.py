from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import models
import schemas
from database import get_db
import crud
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=None)
def create_fund(fund: schemas.InvestmentFundCreate, db: Session = Depends(get_db)):
    try:
        return crud.investment_fund.create(db=db, obj_in=fund)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=None)
def read_funds(
        db: Session = Depends(get_db),
        page: int = Query(1, gt=0, description="Page number"),
        per_page: int = Query(50, gt=0, le=100, description="Items per page")
):
    try:
        total = db.query(models.InvestmentFund).count()
        skip = (page - 1) * per_page
        funds = crud.investment_fund.get_multi(
            db=db,
            skip=skip,
            limit=per_page
        )
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": -(-total // per_page),
            "results": funds
        }
    except Exception as e:
        logger.error(f"Error fetching funds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def apply_fund_contact_filters(query, email=None, phone=None, address=None):
    if email:
        if email == "has_email":
            query = query.filter(
                (models.InvestmentFund.firm_email != 'NaN')
            )
        elif email == "no_email":
            query = query.filter(
                (models.InvestmentFund.firm_email == 'NaN')
            )

    if phone:
        if phone == "has_phone":
            query = query.filter(
                (models.InvestmentFund.firm_phone != 'NaN')
            )
        elif phone == "no_phone":
            query = query.filter(
                (models.InvestmentFund.firm_phone == 'NaN')
            )

    if address:
        if address == "has_address":
            query = query.filter(models.InvestmentFund.firm_address != 'NaN')
        elif address == "no_address":
            query = query.filter(models.InvestmentFund.firm_address == 'NaN')

    return query


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


@router.get("/search")
async def search_funds_get(
        search_term: Optional[str] = None,
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100),
        email: Optional[str] = Query(None),
        phone: Optional[str] = Query(None),
        address: Optional[str] = Query(None),
        cities: Optional[List[str]] = Query(None),
        states: Optional[List[str]] = Query(None),
        countries: Optional[List[str]] = Query(None),
        location_preferences: Optional[list[str]] = Query(None),
        industries: Optional[List[str]] = Query(None),
        fund_types: Optional[List[str]] = Query(None),
        stages: Optional[List[str]] = Query(None),
        assets_under_management: Optional[str] = Query(None),
        minimum_investment: Optional[str] = Query(None),
        maximum_investment: Optional[str] = Query(None),
        number_of_investors: Optional[str] = Query(None),
        gender_ratio: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """Search investment funds using query parameters"""
    try:
        query = db.query(models.InvestmentFund)

        if search_term:
            search = f"%{search_term}%"
            query = query.filter(
                models.InvestmentFund.firm_name.ilike(search) |
                models.InvestmentFund.contact_email.ilike(search) |
                models.InvestmentFund.firm_email.ilike(search)
            )

        query = apply_fund_contact_filters(query, email, phone, address)

        if cities:
            query = query.filter(models.InvestmentFund.firm_city.in_(cities))
        if states:
            query = query.filter(models.InvestmentFund.firm_state.in_(states))
        if countries:
            query = query.filter(models.InvestmentFund.firm_country.in_(countries))
        if location_preferences:
            query = query.filter(models.InvestmentFund.geographic_preferences.overlap([location_preferences]))
        if industries:
            query = query.filter(models.InvestmentFund.industry_preferences.overlap(industries))

        if fund_types:
            query = query.filter(models.InvestmentFund.firm_type.in_(fund_types))

        if stages:
            query = query.filter(models.InvestmentFund.stage_preferences.overlap(stages))
        if assets_under_management:
            lower, upper = string_to_float(assets_under_management)
            query = query.filter(models.InvestmentFund.capital_managed.between(lower, upper))
        if minimum_investment:
            lower, upper = string_to_float(minimum_investment)
            query = query.filter(models.InvestmentFund.min_investment.between(lower, upper))
        if maximum_investment:
            lower, upper = string_to_float(maximum_investment)
            query = query.filter(models.InvestmentFund.max_investment.between(lower, upper))
        if number_of_investors:
            lower, upper = string_to_float(number_of_investors)
            query = query.filter(models.InvestmentFund.number_of_investors.between(lower, upper))
        total = query.count()
        skip = (page - 1) * per_page
        results = query.offset(skip).limit(per_page).all()

        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": -(-total // per_page),
            "results": [crud.investment_fund.to_dict(r) for r in results]
        }

    except Exception as e:
        logger.error(f"Error searching investment funds: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fund_id}", response_model=None)
def read_fund(fund_id: int, db: Session = Depends(get_db)):
    try:
        db_fund = crud.investment_fund.get(db, id=fund_id)
        if db_fund is None:
            raise HTTPException(status_code=404, detail="Investment Fund not found")
        return db_fund
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{fund_id}", response_model=None)
def update_fund(fund_id: int, fund: schemas.InvestmentFundCreate, db: Session = Depends(get_db)):
    try:
        db_fund = crud.investment_fund.update(db, id=fund_id, obj_in=fund)
        if db_fund is None:
            raise HTTPException(status_code=404, detail="Investment Fund not found")
        return db_fund
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{fund_id}", response_model=None)
def delete_fund(fund_id: int, db: Session = Depends(get_db)):
    try:
        db_fund = crud.investment_fund.delete(db, id=fund_id)
        if db_fund is None:
            raise HTTPException(status_code=404, detail="Investment Fund not found")
        return db_fund
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


