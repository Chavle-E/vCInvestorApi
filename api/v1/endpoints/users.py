# api/v1/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
import logging
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current user profile and usage stats"""
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Calculate searches remaining
        searches_remaining = None if user.monthly_search_limit == -1 else \
            max(0, user.monthly_search_limit - user.monthly_searches)

        return {
            "id": user.id,
            "email": user.email,
            "subscription": {
                "tier": user.subscription_tier,
                "status": user.subscription_status,
                "end_date": user.subscription_end,
            },
            "features": {
                "can_export": user.can_export,
                "can_see_full_profiles": user.can_see_full_profiles,
                "can_see_contact_info": user.can_see_contact_info
            },
            "usage": {
                "monthly_searches": user.monthly_searches,
                "total_searches": user.total_searches,
                "searches_remaining": searches_remaining,
                "search_limit": user.monthly_search_limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/subscription")
async def update_subscription(
        request: Request,
        new_tier: str,
        db: Session = Depends(get_db)
):
    """Update user's subscription tier - called from your frontend when subscription changes"""
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update subscription
        from middleware.auth import SUBSCRIPTION_LIMITS
        if new_tier not in SUBSCRIPTION_LIMITS:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")

        # Apply new limits
        limits = SUBSCRIPTION_LIMITS[new_tier]
        user.subscription_tier = new_tier
        user.monthly_search_limit = limits["monthly_searches"]
        user.can_export = limits["can_export"]
        user.can_see_full_profiles = limits["can_see_full_profiles"]
        user.can_see_contact_info = limits["can_see_contact_info"]

        db.commit()

        return {"status": "success", "tier": new_tier}

    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-usage")
async def reset_usage_stats(request: Request, db: Session = Depends(get_db)):
    """Reset monthly usage counters - typically called by a CRON job"""
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.monthly_searches = 0
        user.last_search = datetime.now(timezone.utc)
        db.commit()

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error resetting usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
