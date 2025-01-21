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
        # Get total count
        total = db.query(models.InvestmentFund).count()

        # Calculate skip
        skip = (page - 1) * per_page

        # Get paginated results
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
            "data": funds
        }
    except Exception as e:
        logger.error(f"Error fetching funds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_funds_get(
        # Search and pagination
        search_term: Optional[str] = None,
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100),

        # Location filters
        cities: Optional[List[str]] = Query(None),
        states: Optional[List[str]] = Query(None),
        countries: Optional[List[str]] = Query(None),
        location_preferences: Optional[List[str]] = Query(None),

        # Contact info filters
        has_email: Optional[bool] = Query(None),
        has_phone: Optional[bool] = Query(None),
        has_address: Optional[bool] = Query(None),

        # Industry filters
        industries: Optional[List[str]] = Query(None),

        # Fund type filters
        fund_types: Optional[List[str]] = Query(None),

        # Stage filters
        stages: Optional[List[str]] = Query(None),

        # Investment range filters
        assets_under_management: Optional[str] = Query(None),
        min_investment: Optional[str] = Query(None),
        max_investment: Optional[str] = Query(None),

        db: Session = Depends(get_db)
):
    """
    Search investment funds using query parameters instead of POST body
    """
    # Construct filter object from query parameters
    filters = schemas.InvestmentFundFilterParams(
        searchTerm=search_term,
        location=schemas.LocationFilter(
            city=cities,
            state=states,
            country=countries,
            location_preferences=location_preferences
        ) if any([cities, states, countries, location_preferences]) else None,
        contactInfo=schemas.ContactInfoFilter(
            hasEmail=has_email,
            hasPhone=has_phone,
            hasAddress=has_address
        ) if any([has_email, has_phone, has_address]) else None,
        industry=schemas.IndustryFilter(
            industries=industries
        ) if industries else None,
        fundType=schemas.FundTypeFilter(
            types=fund_types
        ) if fund_types else None,
        stages=schemas.StagePreferencesFilter(
            stages=stages
        ) if stages else None,
        investmentRanges=schemas.InvestmentRangesFilter(
            assetsUnderManagement=assets_under_management,
            minInvestment=min_investment,
            maxInvestment=max_investment
        ) if any([assets_under_management, min_investment, max_investment]) else None
    )

    try:
        query = db.query(models.InvestmentFund)

        # Apply filters using existing function
        query = apply_fund_filters(query, filters)

        # Calculate pagination
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
                             models.InvestmentFund.full_name.ilike(search) |
                             models.InvestmentFund.firm_email.ilike(search) |
                             models.InvestmentFund.contact_email.ilike(search) |
                             models.InvestmentFund.description.ilike(search))

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
