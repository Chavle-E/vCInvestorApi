from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Investor, InvestmentFund
import logging
from fastapi.responses import StreamingResponse
import io
import csv

router = APIRouter()
logger = logging.getLogger(__name__)


def generate_csv(data, headers):
    """Generate CSV file from data"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    for row in data:
        clean_row = {key: (", ".join(map(str, value)) if isinstance(value, (list, tuple)) else value) for key, value in row.items()}
        writer.writerow(clean_row)

    output.seek(0)
    return output


@router.get("/investors/csv")
async def export_investors_csv(
    db: Session = Depends(get_db),
    limit: int = Query(1000, le=5000)
):
    """Export investors to CSV"""
    try:
        # Fetch investors from the database
        investors = db.query(Investor).limit(limit).all()

        # Convert database rows into dictionaries
        investor_data = [
            {
                "id": inv.id,
                "first_name": inv.first_name,
                "last_name": inv.last_name,
                "firm_name": inv.firm_name,
                "city": inv.city,
                "state": inv.state,
                "country": inv.country,
                "type_of_financing": inv.type_of_financing,
                "industry_preferences": inv.industry_preferences,
                "stage_preferences": inv.stage_preferences,
                "capital_managed": inv.capital_managed,
                "min_investment": inv.min_investment,
                "email": inv.email,
                "phone": inv.phone,
                "office_website": inv.office_website,
            }
            for inv in investors
        ]

        # Generate CSV content in memory
        headers = list(investor_data[0].keys()) if investor_data else []
        csv_content = generate_csv(investor_data, headers)

        # Stream the CSV content as a downloadable file
        return StreamingResponse(
            iter([csv_content.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': 'attachment; filename="investors.csv"'
            }
        )

    except Exception as e:
        logger.error(f"Error exporting investors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting investors: {str(e)}")


@router.get("/funds/csv")
async def export_funds_csv(
    db: Session = Depends(get_db),
    limit: int = Query(1000, le=5000)
):
    """Export investment funds to CSV"""
    try:
        # Fetch investment funds from the database
        funds = db.query(InvestmentFund).limit(limit).all()

        # Convert database rows into dictionaries
        fund_data = [
            {
                "id": fund.id,
                "firm_name": fund.firm_name,
                "firm_type": fund.firm_type,
                "firm_city": fund.firm_city,
                "firm_state": fund.firm_state,
                "firm_country": fund.firm_country,
                "financing_type": fund.financing_type,
                "industry_preferences": fund.industry_preferences,
                "stage_preferences": fund.stage_preferences,
                "capital_managed": fund.capital_managed,
                "min_investment": fund.min_investment,
                "max_investment": fund.max_investment,
                "contact_email": fund.contact_email,
                "contact_phone": fund.contact_phone,
                "firm_email": fund.firm_email,
                "firm_phone": fund.firm_phone,
                "firm_website": fund.firm_website,
            }
            for fund in funds
        ]

        # Generate CSV content in memory
        headers = list(fund_data[0].keys()) if fund_data else []
        csv_content = generate_csv(fund_data, headers)

        # Stream the CSV content as a downloadable file
        return StreamingResponse(
            iter([csv_content.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': 'attachment; filename="investment_funds.csv"'
            }
        )

    except Exception as e:
        logger.error(f"Error exporting funds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting funds: {str(e)}")
