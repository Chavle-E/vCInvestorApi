from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
import crud
import logging
from typing import Optional, List

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
        # Get Total Count
        total = db.query(models.Investor).count()

        # Calculate Offset
        skip = (page - 1) * per_page

        # Get paginated results
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
            "data": investors,
        }
    except Exception as e:
        logger.error(f"Error fetching investors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_investors_get(
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

        # Gender filter
        gender: Optional[str] = Query(None),

        db: Session = Depends(get_db)
):
    """
    Search investors using query parameters instead of POST body
    """
    # Construct filter object from query parameters
    filters = schemas.InvestorFilterParams(
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
        ) if any([assets_under_management, min_investment, max_investment]) else None,
        gender=schemas.GenderFilter(
            gender=gender
        ) if gender else None
    )

    try:
        query = db.query(models.Investor)

        # Apply filters using existing function
        query = apply_investor_filters(query, filters)

        # Calculate pagination
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


@router.get("/{investor_id}", response_model=None)  # Remove response model
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


def apply_investor_filters(query, filters):
    """Apply filters to investor query"""
    if not filters:
        return query

    if filters.searchTerm:
        search = f"%{filters.searchTerm}%"
        query = query.filter(models.Investor.first_name.ilike(search) |
                             models.Investor.last_name.ilike(search) |
                             models.Investor.firm_name.ilike(search) |
                             models.Investor.email.ilike(search) |
                             models.Investor.contact_title.ilike(search))

    if filters.location:
        if filters.location.city:
            query = query.filter(models.Investor.city.in_(filters.location.city))
        if filters.location.state:
            query = query.filter(models.Investor.state.in_(filters.location.state))
        if filters.location.country:
            query = query.filter(models.Investor.country.in_(filters.location.country))
        if filters.location.location_preferences:
            query = query.filter(models.Investor.geographic_preferences.overlap(
                filters.location.location_preferences
            ))

    if filters.industry and filters.industry.industries:
        query = query.filter(models.Investor.industry_preferences.overlap(
            filters.industry.industries
        ))

    if filters.stages and filters.stages.stages:
        query = query.filter(models.Investor.stage_preferences.overlap(
            filters.stages.stages
        ))

    if filters.fundType and filters.fundType.types:
        query = query.filter(models.Investor.type_of_financing.in_(filters.fundType.types))

    if filters.gender and filters.gender.gender:
        query = query.filter(models.Investor.gender == filters.gender.gender)

    return query
