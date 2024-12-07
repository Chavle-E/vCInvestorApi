# api/v1/endpoints/export.py

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Investor, InvestmentFund
import logging
from fastapi.responses import StreamingResponse
import io
import csv

router = APIRouter()
logger = logging.getLogger(__name__)


def check_export_permission(user):
    """Check if user has permission to export data"""
    if not user.can_export:
        raise HTTPException(
            status_code=403,
            detail="Your subscription tier doesn't include export functionality"
        )


def generate_csv(data, headers):
    """Generate CSV file from data"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    for row in data:
        # Clean row data
        clean_row = {}
        for key in headers:
            value = row.get(key)
            if isinstance(value, (list, tuple)):
                clean_row[key] = ", ".join(str(x) for x in value if x)
            else:
                clean_row[key] = value
        writer.writerow(clean_row)

    output.seek(0)
    return output


@router.get("/investors/csv")
async def export_investors_csv(
        request: Request,
        db: Session = Depends(get_db),
        limit: int = Query(1000, le=5000)
):
    """Export investors to CSV - premium feature"""
    try:
        user = request.state.user
        check_export_permission(user)

        # Get all investors
        investors = db.query(Investor).limit(limit).all()

        # Convert to dict
        investor_data = []
        for inv in investors:
            data = {
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
                "min_investment": inv.min_investment
            }

            # Only include contact info for higher tiers
            if user.can_see_contact_info:
                data.update({
                    "email": inv.email,
                    "phone": inv.phone,
                    "office_website": inv.office_website
                })

            investor_data.append(data)

        # Generate CSV
        headers = list(investor_data[0].keys()) if investor_data else []
        output = generate_csv(investor_data, headers)

        # Return streaming response
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename="investors.csv"'
            }
        )

        return response

    except Exception as e:
        logger.error(f"Error exporting investors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funds/csv")
async def export_funds_csv(
        request: Request,
        db: Session = Depends(get_db),
        limit: int = Query(1000, le=5000)
):
    """Export investment funds to CSV - premium feature"""
    try:
        user = request.state.user
        check_export_permission(user)

        # Get all funds
        funds = db.query(InvestmentFund).limit(limit).all()

        # Convert to dict
        fund_data = []
        for fund in funds:
            data = {
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
            }

            # Only include contact info for higher tiers
            if user.can_see_contact_info:
                data.update({
                    "contact_email": fund.contact_email,
                    "contact_phone": fund.contact_phone,
                    "firm_email": fund.firm_email,
                    "firm_phone": fund.firm_phone,
                    "firm_website": fund.firm_website
                })

            fund_data.append(data)

        # Generate CSV
        headers = list(fund_data[0].keys()) if fund_data else []
        output = generate_csv(fund_data, headers)

        # Return streaming response
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename="investment_funds.csv"'
            }
        )

        return response

    except Exception as e:
        logger.error(f"Error exporting funds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))