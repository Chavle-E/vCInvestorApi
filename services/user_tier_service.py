import logging

logger = logging.getLogger(__name__)

# Default rate limits per tier (requests per day)
TIER_RATE_LIMITS = {
    "free": 100,
    "basic": 1000,
    "professional": 5000,
    "enterprise": 10000,
    "admin": 50000
}


def get_user_tier(user, db=None):
    """
    Determine a user's tier based on simple rules (without Paddle integration).

    Args:
        user: User model instance
        db: Database session (not used in this simplified version)

    Returns:
        str: User tier ('free', 'basic', 'professional', 'enterprise', or 'admin')
    """
    # Admin check - simple domain-based rule
    if hasattr(user, 'email') and user.email:
        if '@yourcompany.com' in user.email:
            return "admin"

    # For now, everyone else is on basic tier
    # Later, you'll replace this with Paddle subscription logic
    return "basic"


def get_rate_limit_for_tier(tier):
    """Get the rate limit (requests per day) for a given tier"""
    return TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["free"])