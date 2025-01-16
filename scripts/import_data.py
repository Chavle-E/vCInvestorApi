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

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_column_mappings(model):
    if model == InvestmentFund:
        return {
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
            'Industry Preferences': 'industry_preferences',
            'Geographic Preferences': 'geographic_preferences',
            'Stage Preferences': 'stage_preferences',
            'Capital Managed': 'capital_managed',
            'Min. Investment': 'min_investment',
            'Max. Investment': 'max_investment',
            'Firm Type': 'firm_type'
        }
    else:  # Investor
        return {
            'Prefix': 'prefix',
            'First Name': 'first_name',
            'Last Name': 'last_name',
            'Gender': 'gender',
            'Contact Title': 'contact_title',
            'Email': 'email',
            'Phone': 'phone',
            'Office Website': 'office_website',
            'Firm Name': 'firm_name',
            'City': 'city',
            'State': 'state',
            'Country': 'country',
            'Type of Financing': 'type_of_financing',
            'Industry Preferences': 'industry_preferences',
            'Geographic Preferences': 'geographic_preferences',
            'Stage Preferences': 'stage_preferences',
            'Capital Managed': 'capital_managed',
            'Min Investment': 'min_investment',
            'Max Investment': 'max_investment'
        }


def clean_and_convert_data(df: pd.DataFrame, model: Type[Union[Investor, InvestmentFund]]) -> pd.DataFrame:
    logger.info("\nStarting data cleaning and conversion")

    def convert_currency(value):
        if pd.isna(value) or value is None or value == '':
            return None
        try:
            # If value is already a number, return it
            if isinstance(value, (int, float)):
                return float(value) if value != 0 else None

            # If it's a string, clean and convert
            if isinstance(value, str):
                # Handle lists stored as strings
                if value.startswith('[') and value.endswith(']'):
                    return None
                # Remove any non-numeric characters except dots
                value_str = ''.join(c for c in value if c.isdigit() or c == '.')
                if value_str:
                    result = float(value_str)
                    return result if result != 0 else None
            return None
        except Exception as e:
            logger.error(f"Error converting value '{value}' ({type(value)}): {str(e)}")
            return None

    def convert_list_field(value):
        if pd.isna(value) or value is None or value == '':
            return None
        try:
            if isinstance(value, str):
                # If it's already in list format, try to evaluate it
                if value.startswith('[') and value.endswith(']'):
                    try:
                        # Clean the string before eval
                        cleaned_value = value.replace('", "', '","').strip()
                        result = eval(cleaned_value)
                        return result if result else None
                    except:
                        # If eval fails, split by comma
                        value = value.strip('[]')
                        if value:
                            return [item.strip().strip('"\'') for item in value.split(',') if item.strip()]
                        return None
                # Otherwise split by comma
                return [item.strip() for item in value.split(',') if item.strip()]
            elif isinstance(value, list):
                return value
            return None
        except Exception as e:
            logger.error(f"Error converting list value '{value}' ({type(value)}): {str(e)}")
            return None

    # Replace 'Unknown' and empty strings with None
    df = df.replace({'Unknown': None, '': None, 'N/A': None})

    # Convert numeric fields
    numeric_cols = ['min_investment', 'max_investment', 'capital_managed']

    # Process each numeric column
    for col in numeric_cols:
        if col in df.columns:
            logger.info(f"\nProcessing column: {col}")
            logger.info(f"Original values (first 5):\n{df[col].head()}")

            # Convert to numeric
            df[col] = df[col].apply(convert_currency)

            logger.info(f"Converted values (first 5):\n{df[col].head()}")
            non_null_count = df[col].notnull().sum()
            logger.info(f"Number of non-null values: {non_null_count}")

    # Handle list fields
    list_fields = ['industry_preferences', 'geographic_preferences', 'stage_preferences']
    if model == Investor:
        list_fields.append('type_of_financing')

    for field in list_fields:
        if field in df.columns:
            logger.info(f"\nProcessing list field: {field}")
            logger.info(f"Original values (first 5):\n{df[field].head()}")

            df[field] = df[field].apply(convert_list_field)

            logger.info(f"Converted values (first 5):\n{df[field].head()}")
            non_null_count = df[field].notnull().sum()
            logger.info(f"Number of non-null values: {non_null_count}")

    return df


def import_investors(csv_file: str, session: Session):
    logger.info("\nProcessing Investors data...")
    df = pd.read_csv(csv_file)

    # Print column info
    logger.info(f"Columns in CSV: {df.columns.tolist()}")
    logger.info("\nSample of numeric columns before processing:")
    for col in ['Min Investment', 'Max Investment', 'Capital Managed']:
        if col in df.columns:
            logger.info(f"\n{col}:")
            logger.info(df[col].head())

    # Rename columns
    df = df.rename(columns=get_column_mappings(Investor))

    df_cleaned = clean_and_convert_data(df, Investor)

    # Process in chunks
    chunk_size = 1000
    records_processed = 0

    for start_idx in range(0, len(df_cleaned), chunk_size):
        chunk = df_cleaned.iloc[start_idx:start_idx + chunk_size]

        for _, row in chunk.iterrows():
            try:
                # Convert row to dict and remove None values
                record = {k: v for k, v in row.items() if v is not None and k in Investor.__table__.columns.keys()}

                # Create an UPSERT statement
                stmt = insert(Investor).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['email'],
                    set_=record
                )
                session.execute(stmt)
                session.commit()
                records_processed += 1

            except Exception as e:
                logger.error(f"Error inserting investor record: {str(e)}")
                logger.error(f"Problematic record: {record}")
                session.rollback()

            if records_processed % 100 == 0:
                logger.info(f"Processed {records_processed} investor records")

        logger.info(f"Processed {records_processed} investor records in current chunk")

    logger.info(f"Total investors processed: {records_processed}")
    return records_processed


def import_investment_funds(csv_file: str, session: Session):
    logger.info("\nProcessing Investment Funds data...")
    df = pd.read_csv(csv_file)

    # Rename columns
    df = df.rename(columns=get_column_mappings(InvestmentFund))

    df_cleaned = clean_and_convert_data(df, InvestmentFund)

    # Process in chunks
    chunk_size = 1000
    records_processed = 0

    for start_idx in range(0, len(df_cleaned), chunk_size):
        chunk = df_cleaned.iloc[start_idx:start_idx + chunk_size]

        for _, row in chunk.iterrows():
            try:
                # Convert row to dict and remove None values
                record = {k: v for k, v in row.items() if
                          v is not None and k in InvestmentFund.__table__.columns.keys()}

                # Create an UPSERT statement
                stmt = insert(InvestmentFund).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['firm_email'],
                    set_=record
                )
                session.execute(stmt)
                session.commit()
                records_processed += 1

            except Exception as e:
                logger.error(f"Error inserting fund record: {str(e)}")
                logger.error(f"Problematic record: {record}")
                session.rollback()

        logger.info(f"Processed {records_processed} investment fund records")

    return records_processed


def main():
    try:
        with Session(engine) as session:
            # Import Investors
            investors_csv = os.path.join(BASE_DIR, 'data', 'investors_cleaned.csv')
            if os.path.exists(investors_csv):
                total_investors = import_investors(investors_csv, session)

                # Verify investors import
                total_count = session.query(Investor).count()
                logger.info(f"\nTotal investors in database: {total_count}")

                for col in ['min_investment', 'max_investment', 'capital_managed']:
                    count = session.query(Investor).filter(getattr(Investor, col).isnot(None)).count()
                    logger.info(f"Count of non-null values in {col}: {count}")

                    # Show sample values
                    samples = session.query(Investor).filter(getattr(Investor, col).isnot(None)).limit(3).all()
                    if samples:
                        logger.info(f"Sample values for {col}:")
                        for sample in samples:
                            logger.info(f"{getattr(sample, col)}")
            else:
                logger.warning(f"Investors CSV file not found: {investors_csv}")

            # Import Investment Funds
            funds_csv = os.path.join(BASE_DIR, 'data', 'vc_funds.csv')
            if os.path.exists(funds_csv):
                total_funds = import_investment_funds(funds_csv, session)

                # Verify investment funds import
                total_count = session.query(InvestmentFund).count()
                logger.info(f"\nTotal investment funds in database: {total_count}")

                for col in ['min_investment', 'max_investment', 'capital_managed']:
                    count = session.query(InvestmentFund).filter(getattr(InvestmentFund, col).isnot(None)).count()
                    logger.info(f"Count of non-null values in {col}: {count}")

                    # Show sample values
                    samples = session.query(InvestmentFund).filter(getattr(InvestmentFund, col).isnot(None)).limit(
                        3).all()
                    if samples:
                        logger.info(f"Sample values for {col}:")
                        for sample in samples:
                            logger.info(f"{getattr(sample, col)}")
            else:
                logger.warning(f"Investment Funds CSV file not found: {funds_csv}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
