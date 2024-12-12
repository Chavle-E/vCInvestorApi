import os
import logging
from database import test_db_connection, engine
import models
from scripts.import_data import import_investors, import_investment_funds
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deploy():
    """
    Deploy application and import data
    """
    try:
        # Test database connection
        logger.info("Testing database connection...")
        if not test_db_connection():
            logger.error("Database connection failed!")
            return False

        # Create all tables
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)

        # Import data
        logger.info("Starting data import...")
        with Session(engine) as db:
            # Check if data already exists
            investor_count = db.query(models.Investor).count()
            fund_count = db.query(models.InvestmentFund).count()

            if investor_count == 0 and fund_count == 0:
                # Import investors
                investors_csv = os.path.join('data', 'investors_cleaned.csv')
                if os.path.exists(investors_csv):
                    logger.info(f"Importing investors from {investors_csv}")
                    import_investors(investors_csv, db)
                else:
                    logger.warning(f"Investors CSV file not found: {investors_csv}")

                # Import investment funds
                funds_csv = os.path.join('data', 'vc_funds.csv')
                if os.path.exists(funds_csv):
                    logger.info(f"Importing funds from {funds_csv}")
                    import_investment_funds(funds_csv, db)
                else:
                    logger.warning(f"Investment Funds CSV file not found: {funds_csv}")
            else:
                logger.info("Data already exists in database, skipping import")

        logger.info("Deployment completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during deployment: {str(e)}")
        return False


if __name__ == "__main__":
    deploy()
