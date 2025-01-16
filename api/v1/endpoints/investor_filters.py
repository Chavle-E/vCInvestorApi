from fastapi import APIRouter, Depends, HTTPException, Query
import schemas
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Investor Filter Values
@router.get('/investors/cities')
def return_cities():
    return {
        "cities": [{
            "label": city.value, "value": city.name
        }
            for city in schemas.InvestorCity
        ]
    }


@router.get('/investors/states')
def return_states():
    return {
        "states": [{
            "label": state.value, "value": state.name
        }
            for state in schemas.InvestorState
        ]
    }


@router.get('/investors/country')
def return_country():
    return {
        "countries": [{
            "label": country.value, "value": country.name
        }
            for country in schemas.InvestorCountry
        ]
    }


@router.get('/investors/location_preferences')
def return_location_preferences():
    return {
        "location_preferences": [{
            "label": location.value, "value": location.name
        }
            for location in schemas.InvestorLocationPreference
        ]
    }


@router.get('/investors/industry_preferences')
def return_industry_preferences():
    return {
        "industry_preferences": [{
            "label": industry.value, "value": industry.name
        }
            for industry in schemas.InvestorIndustryPreference
        ]
    }


@router.get('investors/fund_type')
def return_fund_type():
    return {
        "fund_types": [{
            "label": fund_type.value, "value": fund_type.name
        }
            for fund_type in schemas.InvestorFundType
        ]
    }


@router.get('investors/stage_preferences')
def return_stage_preferences():
    return {
        "stage_preferences": [{
            "label": stage.value, "value": stage.name
        }
            for stage in schemas.InvestorStagePreference
        ]
    }


@router.get('investors/assets_under_management')
def return_assets_under_management():
    return {
        "assets_under_management": [{
            "label": asset.value, "value": asset.name
        }
            for asset in schemas.InvestorAssetsUnderManagement
        ]
    }


@router.get('investors/min_investment')
def return_min_investment():
    return {
        "minimum_investment": [{
            "label": investment.value, "value": investment.name
        }
            for investment in schemas.InvestorMinInvestment
        ]
    }


@router.get('investors/max_investment')
def return_max_investment():
    return {
        "maximum_investment": [{
            "label": investment.value, "value": investment.name
        }
            for investment in schemas.InvestorMaxInvestment
        ]
    }


@router.get('investors/number_of_investors')
def return_number_of_investors():
    return {
        "number_of_investors": [{
            "label": number.value, "value": number.name
        }
            for number in schemas.InvestorNumberOfInvestors
        ]
    }


@router.get('investors/gender')
def return_gender():
    return {
        "gender": [{
            "label": gender.value, "value": gender.name
        }
            for gender in schemas.InvestorGender
        ]
    }
