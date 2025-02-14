from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
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


def string_to_float(value: str) -> tuple[float, float]:
    if not value:
        return 0, float('inf')

    ranges = {

        "$1B+": (1_000_000_000, float('inf')),


        "$100M - $500M": (100_000_000, 500_000_000),
        "$500M - $1B": (500_000_000, 1_000_000_000),
        "$25M - $100M": (25_000_000, 100_000_000),
        "$0 - $25M": (1, 25_000_000),
        "$10M - $25M": (10_000_000, 25_000_000),
        "$100M+": (100_000_000, float('inf')),
        "$1M - $10M": (1_000_000, 10_000_000),
        "$0 - $1M": (1, 1_000_000),
        "$5M - $20M": (5_000_000, 20_000_000),
        "$20M+": (20_000_000, float('inf')),
        "$1M - $5M": (1_000_000, 5_000_000),


        "$250K - $1M": (250_000, 1_000_000),
        "$0 - $250K": (0, 250_000),


        "1 - 10": (1, 9.99),
        "10 - 20": (10, 19.99),
        "20 - 30": (20, 29.99),
        "30 - 40": (30, 40)
    }

    return ranges.get(value, (0, float('inf')))


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
        assets_under_management: Optional[List[str]] = Query(None),
        minimum_investment: Optional[List[str]] = Query(None),
        maximum_investment: Optional[List[str]] = Query(None),
        number_of_investors: Optional[List[str]] = Query(None),
        gender_ratio: Optional[List[str]] = Query(None),
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

        query = apply_contact_filters(query, email, phone, address)

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
            conditions = []
            for range_value in assets_under_management:
                lower, upper = string_to_float(range_value)
                conditions.append(
                    and_(
                        models.InvestmentFund.capital_managed >= lower,
                        models.InvestmentFund.capital_managed <= upper
                    )
                )
            if conditions:
                query = query.filter(or_(*conditions))

        if minimum_investment:
            conditions = []
            for range_value in minimum_investment:
                lower, upper = string_to_float(range_value)
                conditions.append(
                    and_(
                        models.InvestmentFund.min_investment >= lower,
                        models.InvestmentFund.min_investment <= upper
                    )
                )
            if conditions:
                query = query.filter(or_(*conditions))
        if maximum_investment:
            conditions = []
            for range_value in maximum_investment:
                lower, upper = string_to_float(range_value)
                conditions.append(
                    and_(
                        models.InvestmentFund.max_investment >= lower,
                        models.InvestmentFund.max_investment <= upper
                    )
                )
            if conditions:
                query = query.filter(or_(*conditions))
        if number_of_investors:
            conditions = []
            for range_value in number_of_investors:
                try:
                    lower, upper = string_to_float(range_value)
                    conditions.append(
                        and_(
                            models.InvestmentFund.number_of_investors >= lower,
                            models.InvestmentFund.number_of_investors <= upper
                        )
                    )
                except Exception as e:
                    logger.error(f"Error parsing number_of_investors range: {e}")
                    continue
            if conditions:
                query = query.filter(or_(*conditions))
        if gender_ratio:
            gender_ratios = gender_ratio if isinstance(gender_ratio, list) else [gender_ratio]
            query = query.filter(models.InvestmentFund.gender_ratio.in_(gender_ratios))

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


