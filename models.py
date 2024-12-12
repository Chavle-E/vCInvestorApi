from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.sql import func
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

# Association tables for many-to-many relationships
saved_investors_association = Table(
    'saved_investors_association',
    Base.metadata,
    Column('list_id', Integer, ForeignKey('saved_lists.id')),
    Column('investor_id', Integer, ForeignKey('investors.id'))
)

saved_funds_association = Table(
    'saved_funds_association',
    Base.metadata,
    Column('list_id', Integer, ForeignKey('saved_lists.id')),
    Column('fund_id', Integer, ForeignKey('investment_funds.id'))
)


class SavedList(Base):
    __tablename__ = "saved_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    list_type = Column(String, nullable=False)  # 'investor' or 'fund'

    # Relationships
    saved_investors = relationship("Investor", secondary=saved_investors_association)
    saved_funds = relationship("InvestmentFund", secondary=saved_funds_association)


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
