from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, cast, ARRAY, String
from sqlalchemy.orm import Session
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


@router.post("/search")
async def search_investors(
        filters: schemas.InvestorFilterParams,
        db: Session = Depends(get_db),
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100)
):
    try:
        query = db.query(models.Investor)

        # Basic text search
        if filters.searchTerm:
            search = f"%{filters.searchTerm}%"
            query = query.filter(or_(
                models.Investor.first_name.ilike(search),
                models.Investor.last_name.ilike(search),
                models.Investor.firm_name.ilike(search),
                models.Investor.contact_title.ilike(search)
            ))

        # Location filters
        if filters.location:
            if filters.location.city:
                query = query.filter(or_(*[
                    models.Investor.city.ilike(f"%{city}%")
                    for city in filters.location.city
                ]))
            if filters.location.state:
                query = query.filter(or_(*[
                    models.Investor.state.ilike(f"%{state}%")
                    for state in filters.location.state
                ]))
            if filters.location.country:
                query = query.filter(or_(*[
                    models.Investor.country.ilike(f"%{country}%")
                    for country in filters.location.country
                ]))
            if filters.location.location_preferences and len(filters.location.location_preferences) > 0:
                query = query.filter(
                    models.Investor.geographic_preferences.op('&&')(
                        cast(filters.location.location_preferences, ARRAY(String))
                    )
                )

        # Contact info filters
        if filters.contactInfo:
            if filters.contactInfo.hasEmail:
                query = query.filter(models.Investor.email.isnot(None))
            if filters.contactInfo.hasPhone:
                query = query.filter(models.Investor.phone.isnot(None))
            if filters.contactInfo.hasAddress:
                query = query.filter(models.Investor.city.isnot(None))

        # Industry preferences
        if filters.industry and filters.industry.industries:
            query = query.filter(
                models.Investor.industry_preferences.op('&&')(
                    cast(filters.industry.industries, ARRAY(String))
                )
            )

        # Fund type filter
        if filters.fundType and filters.fundType.types:
            query = query.filter(
                models.Investor.type_of_financing.in_(filters.fundType.types)
            )

        # Investment stages
        if filters.stages and filters.stages.stages:
            query = query.filter(
                models.Investor.stage_preferences.op('&&')(
                    cast(filters.stages.stages, ARRAY(String))
                )
            )

        # Investment ranges
        if filters.investmentRanges:
            from api.v1.dependencies import parse_investment_range

            if filters.investmentRanges.assetsUnderManagement:
                min_val, max_val = parse_investment_range(filters.investmentRanges.assetsUnderManagement)
                if min_val is not None:
                    query = query.filter(models.Investor.capital_managed >= min_val)
                if max_val is not None:
                    query = query.filter(models.Investor.capital_managed <= max_val)

            if filters.investmentRanges.minInvestment:
                min_val, max_val = parse_investment_range(filters.investmentRanges.minInvestment)
                if min_val is not None:
                    query = query.filter(models.Investor.min_investment >= min_val)
                if max_val is not None:
                    query = query.filter(models.Investor.min_investment <= max_val)

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
