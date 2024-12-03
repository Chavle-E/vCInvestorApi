from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from enum import Enum


# ==================== Enums ====================

class City(str, Enum):
    NEW_YORK = "New York"
    LONDON = "London"
    SAN_FRANCISCO = "San Francisco"
    CHICAGO = "Chicago"
    BOSTON = "Boston"
    PARIS = "Paris"
    TORONTO = "Toronto"
    PALO_ALTO = "Palo Alto"
    SHANGHAI = "Shanghai"
    TOKYO = "Tokyo"
    BEIJING = "Beijing"
    MUMBAI = "Mumbai"
    CAMBRIDGE = "Cambridge"
    AUSTIN = "Austin"


class State(str, Enum):
    CALIFORNIA = "California"
    NEW_YORK = "New York"
    MASSACHUSETTS = "Massachusetts"
    TEXAS = "Texas"
    ILLINOIS = "Illinois"
    ONTARIO = "Ontario"
    CONNECTICUT = "Connecticut"
    FLORIDA = "Florida"
    PENNSYLVANIA = "Pennsylvania"
    COLORADO = "Colorado"
    MICHIGAN = "Michigan"
    OHIO = "Ohio"
    GEORGIA = "Georgia"
    MARYLAND = "Maryland"
    VIRGINIA = "Virginia"
    NEW_SOUTH_WALES = "New South Wales"
    NORTH_CAROLINA = "North Carolina"
    WASHINGTON = "Washington"
    BRITISH_COLUMBIA = "British Columbia"
    NEW_JERSEY = "New Jersey"


class Country(str, Enum):
    UNITED_STATES = "United States"
    UNITED_KINGDOM = "United Kingdom"
    GERMANY = "Germany"
    CANADA = "Canada"
    CHINA = "China"
    FRANCE = "France"
    INDIA = "India"
    ISRAEL = "Israel"
    HONG_KONG = "Hong Kong"
    JAPAN = "Japan"
    SINGAPORE = "Singapore"
    SWEDEN = "Sweden"
    AUSTRALIA = "Australia"
    NETHERLANDS = "Netherlands"
    SPAIN = "Spain"
    BELGIUM = "Belgium"
    SWITZERLAND = "Switzerland"
    FINLAND = "Finland"
    ITALY = "Italy"
    KOREA = "Korea"


class LocationPreference(str, Enum):
    UNITED_STATES = "United States"
    EUROPE = "Europe"
    CANADA = "Canada"
    UNITED_KINGDOM = "United Kingdom"
    CHINA = "China"
    GERMANY = "Germany"
    UNITED_STATES_CALIFORNIA = "United States (California)"
    ASIA = "Asia"
    FRANCE = "France"
    UNITED_STATES_MID_ATLANTIC = "United States (Mid-Atlantic)"
    UNITED_STATES_MIDWEST = "United States (Midwest)"
    UNITED_STATES_SOUTHEAST = "United States (Southeast)"
    UNITED_STATES_SOUTHWEST = "United States (Southwest)"
    UNITED_STATES_NORTHEAST = "United States (Northeast)"
    NETHERLANDS = "Netherlands"
    SWITZERLAND = "Switzerland"
    SWEDEN = "Sweden"
    INDIA = "India"
    AUSTRALIA = "Australia"


class IndustryPreference(str, Enum):
    IT_SERVICES = "IT Services"
    COMMUNICATIONS_NETWORKING = "Communications & Networking"
    SOFTWARE = "Software"
    HEALTHCARE_SERVICES = "Healthcare Services"
    CONSUMER_PRODUCTS_SERVICES = "Consumer Products & Services"
    BUSINESS_PRODUCTS_SERVICES = "Business Products & Services"
    MEDIA_ENTERTAINMENT = "Media & Entertainment"
    DISTRIBUTION_RETAIL = "Distribution/Retailing"
    FINANCIAL_SERVICES = "Financial Services"
    NATURAL_RESOURCES = "Natural Resources"
    DIVERSIFIED = "Diversified"
    INTERNET_TECHNOLOGY = "Internet Technology"
    CHEMICALS_MATERIALS = "Chemicals & Materials"
    MANUFACTURING = "Manufacturing"
    BIOTECHNOLOGY = "Biotechnology"
    ELECTRONICS = "Electronics"
    MEDICAL_DEVICES = "Medical Devices & Equipment"
    INDUSTRIAL_PRODUCTS = "Industrial Products & Services"
    FOOD_SERVICES = "Food Services & Products"
    ENVIRONMENT = "Environment"


class FundType(str, Enum):
    PRIVATE_EQUITY = "Private Equity Fund"
    VENTURE_CAPITAL = "Venture Capital Fund"
    INVESTMENT_BANK = "Investment Bank"
    SMALL_BUSINESS = "Small Business Investment Company"
    STARTUP_STUDIO = "Startup Studio"
    GOVERNMENT = "Government Organization"


class StagePreference(str, Enum):
    EXPANSION = "Expansion"
    MBO_LBO = "MBO/LBO"
    EARLY_STAGE = "Early Stage"
    STARTUP = "Startup"
    SEED = "Seed"
    ACQUISITION = "Acquisition"
    RECAPITALIZATION = "Recapitalization"
    LATER_STAGE = "Later Stage"
    RESTRUCTURING = "Restructuring"
    CORPORATE_DIVESTITURE = "Corporate Divestiture"
    CONSOLIDATION = "Consolidation"
    GOING_PRIVATE = "Going Private"
    SPECIAL_SITUATIONS = "Special Situations"
    TURNAROUND = "Turnaround"
    PIPE = "PIPE"
    SPINOUT = "Spinout"
    SECONDARY_PURCHASE = "Secondary Purchase"
    OWNERSHIP_TRANSITION = "Ownership Transition"
    DISTRESSED_DEBT = "Distressed Debt"
    PRIVATIZATION = "Privatization"


class AssetsUnderManagement(str, Enum):
    TIER_1B_PLUS = "$1B+"
    TIER_100M_500M = "$100M-$500M"
    TIER_500M_1B = "$500M-$1B"
    TIER_25M_100M = "$25M-$100M"
    TIER_0_25M = "$0-$25M"


class MinInvestment(str, Enum):
    TIER_25K_250K = "$25K-$250K"
    TIER_250K_1M = "$250K-$1M"
    TIER_1M_5M = "$1M-$5M"
    TIER_5M_PLUS = "$5M+"
    TIER_0_25K = "$0-$25K"


class MaxInvestment(str, Enum):
    TIER_25M_150M = "$25M-$150M"
    TIER_10M_25M = "$10M-$25M"
    TIER_1M_10M = "$1M-$10M"
    TIER_150M_PLUS = "$150M+"
    TIER_0_1M = "$0-$1M"


class NumberOfInvestors(str, Enum):
    TIER_1_10 = "1-10"
    TIER_11_20 = "11-20"
    TIER_21_30 = "21-30"
    TIER_31_40 = "31-40"


class GenderRatio(str, Enum):
    NO_FEMALE = "0% Female"
    FEMALE_25 = "25% Female"
    FEMALE_33 = "33% Female"
    FEMALE_50 = "50% Female"
    FEMALE_67 = "67% Female"
    FEMALE_75 = "75% Female"
    FEMALE_100 = "100% Female"


# ==================== Filter Models ====================

class LocationFilter(BaseModel):
    city: Optional[List[str]] = None
    state: Optional[List[str]] = None
    country: Optional[List[str]] = None
    location_preferences: Optional[List[str]] = None


class ContactAvailabilityFilter(BaseModel):
    hasOfficeEmail: Optional[bool] = None
    hasOfficePhone: Optional[bool] = None
    hasOfficeAddress: Optional[bool] = None


class IndustryFilter(BaseModel):
    industries: Optional[List[str]] = None


class StagePreferencesFilter(BaseModel):
    stages: Optional[List[str]] = None


class FundTypeFilter(BaseModel):
    types: Optional[List[str]] = None


class InvestmentRangesFilter(BaseModel):
    assetsUnderManagement: Optional[str] = None
    minInvestment: Optional[str] = None
    maxInvestment: Optional[str] = None


class InvestorCountFilter(BaseModel):
    range: Optional[str] = None


class GenderRatioFilter(BaseModel):
    ratio: Optional[str] = None


class GenderFilter(BaseModel):
    gender: Optional[str] = None


class FirmFilter(BaseModel):
    names: Optional[List[str]] = None


class JobTitleFilter(BaseModel):
    titles: Optional[List[str]] = None


class ContactInfoFilter(BaseModel):
    hasEmail: Optional[bool] = None
    hasPhone: Optional[bool] = None
    hasAddress: Optional[bool] = None


# ==================== Base Models ====================

class InvestorBase(BaseModel):
    prefix: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    contact_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    office_email: Optional[str] = None
    office_phone: Optional[str] = None
    office_website: Optional[str] = None
    office_address: Optional[str] = None
    firm_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    type_of_financing: Optional[str] = None
    industry_preferences: Optional[List[str]] = None
    geographic_preferences: Optional[List[str]] = None
    stage_preferences: Optional[List[str]] = None
    capital_managed: Optional[float] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    assets_under_management: Optional[float] = None
    number_of_investors: Optional[int] = None
    gender_ratio: Optional[str] = None


class InvestorCreate(InvestorBase):
    pass


class Investor(InvestorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class InvestmentFundBase(BaseModel):
    full_name: str
    title: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    firm_name: str
    firm_email: Optional[str] = None
    firm_phone: Optional[str] = None
    firm_website: Optional[str] = None
    firm_address: Optional[str] = None
    firm_city: Optional[str] = None
    firm_state: Optional[str] = None
    firm_zip: Optional[str] = None
    firm_country: Optional[str] = None
    office_type: Optional[str] = None
    financing_type: Optional[str] = None
    industry_preferences: Optional[List[str]] = None
    geographic_preferences: Optional[List[str]] = None
    stage_preferences: Optional[List[str]] = None
    capital_managed: Optional[float] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    firm_type: Optional[str] = None
    description: Optional[str] = None
    number_of_investors: Optional[int] = None
    gender_ratio: Optional[str] = None
    assets_under_management: Optional[float] = None


class InvestmentFundCreate(InvestmentFundBase):
    pass


class InvestmentFund(InvestmentFundBase):
    id: int
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={float: lambda v: v if v is not None else None}
    )


# ==================== Filter Params ====================

class InvestorFilterParams(BaseModel):
    searchTerm: Optional[str] = None
    location: Optional[LocationFilter] = None
    contactInfo: Optional[ContactInfoFilter] = None
    industry: Optional[IndustryFilter] = None
    fundType: Optional[FundTypeFilter] = None  # Added
    stages: Optional[StagePreferencesFilter] = None
    investmentRanges: Optional[InvestmentRangesFilter] = None
    firm: Optional[FirmFilter] = None  # Added
    jobTitle: Optional[JobTitleFilter] = None  # Added
    investorCount: Optional[InvestorCountFilter] = None
    gender: Optional[GenderFilter] = None

    class Config:
        use_enum_values = True


class InvestmentFundFilterParams(BaseModel):
    searchTerm: Optional[str] = None
    location: Optional[LocationFilter] = None
    contactInfo: Optional[ContactInfoFilter] = None
    industry: Optional[IndustryFilter] = None
    fundType: Optional[FundTypeFilter] = None
    stages: Optional[StagePreferencesFilter] = None
    investmentRanges: Optional[InvestmentRangesFilter] = None
    investorCount: Optional[InvestorCountFilter] = None
    genderRatio: Optional[GenderRatioFilter] = None

    class Config:
        use_enum_values = True
