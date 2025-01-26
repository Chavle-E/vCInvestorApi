# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy import func
# from sqlalchemy.orm import Session
# from typing import Optional, List
# from database import get_db
# import models
# import schemas
# import logging
#
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
#
#
# @router.post("/investors")
# async def get_investor_filter_counts(
#         filters: Optional[schemas.InvestorFilterParams] = None,
#         exclude_fields: List[str] = Query(default=[]),
#         db: Session = Depends(get_db)
# ):
#     """Get counts for each filter option based on current filter selections"""
#     try:
#         # Start with base query
#         base_query = db.query(models.Investor)
#
#         # Apply filters if provided
#         if filters:
#             base_query = apply_investor_filters(base_query, filters)
#
#         counts = {}
#
#         # Location counts
#         if "location" not in exclude_fields:
#             # Cities
#             city_counts = (
#                 base_query
#                 .with_entities(models.Investor.city, func.count(models.Investor.id))
#                 .filter(models.Investor.city.isnot(None))
#                 .group_by(models.Investor.city)
#                 .all()
#             )
#             counts["cities"] = {city: count for city, count in city_counts if city}
#
#             # States
#             state_counts = (
#                 base_query
#                 .with_entities(models.Investor.state, func.count(models.Investor.id))
#                 .filter(models.Investor.state.isnot(None))
#                 .group_by(models.Investor.state)
#                 .all()
#             )
#             counts["states"] = {state: count for state, count in state_counts if state}
#
#             # Countries
#             country_counts = (
#                 base_query
#                 .with_entities(models.Investor.country, func.count(models.Investor.id))
#                 .filter(models.Investor.country.isnot(None))
#                 .group_by(models.Investor.country)
#                 .all()
#             )
#             counts["countries"] = {country: count for country, count in country_counts if country}
#
#         # Industry preferences
#         if "industry" not in exclude_fields:
#             industry_counts = (
#                 base_query
#                 .with_entities(
#                     func.unnest(models.Investor.industry_preferences).label('industry'),
#                     func.count(models.Investor.id)
#                 )
#                 .filter(models.Investor.industry_preferences.isnot(None))
#                 .group_by('industry')
#                 .all()
#             )
#             counts["industries"] = {ind: count for ind, count in industry_counts if ind}
#
#         # Stage preferences
#         if "stages" not in exclude_fields:
#             stage_counts = (
#                 base_query
#                 .with_entities(
#                     func.unnest(models.Investor.stage_preferences).label('stage'),
#                     func.count(models.Investor.id)
#                 )
#                 .filter(models.Investor.stage_preferences.isnot(None))
#                 .group_by('stage')
#                 .all()
#             )
#             counts["stages"] = {stage: count for stage, count in stage_counts if stage}
#
#         # Fund types
#         if "fundType" not in exclude_fields:
#             fund_type_counts = (
#                 base_query
#                 .with_entities(models.Investor.type_of_financing, func.count(models.Investor.id))
#                 .filter(models.Investor.type_of_financing.isnot(None))
#                 .group_by(models.Investor.type_of_financing)
#                 .all()
#             )
#             counts["fundTypes"] = {ft: count for ft, count in fund_type_counts if ft}
#
#         # Gender
#         if "gender" not in exclude_fields:
#             gender_counts = (
#                 base_query
#                 .with_entities(models.Investor.gender, func.count(models.Investor.id))
#                 .filter(models.Investor.gender.isnot(None))
#                 .group_by(models.Investor.gender)
#                 .all()
#             )
#             counts["genders"] = {gender: count for gender, count in gender_counts if gender}
#
#         return counts
#
#     except Exception as e:
#         logger.error(f"Error getting investor filter counts: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/funds")
# async def get_fund_filter_counts(
#         filters: Optional[schemas.InvestmentFundFilterParams] = None,
#         exclude_fields: List[str] = Query(default=[]),
#         db: Session = Depends(get_db)
# ):
#     """Get counts for each filter option based on current filter selections"""
#     try:
#         # Start with base query
#         base_query = db.query(models.InvestmentFund)
#
#         # Apply filters if provided
#         if filters:
#             base_query = apply_fund_filters(base_query, filters)
#
#         counts = {}
#
#         # Location counts
#         if "location" not in exclude_fields:
#             # Cities
#             city_counts = (
#                 base_query
#                 .with_entities(models.InvestmentFund.firm_city, func.count(models.InvestmentFund.id))
#                 .filter(models.InvestmentFund.firm_city.isnot(None))
#                 .group_by(models.InvestmentFund.firm_city)
#                 .all()
#             )
#             counts["cities"] = {city: count for city, count in city_counts if city}
#
#             # States
#             state_counts = (
#                 base_query
#                 .with_entities(models.InvestmentFund.firm_state, func.count(models.InvestmentFund.id))
#                 .filter(models.InvestmentFund.firm_state.isnot(None))
#                 .group_by(models.InvestmentFund.firm_state)
#                 .all()
#             )
#             counts["states"] = {state: count for state, count in state_counts if state}
#
#             # Countries
#             country_counts = (
#                 base_query
#                 .with_entities(models.InvestmentFund.firm_country, func.count(models.InvestmentFund.id))
#                 .filter(models.InvestmentFund.firm_country.isnot(None))
#                 .group_by(models.InvestmentFund.firm_country)
#                 .all()
#             )
#             counts["countries"] = {country: count for country, count in country_counts if country}
#
#         # Industry preferences
#         if "industry" not in exclude_fields:
#             industry_counts = (
#                 base_query
#                 .with_entities(
#                     func.unnest(models.InvestmentFund.industry_preferences).label('industry'),
#                     func.count(models.InvestmentFund.id)
#                 )
#                 .filter(models.InvestmentFund.industry_preferences.isnot(None))
#                 .group_by('industry')
#                 .all()
#             )
#             counts["industries"] = {ind: count for ind, count in industry_counts if ind}
#
#         # Stage preferences
#         if "stages" not in exclude_fields:
#             stage_counts = (
#                 base_query
#                 .with_entities(
#                     func.unnest(models.InvestmentFund.stage_preferences).label('stage'),
#                     func.count(models.InvestmentFund.id)
#                 )
#                 .filter(models.InvestmentFund.stage_preferences.isnot(None))
#                 .group_by('stage')
#                 .all()
#             )
#             counts["stages"] = {stage: count for stage, count in stage_counts if stage}
#
#         # Fund types
#         if "fundType" not in exclude_fields:
#             fund_type_counts = (
#                 base_query
#                 .with_entities(models.InvestmentFund.firm_type, func.count(models.InvestmentFund.id))
#                 .filter(models.InvestmentFund.firm_type.isnot(None))
#                 .group_by(models.InvestmentFund.firm_type)
#                 .all()
#             )
#             counts["fundTypes"] = {ft: count for ft, count in fund_type_counts if ft}
#
#         return counts
#
#     except Exception as e:
#         logger.error(f"Error getting fund filter counts: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))