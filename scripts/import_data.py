import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from database import engine
from models import Base, Investor, InvestmentFund
from typing import Type, Union
import logging
import os
import traceback

# Get the absolute path of the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create tables
Base.metadata.create_all(bind=engine)

# Setup logging
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
            'Firm Type': 'firm_type'
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


def clean_and_convert_data(df: pd.DataFrame, model: Type[Union[Investor, InvestmentFund]]) -> pd.DataFrame:
    def convert_currency(value):
        if pd.isna(value) or value is None or value == '' or value == 0:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace(' ', '')
                if '-' in value:
                    parts = value.split('-')
                    values = [float(p) for p in parts if p.strip()]
                    return sum(values) / len(values)
                return float(value)
            return None
        except:
            return None

    def clean_list_field(value):
        if pd.isna(value) or value is None or value == '' or value == '[""]':
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
        except:
            return None

    # Replace empty values
    df = df.replace({
        'Unknown': None, '': None, 'N/A': None, 'nan': None,
        'NULL': None, 'None': None, '["]': None, '[]': None,
        0: None
    })

    # Convert numeric fields
    numeric_cols = ['min_investment', 'max_investment', 'capital_managed']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(convert_currency)

    # Convert list fields
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

    df = pd.read_csv(csv_file)
    df = df.rename(columns=get_column_mappings(model))
    df_cleaned = clean_and_convert_data(df, model)

    chunk_size = 1000
    records_processed = 0
    errors = 0

    for start_idx in range(0, len(df_cleaned), chunk_size):
        chunk = df_cleaned.iloc[start_idx:start_idx + chunk_size]

        for _, row in chunk.iterrows():
            try:
                record = {k: v for k, v in row.items()
                          if v is not None and k in model.__table__.columns.keys()}

                id_field = 'email' if model == Investor else 'firm_email'

                if record.get(id_field):
                    stmt = insert(model).values(**record)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[id_field],
                        set_=record
                    )

                    session.execute(stmt)
                    session.commit()
                    records_processed += 1
                else:
                    errors += 1
                    logger.warning(f"Skipping record - missing {id_field}")

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

        # Sample values
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
            # Import Investors
            investors_csv = f"{BASE_DIR}/data/investors_cleaned.csv"
            logger.info(f"Looking for investors CSV at: {investors_csv}")
            if os.path.exists(investors_csv):
                logger.info("Found investors CSV file")
                total_investors = import_data(investors_csv, Investor, session)
                verify_import(session, Investor)
            else:
                logger.error(f"Investors CSV not found at {investors_csv}")

            # Import Investment Funds
            funds_csv = f"{BASE_DIR}/data/vc_funds.csv"
            logger.info(f"Looking for funds CSV at: {funds_csv}")
            if os.path.exists(funds_csv):
                logger.info("Found funds CSV file")
                total_funds = import_data(funds_csv, InvestmentFund, session)
                verify_import(session, InvestmentFund)
            else:
                logger.error(f"Funds CSV not found at {funds_csv}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
