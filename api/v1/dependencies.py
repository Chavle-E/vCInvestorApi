from typing import Optional, Tuple


def parse_investment_range(range_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Convert string investment range to numeric min/max values"""
    if not range_str:
        return None, None

    ranges = {
        # Assets Under Management
        "1B_PLUS": (1_000_000_000, None),
        "100M_500M": (100_000_000, 500_000_000),
        "500M_1B": (500_000_000, 1_000_000_000),
        "25M_100M": (25_000_000, 100_000_000),
        "0_25M": (0, 25_000_000),

        # Min Investment
        "25K_250K": (25_000, 250_000),
        "250K_1M": (250_000, 1_000_000),
        "1M_5M": (1_000_000, 5_000_000),
        "5M_PLUS": (5_000_000, None),

        # Max Investment
        "25M_150M": (25_000_000, 150_000_000),
        "10M_25M": (10_000_000, 25_000_000),
        "1M_10M": (1_000_000, 10_000_000),
        "150M_PLUS": (150_000_000, None)
    }

    return ranges.get(range_str, (None, None))