from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, cast, ARRAY, String, func, text
from sqlalchemy.sql import expression
from sqlalchemy.orm import Session
from typing import List, Dict
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


@router.post("/search")
async def search_funds(
        filters: schemas.InvestmentFundFilterParams,
        db: Session = Depends(get_db),
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100)
):
    try:
        query = db.query(models.InvestmentFund)

        # Basic text search
        if filters.searchTerm:
            search = f"%{filters.searchTerm}%"
            query = query.filter(or_(
                models.InvestmentFund.firm_name.ilike(search),
                models.InvestmentFund.full_name.ilike(search),
                models.InvestmentFund.firm_email.ilike(search),
                models.InvestmentFund.contact_email.ilike(search),
                models.InvestmentFund.description.ilike(search)
            ))

        # Location filters
        if filters.location:
            if filters.location.city:
                query = query.filter(or_(*[
                    models.InvestmentFund.firm_city.ilike(f"%{city}%")
                    for city in filters.location.city
                ]))
            if filters.location.state:
                query = query.filter(or_(*[
                    models.InvestmentFund.firm_state.ilike(f"%{state}%")
                    for state in filters.location.state
                ]))
            if filters.location.country:
                query = query.filter(or_(*[
                    models.InvestmentFund.firm_country.ilike(f"%{country}%")
                    for country in filters.location.country
                ]))
            if filters.location.location_preferences and len(filters.location.location_preferences) > 0:
                query = query.filter(
                    models.InvestmentFund.geographic_preferences.op('&&')(
                        cast(filters.location.location_preferences, ARRAY(String))
                    )
                )

        # Contact info filters
        if filters.contactInfo:
            if filters.contactInfo.hasEmail:
                query = query.filter(or_(
                    models.InvestmentFund.firm_email.isnot(None),
                    models.InvestmentFund.contact_email.isnot(None)
                ))
            if filters.contactInfo.hasPhone:
                query = query.filter(or_(
                    models.InvestmentFund.firm_phone.isnot(None),
                    models.InvestmentFund.contact_phone.isnot(None)
                ))
            if filters.contactInfo.hasAddress:
                query = query.filter(and_(
                    models.InvestmentFund.firm_address.isnot(None),
                    models.InvestmentFund.firm_city.isnot(None)
                ))

        # Industry filters
        if filters.industry and filters.industry.industries:
            query = query.filter(
                models.InvestmentFund.industry_preferences.op('&&')(
                    cast(filters.industry.industries, ARRAY(String))
                )
            )
        # Fund type filter
        if filters.fundType and filters.fundType.types:
            query = query.filter(or_(*[
                or_(
                    models.InvestmentFund.firm_type.ilike(f"%{t}%"),
                    models.InvestmentFund.financing_type.ilike(f"%{t}%")
                ) for t in filters.fundType.types
            ]))

        # Investment stages
        if filters.stages and filters.stages.stages:
            query = query.filter(
                models.InvestmentFund.stage_preferences.op('&&')(
                    cast(filters.stages.stages, ARRAY(String))
                )
            )

        # Investment ranges
        if filters.investmentRanges:
            from api.v1.dependencies import parse_investment_range

            if filters.investmentRanges.assetsUnderManagement:
                min_val, max_val = parse_investment_range(filters.investmentRanges.assetsUnderManagement)
                if min_val is not None:
                    query = query.filter(models.InvestmentFund.capital_managed >= min_val)
                if max_val is not None:
                    query = query.filter(models.InvestmentFund.capital_managed <= max_val)

            if filters.investmentRanges.minInvestment:
                min_val, max_val = parse_investment_range(filters.investmentRanges.minInvestment)
                if min_val is not None:
                    query = query.filter(models.InvestmentFund.min_investment >= min_val)
                if max_val is not None:
                    query = query.filter(models.InvestmentFund.min_investment <= max_val)

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
