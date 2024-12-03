from sqlalchemy.orm import Session
from sqlalchemy import Column, or_, String, Text
from sqlalchemy.sql import expression
import models
import schemas
from typing import TypeVar, Generic, List, Any, Dict, Optional, Type, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
import math
from decimal import Decimal

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=schemas.BaseModel)

logger = logging.getLogger(__name__)


class CRUDBase(Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_multi(
            self,
            db: Session,
            skip: int = 0,
            limit: int = 100,
            search: Optional[str] = None,
            filters: Optional[Dict] = None,
            sort_by: Optional[str] = None,
            sort_desc: bool = False
    ) -> List[Dict]:
        try:
            query = db.query(self.model)

            # Apply text search across string fields
            if search:
                search_filters = []
                for column in self.model.__table__.columns:
                    if isinstance(column.type, (String, Text)):
                        search_filters.append(getattr(self.model, column.key).ilike(f"%{search}%"))
                if search_filters:
                    query = query.filter(or_(*search_filters))

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, dict):
                            col = getattr(self.model, key)
                            for op, val in value.items():
                                if op == "gte":
                                    query = query.filter(col >= val)
                                elif op == "lte":
                                    query = query.filter(col <= val)
                        elif isinstance(value, (list, tuple)):
                            # Handle array overlaps for preferences
                            col = getattr(self.model, key)
                            if hasattr(col, 'overlap'):
                                query = query.filter(col.overlap(value))
                            else:
                                query = query.filter(col.in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)

            # Apply sorting
            if sort_by and hasattr(self.model, sort_by):
                order_col = getattr(self.model, sort_by)
                if sort_desc:
                    order_col = order_col.desc()
                query = query.order_by(order_col)

            records = query.offset(skip).limit(limit).all()
            return [self.to_dict(record) for record in records]

        except Exception as e:
            logger.error(f"Error in get_multi: {str(e)}")
            raise

    @staticmethod
    def sanitize_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (float, Decimal)):
            if math.isnan(float(value)) or math.isinf(float(value)):
                return None
            return float(value)
        return value

    @staticmethod
    def sanitize_list(value: Any) -> Optional[List]:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item) for item in value if item is not None]
        if isinstance(value, str):
            return [value]
        return None

    def to_dict(self, obj: ModelType) -> Dict:
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)

            # Handle different types of values
            if isinstance(value, (float, Decimal)):
                # Handle non-JSON-compliant float values
                if value is None or math.isnan(float(value)) or math.isinf(float(value)):
                    result[column.name] = None
                else:
                    result[column.name] = float(value)
            elif isinstance(value, list):
                # Handle lists (like arrays from postgres)
                if value and isinstance(value[0], str) and value[0].startswith('{'):
                    # Handle PostgreSQL array format {item1,item2}
                    cleaned = value[0].strip('{}').split(',')
                    result[column.name] = [item.strip('"') for item in cleaned if item]
                else:
                    result[column.name] = value
            else:
                result[column.name] = value

        return result

    def create(self, db: Session, obj_in: CreateSchemaType) -> Dict:
        try:
            obj_in_data = self.prepare_data_for_db(obj_in.model_dump())
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return self.to_dict(db_obj)
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if obj:
                return self.to_dict(obj)
            return None
        except Exception as e:
            logger.error(f"Error in get: {str(e)}")
            raise

    def update(self, db: Session, id: Any, obj_in: CreateSchemaType) -> Optional[Dict]:
        try:
            db_obj = db.query(self.model).filter(self.model.id == id).first()
            if db_obj:
                obj_data = self.prepare_data_for_db(obj_in.model_dump(exclude_unset=True))
                for key, value in obj_data.items():
                    setattr(db_obj, key, value)

                db.commit()
                db.refresh(db_obj)
                return self.to_dict(db_obj)
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise

    def delete(self, db: Session, id: Any) -> Optional[Dict]:
        try:
            obj = db.query(self.model).get(id)

            if obj:
                obj_dict = self.to_dict(obj)
                db.delete(obj)
                db.commit()
                return obj_dict
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise

    @staticmethod
    def handle_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (float, Decimal)):
            try:
                float_val = float(value)
                if math.isnan(float_val) or math.isinf(float_val):
                    return None
                return float_val
            except (ValueError, TypeError):
                return None
        return value

    def prepare_data_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prepared_data = {}
        for key, value in data.items():
            if isinstance(value, (float, Decimal)):
                prepared_data[key] = self.handle_float(value)
            elif isinstance(value, list):
                prepared_data[key] = [str(item) for item in value if item] or None
            else:
                prepared_data[key] = value
        return prepared_data


class CRUDInvestor(CRUDBase[models.Investor, schemas.InvestorCreate]):
    def get_by_email(self, db: Session, email: str) -> Optional[models.Investor]:
        return db.query(models.Investor).filter(models.Investor.email == email).first()

    def get_by_industry(self, db: Session, industry: str) -> List[models.Investor]:
        return db.query(models.Investor).filter(
            models.Investor.industry_preferences.overlap([industry])
        ).all()


class CRUDInvestmentFund(CRUDBase[models.InvestmentFund, schemas.InvestmentFundCreate]):
    def get_by_firm_email(self, db: Session, firm_email: str) -> Optional[models.InvestmentFund]:
        return db.query(models.InvestmentFund).filter(
            models.InvestmentFund.firm_email == firm_email
        ).first()

    def get_by_firm_name(self, db: Session, firm_name: str) -> Optional[models.InvestmentFund]:
        return db.query(models.InvestmentFund).filter(
            models.InvestmentFund.firm_name == firm_name
        ).first()


# Create instances
investor = CRUDInvestor(models.Investor)
investment_fund = CRUDInvestmentFund(models.InvestmentFund)
