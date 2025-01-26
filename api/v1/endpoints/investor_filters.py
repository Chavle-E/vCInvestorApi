from fastapi import APIRouter
import schemas
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Investor Filter Values
@router.get('/investors/email')
def return_email():
    return {
        "email": [
            {
                "label": "has_email",
                "value": "has_email"
            },
            {
                "label": "no_email",
                "value": "no_email"
            }
        ]

    }


@router.get('/investors/phone')
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


@router.get('/investors/address')
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


@router.get('/investors/cities')
def return_cities():
    return {
        "cities": [{
            "label": city.value, "value": city.value
        }
            for city in schemas.InvestorCity
        ]
    }


@router.get('/investors/states')
def return_states():
    return {
        "states": [{
            "label": state.value, "value": state.value
        }
            for state in schemas.InvestorState
        ]
    }


@router.get('/investors/country')
def return_country():
    return {
        "countries": [{
            "label": country.value, "value": country.value
        }
            for country in schemas.InvestorCountry
        ]
    }


@router.get('/investors/location_preferences')
def return_location_preferences():
    return {
        "location_preferences": [{
            "label": location.value, "value": location.value
        }
            for location in schemas.InvestorLocationPreference
        ]
    }


@router.get('/investors/industry_preferences')
def return_industry_preferences():
    return {
        "industry_preferences": [{
            "label": industry.value, "value": industry.value
        }
            for industry in schemas.InvestorIndustryPreference
        ]
    }


@router.get('/investors/fund_type')
def return_fund_type():
    return {
        "fund_types": [{
            "label": fund_type.value, "value": fund_type.value
        }
            for fund_type in schemas.InvestorFundType
        ]
    }


@router.get('/investors/stage_preferences')
def return_stage_preferences():
    return {
        "stage_preferences": [{
            "label": stage.value, "value": stage.value
        }
            for stage in schemas.InvestorStagePreference
        ]
    }


@router.get('/investors/assets_under_management')
def return_assets_under_management():
    return {
        "assets_under_management": [{
            "label": asset.value, "value": asset.value
        }
            for asset in schemas.InvestorAssetsUnderManagement
        ]
    }


@router.get('/investors/min_investment')
def return_min_investment():
    return {
        "minimum_investment": [{
            "label": investment.value, "value": investment.value
        }
            for investment in schemas.InvestorMinInvestment
        ]
    }


@router.get('/investors/max_investment')
def return_max_investment():
    return {
        "maximum_investment": [{
            "label": investment.value, "value": investment.value
        }
            for investment in schemas.InvestorMaxInvestment
        ]
    }


@router.get('/investors/job_title')
def return_job_title():
    return {
        "job_title": [{
            "label": title.value, "value": title.value
        }
            for title in schemas.InvestorJobTitle
        ]
    }


@router.get('/investors/number_of_investors')
def return_investors_amount():
    return {
        "number_of_investors": [{
            "label": investorsNumber.value, "value": investorsNumber.value
        }
            for investorsNumber in schemas.InvestorNumberOfInvestors
        ]
    }


@router.get('/investors/gender')
def return_gender():
    return {
        "gender": [{
            "label": gender.value, "value": gender.value
        }
            for gender in schemas.InvestorGender
        ]
    }
