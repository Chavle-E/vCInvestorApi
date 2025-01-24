from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    return value.title().replace('_', ' ')


def apply_contact_filters(query, email=None, phone=None, address=None):
    if email:
        if email == "has_email":
            query = query.filter(models.Investor.email.isnot(None))
        elif email == "no_email":
            query = query.filter(models.Investor.email.is_(None))

    if phone:
        if phone == "has_phone":
            query = query.filter(models.Investor.phone.isnot(None))
        elif phone == "no_phone":
            query = query.filter(models.Investor.phone.is_(None))

    if address:
        if address == "has_address":
            query = query.filter(models.Investor.address.isnot(None))
        elif address == "no_address":
            query = query.filter(models.Investor.address.is_(None))

    return query


@router.get("/search")
async def search_investors_get(
        search_term: Optional[str] = None,
        page: int = Query(1, gt=0),
        per_page: int = Query(50, gt=1, le=100),
        email: Optional[str] = Query(None, enum=["has_email", "no_email"]),
        phone: Optional[str] = Query(None, enum=["has_phone", "no_phone"]),
        address: Optional[str] = Query(None, enum=["has_address", "no_address"]),
        cities: Optional[str] = Query(None),
        states: Optional[str] = Query(None),
        countries: Optional[str] = Query(None),
        industries: Optional[Union[str, List[str]]] = Query(None),
        fund_types: Optional[str] = Query(None),
        stages: Optional[str] = Query(None),
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
                models.Investor.firm_name.ilike(search) |
                models.Investor.email.ilike(search)
            )

        query = apply_contact_filters(query, email, phone, address)

        if cities:
            normalized_city = normalize_enum_value(cities)
            query = query.filter(models.Investor.city == normalized_city)

        if states:
            normalized_state = normalize_enum_value(states)
            query = query.filter(models.Investor.state == normalized_state)

        if countries:
            normalized_country = normalize_enum_value(countries)
            query = query.filter(models.Investor.country == normalized_country)

        if industries:
            query = query.filter(models.Investor.industry_preferences.overlap([industries]))

        if fund_types:
            fund_type_list = fund_types.split(',') if ',' in fund_types else [fund_types]
            normalized_fund_types = [normalize_enum_value(ft) for ft in fund_type_list]
            query = query.filter(models.Investor.type_of_financing.overlap(normalized_fund_types))
        if stages:
            query = query.filter(models.Investor.stage_preferences.overlap([stages]))

        if gender:
            normalized_gender = normalize_enum_value(gender)
            query = query.filter(models.Investor.gender == normalized_gender)

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

    if filters.contactInfo:
        if filters.contactInfo.hasEmail is not None:
            if filters.contactInfo.hasEmail:
                query = query.filter(models.Investor.email.isnot(None))
            else:
                query = query.filter(models.Investor.email.is_(None))

        if filters.contactInfo.hasPhone is not None:
            if filters.contactInfo.hasPhone:
                query = query.filter(models.Investor.phone.isnot(None))
            else:
                query = query.filter(models.Investor.phone.is_(None))

        if filters.contactInfo.hasAddress is not None:
            if filters.contactInfo.hasAddress:
                query = query.filter(models.Investor.address.isnot(None))
            else:
                query = query.filter(models.Investor.address.is_(None))

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
