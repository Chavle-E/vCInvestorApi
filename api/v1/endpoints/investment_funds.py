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
                (models.InvestmentFund.contact_email.isnot(None)) |
                (models.InvestmentFund.firm_email.isnot(None))
            )
        elif email == "no_email":
            query = query.filter(
                (models.InvestmentFund.contact_email.is_(None)) &
                (models.InvestmentFund.firm_email.is_(None))
            )

    if phone:
        if phone == "has_phone":
            query = query.filter(
                (models.InvestmentFund.contact_phone.isnot(None)) |
                (models.InvestmentFund.firm_phone.isnot(None))
            )
        elif phone == "no_phone":
            query = query.filter(
                (models.InvestmentFund.contact_phone.is_(None)) &
                (models.InvestmentFund.firm_phone.is_(None))
            )

    if address:
        if address == "has_address":
            query = query.filter(models.InvestmentFund.firm_address.isnot(None))
        elif address == "no_address":
            query = query.filter(models.InvestmentFund.firm_address.is_(None))

    return query


@router.get("/search")
async def search_funds_get(
        search_term: Optional[str] = None,
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100),
        email: Optional[str] = Query(None, enum=["has_email", "no_email"]),
        phone: Optional[str] = Query(None, enum=["has_phone", "no_phone"]),
        address: Optional[str] = Query(None, enum=["has_address", "no_address"]),
        cities: Optional[List[str]] = Query(None),
        states: Optional[List[str]] = Query(None),
        countries: Optional[List[str]] = Query(None),
        industries: Optional[List[str]] = Query(None),
        fund_types: Optional[List[str]] = Query(None),
        stages: Optional[List[str]] = Query(None),
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

        if industries:
            query = query.filter(models.InvestmentFund.industry_preferences.overlap(industries))

        if fund_types:
            query = query.filter(models.InvestmentFund.firm_type.in_(fund_types))

        if stages:
            query = query.filter(models.InvestmentFund.stage_preferences.overlap(stages))

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


def apply_fund_filters(query, filters):
    """Apply filters to investment fund query"""
    if not filters:
        return query

    if filters.searchTerm:
        search = f"%{filters.searchTerm}%"
        query = query.filter(models.InvestmentFund.firm_name.ilike(search) |
                             models.InvestmentFund.contact_email.ilike(search) |
                             models.InvestmentFund.firm_email.ilike(search) |
                             models.InvestmentFund.description.ilike(search))

    if filters.contactInfo:
        if filters.contactInfo.hasEmail is not None:
            if filters.contactInfo.hasEmail:
                query = query.filter(
                    (models.InvestmentFund.contact_email.isnot(None)) |
                    (models.InvestmentFund.firm_email.isnot(None))
                )
            else:
                query = query.filter(
                    (models.InvestmentFund.contact_email.is_(None)) &
                    (models.InvestmentFund.firm_email.is_(None))
                )

        if filters.contactInfo.hasPhone is not None:
            if filters.contactInfo.hasPhone:
                query = query.filter(
                    (models.InvestmentFund.contact_phone.isnot(None)) |
                    (models.InvestmentFund.firm_phone.isnot(None))
                )
            else:
                query = query.filter(
                    (models.InvestmentFund.contact_phone.is_(None)) &
                    (models.InvestmentFund.firm_phone.is_(None))
                )

        if filters.contactInfo.hasAddress is not None:
            if filters.contactInfo.hasAddress:
                query = query.filter(models.InvestmentFund.firm_address.isnot(None))
            else:
                query = query.filter(models.InvestmentFund.firm_address.is_(None))

    if filters.location:
        if filters.location.city:
            query = query.filter(models.InvestmentFund.firm_city.in_(filters.location.city))
        if filters.location.state:
            query = query.filter(models.InvestmentFund.firm_state.in_(filters.location.state))
        if filters.location.country:
            query = query.filter(models.InvestmentFund.firm_country.in_(filters.location.country))
        if filters.location.location_preferences:
            query = query.filter(models.InvestmentFund.geographic_preferences.overlap(
                filters.location.location_preferences
            ))

    if filters.industry and filters.industry.industries:
        query = query.filter(models.InvestmentFund.industry_preferences.overlap(
            filters.industry.industries
        ))

    if filters.stages and filters.stages.stages:
        query = query.filter(models.InvestmentFund.stage_preferences.overlap(
            filters.stages.stages
        ))

    if filters.fundType and filters.fundType.types:
        query = query.filter(models.InvestmentFund.firm_type.in_(filters.fundType.types))

    return query