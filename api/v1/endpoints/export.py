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


@router.get("/lists/{list_id}/export/csv")
async def export_list_items_csv(
        list_id: int,
        db: Session = Depends(get_db)
):
    """Export items from a specific list to CSV"""
    try:
        # Get the list and verify it exists
        saved_list = db.query(models.SavedList).filter(models.SavedList.id == list_id).first()
        if not saved_list:
            raise HTTPException(status_code=404, detail="List not found")

        # Get list items
        items = crud.saved_list.get_list_items(db=db, list_id=list_id)
        if not items:
            raise HTTPException(status_code=404, detail="No items found in list")

        # Generate CSV based on list type
        if saved_list.list_type.lower() == 'investor':
            headers = [
                "id", "first_name", "last_name", "email", "phone",
                "firm_name", "city", "state", "country",
                "type_of_financing", "industry_preferences",
                "stage_preferences", "capital_managed"
            ]
        else:
            headers = [
                "id", "firm_name", "firm_type", "contact_email",
                "firm_city", "firm_state", "firm_country",
                "financing_type", "industry_preferences",
                "stage_preferences", "capital_managed"
            ]

        # Generate CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for item in items:
            # Clean up the row data
            row = {k: (', '.join(map(str, v)) if isinstance(v, (list, tuple)) else v)
                   for k, v in item.items() if k in headers}
            writer.writerow(row)

        output.seek(0)

        # Stream the CSV
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename="{saved_list.name}_{datetime.now().strftime("%Y%m%d")}.csv"'
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error exporting list items: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating export")