import logging
import os
import sys
import traceback
from typing import Type, Union

import pandas as pd
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from database import engine
from models import Base, Investor, InvestmentFund

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_column_mappings(model):
    common_mappings = {
        'Industry Preferences': 'industry_preferences',
        'Geographic Preferences': 'geographic_preferences',
        'Stage Preferences': 'stage_preferences',
        'Capital Managed': 'capital_managed',
        'Number Of Investors': 'number_of_investors',
    }

    if model == InvestmentFund:
        return {
            **common_mappings,
            'Full Name': 'full_name',
            'Title': 'title',
            'Contact Email': 'contact_email',
            'Contact Phone': 'contact_phone',
            'Firm Name': 'firm_name',
            'Firm Email': 'firm_email',
            'Firm Phone': 'firm_phone',
            'Firm Website': 'firm_website',
            'Firm Address': 'firm_address',
            'Firm City': 'firm_city',
            'Firm State': 'firm_state',
            'Firm Zip': 'firm_zip',
            'Firm Country': 'firm_country',
            'Office Type': 'office_type',
            'Financing Type': 'financing_type',
            'Min. Investment': 'min_investment',
            'Max. Investment': 'max_investment',
            'Firm Type': 'firm_type',
            'Gender Ratio': 'gender_ratio'
        }
    else:  # Investor
        return {
            **common_mappings,
            'Prefix': 'prefix',
            'First Name': 'first_name',
            'Last Name': 'last_name',
            'Gender': 'gender',
            'Contact Title': 'contact_title',
            'Email': 'email',
            'Phone': 'phone',
            'Address': 'address',
            'Office Website': 'office_website',
            'Firm Name': 'firm_name',
            'City': 'city',
            'State': 'state',
            'Country': 'country',
            'Type Of Firm': 'type_of_firm',
            'Type of Financing': 'type_of_financing',
            'Min Investment': 'min_investment',
            'Max Investment': 'max_investment'
        }


def convert_currency(value):
    if pd.isna(value) or value is None or value == '':
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value) if value > 0 else None
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').replace(' ', '')
            if '-' in value:
                parts = value.split('-')
                values = [float(p) for p in parts if p.strip()]
                return sum(values) / len(values) if values else None
            return float(value) if float(value) > 0 else None
        return None
    except Exception as e:
        logger.error(f"Error converting currency value '{value}': {str(e)}")
        return None


def clean_list_field(value):
    if pd.isna(value) or value in ('', '[""]'):
        return None
    try:
        if isinstance(value, str):
            value = value.strip('[]').replace('"', '').replace("'", '')
            items = [item.strip() for item in value.split(',')]
            items = list(set(item for item in items if item))
            return items if items else None
        elif isinstance(value, list):
            items = [str(item).strip() for item in value if item]
            return list(set(items)) if items else None
        return None
    except Exception as e:
        logger.error(f"List cleaning error for {value}: {str(e)}")
        return None


def clean_and_convert_data(df: pd.DataFrame, model: Type[Union[Investor, InvestmentFund]]) -> pd.DataFrame:
    df = df.replace({
        'Unknown': None, '': None, 'N/A': None, 'nan': None,
        'NULL': None, 'None': None, '["]': None, '[]': None
    })

    numeric_cols = ['min_investment', 'max_investment', 'capital_managed']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(convert_currency)

    if 'number_of_investors' in df.columns:
        df['number_of_investors'] = df['number_of_investors'].apply(lambda x: float(x) if pd.notnull(x) else None)

    if 'gender_ratio' in df.columns:
        df['gender_ratio'] = df['gender_ratio'].astype(str)

    list_fields = ['industry_preferences', 'geographic_preferences', 'stage_preferences']
    if model == Investor:
        list_fields.append('type_of_financing')
    elif model == InvestmentFund:
        list_fields.append('financing_type')

    for field in list_fields:
        if field in df.columns:
            df[field] = df[field].apply(clean_list_field)

    return df


def import_data(csv_file: str, model: Type[Union[Investor, InvestmentFund]], session: Session):
    logger.info(f"\nProcessing {model.__name__} data from {csv_file}")

    try:
        df = pd.read_csv(csv_file)
        logger.info(f"Successfully read CSV with {len(df)} rows")

        df = df.rename(columns=get_column_mappings(model))
        df_cleaned = clean_and_convert_data(df, model)
        logger.info("Data cleaning completed")

    except Exception as e:
        logger.error(f"Error processing CSV file {csv_file}: {str(e)}")
        raise

    chunk_size = 1000
    records_processed = 0
    errors = 0

    for start_idx in range(0, len(df_cleaned), chunk_size):
        chunk = df_cleaned.iloc[start_idx:start_idx + chunk_size]

        for _, row in chunk.iterrows():
            try:
                record = {k: v for k, v in row.items()
                          if v is not None and k in model.__table__.columns.keys()}

                stmt = insert(model).values(**record)
                session.execute(stmt)
                session.commit()
                records_processed += 1

            except Exception as e:
                errors += 1
                logger.error(f"Error inserting record: {str(e)}")
                logger.error(f"Problematic record: {record}")
                session.rollback()

            if records_processed % 100 == 0:
                logger.info(f"Processed {records_processed} records. Errors: {errors}")

    logger.info(f"\nImport completed for {model.__name__}:")
    logger.info(f"Total records processed: {records_processed}")
    logger.info(f"Total errors: {errors}")

    return records_processed


def verify_import(session: Session, model: Type[Union[Investor, InvestmentFund]]):
    logger.info(f"\nVerifying {model.__name__} import:")
    total = session.query(model).count()
    logger.info(f"Total records: {total}")

    for col in ['min_investment', 'max_investment', 'capital_managed']:
        count = session.query(model).filter(getattr(model, col).isnot(None)).count()
        logger.info(f"Non-null {col}: {count}")

        samples = session.query(model).filter(
            getattr(model, col).isnot(None)
        ).limit(5).all()
        if samples:
            logger.info(f"Sample {col} values:")
            for sample in samples:
                logger.info(f"  {getattr(sample, col)}")


def main():
    try:
        logger.info(f"BASE_DIR: {BASE_DIR}")

        with Session(engine) as session:
            try:
                investors_csv = f"{BASE_DIR}/data/investors_cleaned.csv"
                if os.path.exists(investors_csv):
                    logger.info("Found investors CSV file")
                    total_investors = import_data(investors_csv, Investor, session)
                    print(total_investors)
                    verify_import(session, Investor)
                else:
                    logger.error(f"Investors CSV not found at {investors_csv}")

                funds_csv = f"{BASE_DIR}/data/vc_funds.csv"
                if os.path.exists(funds_csv):
                    logger.info("Found funds CSV file")
                    total_funds = import_data(funds_csv, InvestmentFund, session)
                    print(total_funds)
                    verify_import(session, InvestmentFund)
                else:
                    logger.error(f"Funds CSV not found at {funds_csv}")

            except Exception as e:
                logger.error(f"Database session error: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        logger.error(f"Python version: {sys.version}")
        logger.error(f"Platform: {sys.platform}")
        logger.error(f"Working directory: {os.getcwd()}")
        logger.error(f"pandas version: {pd.__version__}")
        logger.error(f"sqlalchemy version: {sqlalchemy.__version__}")
        raise


if __name__ == "__main__":
    main()
