from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict
import models
from database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
def get_database_stats(db: Session = Depends(get_db)) -> Dict:
    """Get database statistics"""
    try:
        total_investors = db.query(models.Investor).count()
        total_funds = db.query(models.InvestmentFund).count()
        return {
            "total_investors": total_investors,
            "total_investment_funds": total_funds
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-pagination")
def test_pagination(
        db: Session = Depends(get_db),
        page: int = Query(1, gt=0),
        per_page: int = Query(100, gt=0, le=500)
):
    """Test Pagination with metrics"""
    try:
        skip = (page - 1) * per_page

        # Get Investors
        total_investors = db.query(models.Investor).count()
        investors = db.query(models.Investor).offset(skip).limit(per_page).all()

        # Get Investment Funds
        total_funds = db.query(models.InvestmentFund).count()
        funds = db.query(models.InvestmentFund).offset(skip).limit(per_page).all()

        return {
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_investors": total_investors,
                "total_funds": total_funds,
                "total_pages_investors": -(-total_investors // per_page),
                "total_pages_funds": -(-total_funds // per_page),
            },
            "current_page_data": {
                "investor_count": len(investors),
                "funds_count": len(funds),
                "skip": skip,
                "investors_sample": [{"id": inv.id, "email": inv.email} for inv in investors[:5]],
                "funds_sample": [{"id": fund.id, "name": fund.firm_name} for fund in funds[:5]]
            }
        }
    except Exception as e:
        logger.error(f"Error in test-pagination: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
