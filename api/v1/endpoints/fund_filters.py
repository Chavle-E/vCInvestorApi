from fastapi import APIRouter
import schemas
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Investment Fund Filter Values
@router.get('/investment-funds/email')
def return_email():
    return {
        "email": [
            {
                "label": "Has Email",
                "value": "has_email"
            },
            {
                "label": "No Email",
                "value": "no_email"
            }
        ]

    }


@router.get('/investment-funds/phone')
def return_phone():
    return {
        "phone": [
            {
                "label": "has_phone",
                "value": "has_phone"
            },
            {
                "label": "no_phone",
                "value": "no_phone"
            }
        ]

    }


@router.get('/investment-funds/address')
def return_address():
    return {
        "address": [
            {
                "label": "has_address",
                "value": "has_address"
            },
            {
                "label": "no_address",
                "value": "no_address"
            }
        ]

    }


@router.get('/investment-funds/cities')
def return_cities():
    return {
        "cities": [{
            "label": city.value, "value": city.value
        }
            for city in schemas.InvestmentFundCity
        ]
    }


@router.get('/investment-funds/states')
def return_states():
    return {
        "states": [{
            "label": state.value, "value": state.value
        }
            for state in schemas.InvestmentFundState
        ]
    }


@router.get('/investment-funds/countries')
def return_countries():
    return {
        "countries": [{
            "label": country.value, "value": country.value
        }
            for country in schemas.InvestmentFundCountry
        ]
    }


@router.get('/investment-funds/location-preferences')
def return_location_preferences():
    return {
        "location_preferences": [{
            "label": location.value, "value": location.value
        }
            for location in schemas.InvestmentFundLocationPreference
        ]
    }


@router.get('/investment-funds/industry-preferences')
def return_industry_preferences():
    return {
        "industry_preferences": [{
            "label": industry.value, "value": industry.value
        }
            for industry in schemas.InvestmentFundIndustryPreference
        ]
    }


@router.get('/investment-funds/fund-types')
def return_fund_types():
    return {
        "fund_types": [{
            "label": fund_type.value, "value": fund_type.value
        }
            for fund_type in schemas.InvestmentFundType
        ]
    }


@router.get('/investment-funds/stage-preferences')
def return_stage_preferences():
    return {
        "stage_preferences": [{
            "label": stage.value, "value": stage.value
        }
            for stage in schemas.InvestmentFundStagePreference
        ]
    }


@router.get('/investment-funds/assets-under-management')
def return_assets_under_management():
    return {
        "assets_under_management": [{
            "label": asset.value, "value": asset.value
        }
            for asset in schemas.InvestmentFundAssetsUnderManagement
        ]
    }


@router.get('/investment-funds/min-investment')
def return_min_investment():
    return {
        "minimum_investment": [{
            "label": investment.value, "value": investment.value
        }
            for investment in schemas.InvestmentFundMinInvestment
        ]
    }


@router.get('/investment-funds/max-investment')
def return_max_investment():
    return {
        "maximum_investment": [{
            "label": investment.value, "value": investment.value
        }
            for investment in schemas.InvestmentFundMaxInvestment
        ]
    }


@router.get('/investment-funds/number-of-investors')
def return_number_of_investors():
    return {
        "number_of_investors": [{
            "label": number.value, "value": number.value
        }
            for number in schemas.InvestmentFundNumberOfInvestors
        ]
    }


@router.get('/investment-funds/gender-ratio')
def return_gender_ratio():
    return {
        "gender_ratio": [{
            "label": gender.value, "value": gender.value
        }
            for gender in schemas.InvestmentFundGenderRatio
        ]
    }
