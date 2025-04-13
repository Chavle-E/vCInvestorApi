from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime


###########################################
# Investment Fund Filter Enums
###########################################

class InvestmentFundCity(str, Enum):
    NEW_YORK = "New York"
    LONDON = "London"
    SAN_FRANCISCO = "San Francisco"
    CHICAGO = "Chicago"
    BOSTON = "Boston"
    PARIS = "Paris"
    PALO_ALTO = "Palo Alto"
    SHANGHAI = "Shanghai"
    TORONTO = "Toronto"
    MENLO_PARK = "Menlo Park"
    DALLAS = "Dallas"
    TOKYO = "Tokyo"
    BEIJING = "Beijing"
    LOS_ANGELES = "Los Angeles"
    HOUSTON = "Houston"
    MUNICH = "Munich"
    STOCKHOLM = "Stockholm"
    MUMBAI = "Mumbai"
    CAMBRIDGE = "Cambridge"
    AUSTIN = "Austin"


class InvestmentFundState(str, Enum):
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


class InvestmentFundCountry(str, Enum):
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


class InvestmentFundLocationPreference(str, Enum):
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
    ISRAEL = "Israel"
    UNITED_STATES_SOUTHWEST = "United States (Southwest)"
    UNITED_STATES_SOUTHEAST = "United States (Southeast)"
    UNITED_STATES_NORTHEAST = "United States (Northeast)"
    SWITZERLAND = "Switzerland"
    SWEDEN = "Sweden"
    INDIA = "India"
    NETHERLANDS = "Netherlands"
    AUSTRALIA = "Australia"


class InvestmentFundFinancingType(str, Enum):
    DEBT = "Debt"
    EQUITY = "Equity"
    FUND_OF_FUNDS = 'Fund of Funds'
    LEASES = 'Leases'
    MEZZANINE = 'Mezzanine'
    ROYALTIES = 'Royalties'


class InvestmentFundIndustryPreference(str, Enum):
    IT_SERVICES = "IT Services"
    COMMUNICATIONS_NETWORKING = "Communications & Networking"
    SOFTWARE = "Software"
    HEALTHCARE_SERVICES = "Healthcare Services"
    CONSUMER_PRODUCTS_SERVICES = "Consumer Products & Services"
    BUSINESS_PRODUCTS_SERVICES = "Business Products & Services"
    MEDIA_ENTERTAINMENT = "Media & Entertainment"
    DISTRIBUTION_RETAIL = "Distribution/Retailing"
    FINANCIAL_SERVICES = "Financial Services"
    ENERGY_NATURAL_RESOURCES = "Energy/Natural Resources"
    DIVERSIFIED = "Diversified"
    INTERNET_TECHNOLOGY = "Internet Technology"
    CHEMICALS_MATERIALS = "Chemicals & Materials"
    MANUFACTURING = "Manufacturing"
    BIOTECHNOLOGY = "Biotechnology"
    ELECTRONICS = "Electronics"
    MEDICAL_DEVICES_EQUIPMENT = "Medical Devices & Equipment"
    INDUSTRIAL_PRODUCTS_SERVICES = "Industrial Products & Services"
    FOOD_SERVICES_PRODUCTS = "Food Services & Products"
    ENVIRONMENT = "Environment"


class InvestmentFundType(str, Enum):
    PRIVATE_EQUITY = "Private Equity Fund"
    VENTURE_CAPITAL = "Venture Capital Fund"
    INVESTMENT_BANK = "Investment Bank"
    SMALL_BUSINESS = "Small Business Investment Company"
    STARTUP_STUDIO = "Startup Studio"
    GOVERNMENT = "Government Organization"


class InvestmentFundStagePreference(str, Enum):
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


class InvestmentFundAssetsUnderManagement(str, Enum):
    TIER_1B_PLUS = "$1B+"
    TIER_100M_500M = "$100M - $500M"
    TIER_500M_1B = "$500M - $1B"
    TIER_25M_100M = "$25M - $100M"
    TIER_0_25M = "$0 - $25M"


class InvestmentFundMinInvestment(str, Enum):
    TIER_5M_20M = "$5M - $20M"
    TIER_1M_5M = "$1M - $5M"
    TIER_250K_1M = "$250K - $1M"
    TIER_20M_PLUS = "$20M+"
    TIER_0_250K = "$0 - $250K"


class InvestmentFundMaxInvestment(str, Enum):
    TIER_1M_10M = "$1M - $10M"
    TIER_10M_25M = "$10M - $25M"
    TIER_25M_100M = "$25M - $100M"
    TIER_100M_PLUS = "$100M+"
    TIER_0_1M = "$0 - $1M"


class InvestmentFundNumberOfInvestors(str, Enum):
    TIER_1_10 = "1 - 10"
    TIER_10_20 = "10 - 20"
    TIER_20_30 = "20 - 30"
    TIER_30_40 = "30 - 40"


class InvestmentFundGenderRatio(str, Enum):
    NO_FEMALE = "0% female"
    FEMALE_25 = "25% female"
    FEMALE_20 = "20% female"
    FEMALE_33 = "33% female"
    FEMALE_17 = "17% female"
    FEMALE_13 = "13% female"
    FEMALE_50 = "50% female"
    FEMALE_14 = "14% female"
    FEMALE_11 = "11% female"
    FEMALE_8 = "8% female"
    FEMALE_9 = "9% female"
    FEMALE_10 = "10% female"
    FEMALE_6 = "6% female"
    FEMALE_100 = "100% female"
    FEMALE_40 = "40% female"
    FEMALE_29 = "29% female"
    FEMALE_22 = "22% female"
    FEMALE_7 = "7% female"
    FEMALE_15 = "15% female"
    FEMALE_4 = "4% female"


###########################################
# Investor Filter Enums
###########################################

class InvestorCity(str, Enum):
    NEW_YORK = "New York"
    LONDON = "London"
    SAN_FRANCISCO = "San Francisco"
    CHICAGO = "Chicago"
    BOSTON = "Boston"
    PARIS = "Paris"
    TORONTO = "Toronto"
    PALO_ALTO = "Palo Alto"
    SHANGHAI = "Shanghai"
    MENLO_PARK = "Menlo Park"
    DALLAS = "Dallas"
    LOS_ANGELES = "Los Angeles"
    HOUSTON = "Houston"
    STOCKHOLM = "Stockholm"
    MUNICH = "Munich"
    AMSTERDAM = "Amsterdam"
    BEIJING = "Beijing"
    GREENWICH = "Greenwich"
    MUMBAI = "Mumbai"
    TOKYO = "Tokyo"


class InvestorState(str, Enum):
    CALIFORNIA = "California"
    NEW_YORK = "New York"
    MASSACHUSETTS = "Massachusetts"
    ILLINOIS = "Illinois"
    TEXAS = "Texas"
    CONNECTICUT = "Connecticut"
    ONTARIO = "Ontario"
    PENNSYLVANIA = "Pennsylvania"
    FLORIDA = "Florida"
    NORTH_CAROLINA = "North Carolina"
    COLORADO = "Colorado"
    MARYLAND = "Maryland"
    MICHIGAN = "Michigan"
    NEW_SOUTH_WALES = "New South Wales"
    GEORGIA = "Georgia"
    OHIO = "Ohio"
    VIRGINIA = "Virginia"
    MINNESOTA = "Minnesota"
    DISTRICT_OF_COLUMBIA = "District of Columbia"
    MISSOURI = "Missouri"


class InvestorCountry(str, Enum):
    UNITED_STATES = "United States"
    UNITED_KINGDOM = "United Kingdom"
    FRANCE = "France"
    GERMANY = "Germany"
    CANADA = "Canada"
    CHINA = "China"
    NETHERLANDS = "Netherlands"
    INDIA = "India"
    SWEDEN = "Sweden"
    ISRAEL = "Israel"
    SPAIN = "Spain"
    AUSTRALIA = "Australia"
    SINGAPORE = "Singapore"
    BELGIUM = "Belgium"
    FINLAND = "Finland"
    JAPAN = "Japan"
    HONG_KONG = "Hong Kong"
    ITALY = "Italy"
    SWITZERLAND = "Switzerland"
    NORWAY = "Norway"


class InvestorLocationPreference(str, Enum):
    UNITED_STATES = "United States"
    EUROPE = "Europe"
    CANADA = "Canada"
    UNITED_KINGDOM = "United Kingdom"
    GERMANY = "Germany"
    CHINA = "China"
    FRANCE = "France"
    UNITED_STATES_CALIFORNIA = "United States (California)"
    ASIA = "Asia"
    UNITED_STATES_MID_ATLANTIC = "United States (Mid-Atlantic)"
    UNITED_STATES_MIDWEST = "United States (Midwest)"
    UNITED_STATES_SOUTHEAST = "United States (Southeast)"
    ISRAEL = "Israel"
    SWITZERLAND = "Switzerland"
    UNITED_STATES_SOUTHWEST = "United States (Southwest)"
    NETHERLANDS = "Netherlands"
    SWEDEN = "Sweden"
    UNITED_STATES_NORTHEAST = "United States (Northeast)"
    FINLAND = "Finland"
    AUSTRIA = "Austria"


class InvestorIndustryPreference(str, Enum):
    IT_SERVICES = "IT Services"
    COMMUNICATIONS_NETWORKING = "Communications & Networking"
    HEALTHCARE_SERVICES = "Healthcare Services"
    BUSINESS_PRODUCTS_SERVICES = "Business Products & Services"
    CONSUMER_PRODUCTS_SERVICES = "Consumer Products & Services"
    DISTRIBUTION_RETAIL = "Distribution/Retailing"
    FINANCIAL_SERVICES = "Financial Services"
    SOFTWARE = "Software"
    DIVERSIFIED = "Diversified"
    MEDIA_ENTERTAINMENT = "Media & Entertainment"
    ENERGY_NATURAL_RESOURCES = "Energy/Natural Resources"
    MANUFACTURING = "Manufacturing"
    INTERNET_TECHNOLOGY = "Internet Technology"
    CHEMICALS_MATERIALS = "Chemicals & Materials"
    INDUSTRIAL_PRODUCTS_SERVICES = "Industrial Products & Services"
    ELECTRONICS = "Electronics"
    BIOTECHNOLOGY = "Biotechnology"
    MEDICAL_DEVICES_EQUIPMENT = "Medical Devices & Equipment"
    FOOD_SERVICES_PRODUCTS = "Food Services & Products"
    EDUCATION_TRAINING = "Education & Training"


class InvestorFundType(str, Enum):
    PRIVATE_EQUITY = "Private Equity Fund"
    VENTURE_CAPITAL = "Venture Capital Fund"
    SMALL_BUSINESS = "Small Business Investment Company"
    INVESTMENT_BANK = "Investment Bank"
    GOVERNMENT = "Government Organization"
    STARTUP_STUDIO = "Startup Studio"


class InvestorFinancingType(str, Enum):
    DEBT = "Debt"
    EQUITY = "Equity"
    FUND_OF_FUNDS = 'Fund of Funds'
    LEASES = 'Leases'
    MEZZANINE = 'Mezzanine'
    ROYALTIES = 'Royalties'


class InvestorStagePreference(str, Enum):
    EXPANSION = "Expansion"
    MBO_LBO = "MBO/LBO"
    EARLY_STAGE = "Early Stage"
    STARTUP = "Startup"
    SEED = "Seed"
    RECAPITALIZATION = "Recapitalization"
    ACQUISITION = "Acquisition"
    LATER_STAGE = "Later Stage"
    CORPORATE_DIVESTITURE = "Corporate Divestiture"
    RESTRUCTURING = "Restructuring"
    CONSOLIDATION = "Consolidation"
    GOING_PRIVATE = "Going Private"
    SPECIAL_SITUATIONS = "Special Situations"
    TURNAROUND = "Turnaround"
    PIPE = "PIPE"
    SPINOUT = "Spinout"
    OWNERSHIP_TRANSITION = "Ownership Transition"
    SECONDARY_PURCHASE = "Secondary Purchase"
    PRIVATIZATION = "Privatization"
    DISTRESSED_DEBT = "Distressed Debt"


class InvestorAssetsUnderManagement(str, Enum):
    TIER_1B_PLUS = "$1B+"
    TIER_100M_500M = "$100M - $500M"
    TIER_500M_1B = "$500M - $1B"
    TIER_25M_100M = "$25M - $100M"
    TIER_0_25M = "$0 - $25M"


class InvestorMinInvestment(str, Enum):
    TIER_5M_20M = "$5M - $20M"
    TIER_20M_PLUS = "$20M+"
    TIER_1M_5M = "$1M - $5M"
    TIER_250K_1M = "$250K - $1M"
    TIER_0_250K = "$0 - $250K"


class InvestorMaxInvestment(str, Enum):
    TIER_25M_100M = "$25M - $100M"
    TIER_10M_25M = "$10M - $25M"
    TIER_100M_PLUS = "$100M+"
    TIER_1M_10M = "$1M - $10M"
    TIER_0_1M = "$0 - $1M"


class InvestorNumberOfInvestors(str, Enum):
    TIER_1_10 = "1 - 10"
    TIER_10_20 = "10 - 20"
    TIER_20_30 = "20 - 30"
    TIER_30_40 = "30 - 40"


class InvestorJobTitle(str, Enum):
    PARTNER = "Partner"
    MANAGING_DIRECTOR = "Managing Director"
    MANAGING_PARTNER = "Managing Partner"
    ASSOCIATE = "Associate"
    PRINCIPAL = "Principal"
    VICE_PRESIDENT = "Vice President"
    SENIOR_ASSOCIATE = "Senior Associate"
    GENERAL_PARTNER = "General Partner"
    INVESTMENT_MANAGER = "Investment Manager"
    INVESTMENT_DIRECTOR = "Investment Director"
    DIRECTOR = "Director"
    CFO = "CFO"
    ANALYST = "Analyst"
    CEO = "CEO"
    FOUNDING_PARTNER = "Founding Partner"
    VENTURE_PARTNER = "Venture Partner"
    OPERATING_PARTNER = "Operating Partner"
    PRESIDENT = "President"
    CHAIRMAN = "Chairman"
    SENIOR_MANAGING_DIRECTOR = "Senior Managing Director"


class InvestorGender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


###########################################
# Filter Parameters Models
###########################################

class LocationFilter(BaseModel):
    """Location filter parameters"""
    city: Optional[List[str]] = None
    state: Optional[List[str]] = None
    country: Optional[List[str]] = None
    location_preferences: Optional[List[str]] = None


class ContactInfoFilter(BaseModel):
    """Contact information filter parameters"""
    hasEmail: Optional[bool] = None
    hasPhone: Optional[bool] = None
    hasAddress: Optional[bool] = None


class IndustryFilter(BaseModel):
    """Industry preferences filter parameters"""
    industries: Optional[List[str]] = None


class StagePreferencesFilter(BaseModel):
    """Investment stage preferences filter parameters"""
    stages: Optional[List[str]] = None


class FundTypeFilter(BaseModel):
    """Fund type filter parameters"""
    types: Optional[List[str]] = None


class InvestmentRangesFilter(BaseModel):
    """Investment range filter parameters"""
    assetsUnderManagement: Optional[List[str]] = None
    minInvestment: Optional[List[str]] = None
    maxInvestment: Optional[List[str]] = None


class InvestorCountFilter(BaseModel):
    """Number of investors filter parameters"""
    range: Optional[List[str]] = None


class GenderRatioFilter(BaseModel):
    """Gender ratio filter parameters"""
    ratio: Optional[List[str]] = None


class GenderFilter(BaseModel):
    """Gender filter parameters"""
    gender: Optional[str] = None


class JobTitleFilter(BaseModel):
    """Job title filter parameters"""
    titles: Optional[List[str]] = None


# Main filter parameter models
class InvestorFilterParams(BaseModel):
    """Complete investor filter parameters"""
    searchTerm: Optional[str] = None
    location: Optional[LocationFilter] = None
    contactInfo: Optional[ContactInfoFilter] = None
    industry: Optional[IndustryFilter] = None
    fundType: Optional[FundTypeFilter] = None
    stages: Optional[StagePreferencesFilter] = None
    investmentRanges: Optional[InvestmentRangesFilter] = None
    jobTitle: Optional[JobTitleFilter] = None
    gender: Optional[GenderFilter] = None

    class Config:
        use_enum_values = True


###########################################
# Base Models
###########################################

class InvestorBase(BaseModel):
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    gender: Optional[str] = None
    contact_title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    office_website: Optional[str] = None
    firm_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    type_of_firm: Optional[str] = None
    type_of_financing: Optional[List[str]] = None
    industry_preferences: Optional[List[str]] = None
    geographic_preferences: Optional[List[str]] = None
    stage_preferences: Optional[List[str]] = None
    capital_managed: Optional[float] = None
    min_investment: Optional[float] = None
    max_investment: Optional[float] = None
    number_of_investors: Optional[float] = None


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
    number_of_investors: Optional[float] = None
    gender_ratio: Optional[str] = None


class InvestmentFundCreate(InvestmentFundBase):
    pass


class InvestmentFund(InvestmentFundBase):
    id: int
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={float: lambda v: v if v is not None else None}
    )


class InvestmentFundFilterParams(BaseModel):
    """Complete investment fund filter parameters"""
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


class SavedListBase(BaseModel):
    """Base class for saved lists"""
    name: str
    description: Optional[str] = None
    list_type: str  # 'investor' or 'fund'


class SavedListCreate(SavedListBase):
    """Create schema for saved lists"""
    pass


class SavedList(SavedListBase):
    """Response schema for saved lists"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_photo: Optional[str] = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class VerifyEmail(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    verification_id: str


class VerifyOTP(BaseModel):
    user_id: int
    code: str = Field(..., min_length=6, max_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile_photo: Optional[str] = None
    is_google_auth: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class GoogleAccountLink(BaseModel):
    email: EmailStr
    password: str


class SetPasswordForOAuthUser(BaseModel):
    password: str = Field(..., min_length=8)
    confirm_password: str
