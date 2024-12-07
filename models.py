from sqlalchemy import Column, Integer, String, Float, ARRAY, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    subscription_tier = Column(String, default="free")  # free, basic, professional
    subscription_status = Column(String, default="active")
    subscription_start = Column(DateTime(timezone=True), server_default=func.now())
    subscription_end = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    monthly_searches = Column(Integer, default=0)
    last_search = Column(DateTime(timezone=True), nullable=True)
    total_searches = Column(Integer, default=0)

    # Feature access flags
    can_export = Column(Boolean, default=False)
    can_see_full_profiles = Column(Boolean, default=False)
    can_see_contact_info = Column(Boolean, default=False)
    monthly_search_limit = Column(Integer, default=10)  # -1 for unlimited

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Investor(Base):
    __tablename__ = "investors"

    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    gender = Column(String, nullable=True)
    contact_title = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    office_website = Column(String, nullable=True)
    firm_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    type_of_financing = Column(String, nullable=True)
    industry_preferences = Column(PG_ARRAY(String), nullable=True)
    geographic_preferences = Column(PG_ARRAY(String), nullable=True)
    stage_preferences = Column(PG_ARRAY(String), nullable=True)
    capital_managed = Column(Float, nullable=True)
    min_investment = Column(Float, nullable=True)
    max_investment = Column(Float, nullable=True)


class InvestmentFund(Base):
    __tablename__ = "investment_funds"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    title = Column(String, nullable=True)
    contact_email = Column(String, index=True)
    contact_phone = Column(String, nullable=True)
    firm_name = Column(String)
    firm_email = Column(String, unique=True, index=True, nullable=True)
    firm_phone = Column(String, nullable=True)
    firm_website = Column(String, nullable=True)
    firm_address = Column(String, nullable=True)
    firm_city = Column(String, nullable=True)
    firm_state = Column(String, nullable=True)
    firm_zip = Column(String, nullable=True)
    firm_country = Column(String, nullable=True)
    office_type = Column(String, nullable=True)
    financing_type = Column(String, nullable=True)
    industry_preferences = Column(PG_ARRAY(String), nullable=True)
    geographic_preferences = Column(PG_ARRAY(String), nullable=True)
    stage_preferences = Column(PG_ARRAY(String), nullable=True)
    capital_managed = Column(Float, nullable=True)
    min_investment = Column(Float, nullable=True)
    max_investment = Column(Float, nullable=True)
    firm_type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
