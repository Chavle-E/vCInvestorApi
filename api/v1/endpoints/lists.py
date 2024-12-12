from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
import models
import schemas
from database import get_db
import crud
import logging
from datetime import datetime
import io
import csv

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.SavedList)
def create_list(
        list_data: schemas.SavedListCreate,
        db: Session = Depends(get_db)
):
    """Create a new saved list"""
    return crud.saved_list.create(db=db, obj_in=list_data)


@router.get("/", response_model=List[schemas.SavedList])
def get_all_lists(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    """Get all saved lists"""
    return crud.saved_list.get_multi(db=db, skip=skip, limit=limit)


@router.post("/{list_id}/investors/{investor_id}")
def add_investor_to_list(
        list_id: int,
        investor_id: int,
        db: Session = Depends(get_db)
):
    """Add an investor to a saved list"""
    success = crud.saved_list.add_investor_to_list(db=db, list_id=list_id, investor_id=investor_id)
    if not success:
        raise HTTPException(status_code=404, detail="List or investor not found")
    return {"status": "success"}


@router.post("/{list_id}/funds/{fund_id}")
def add_fund_to_list(
        list_id: int,
        fund_id: int,
        db: Session = Depends(get_db)
):
    """Add a fund to a saved list"""
    success = crud.saved_list.add_fund_to_list(db=db, list_id=list_id, fund_id=fund_id)
    if not success:
        raise HTTPException(status_code=404, detail="List or fund not found")
    return {"status": "success"}


@router.delete("/{list_id}/investors/{investor_id}")
def remove_investor_from_list(
        list_id: int,
        investor_id: int,
        db: Session = Depends(get_db)
):
    """Remove an investor from a saved list"""
    success = crud.saved_list.remove_investor_from_list(db=db, list_id=list_id, investor_id=investor_id)
    if not success:
        raise HTTPException(status_code=404, detail="List or investor not found")
    return {"status": "success"}


@router.delete("/{list_id}/funds/{fund_id}")
def remove_fund_from_list(
        list_id: int,
        fund_id: int,
        db: Session = Depends(get_db)
):
    """Remove a fund from a saved list"""
    success = crud.saved_list.remove_fund_from_list(db=db, list_id=list_id, fund_id=fund_id)
    if not success:
        raise HTTPException(status_code=404, detail="List or fund not found")
    return {"status": "success"}


@router.get("/{list_id}/items", response_model=None)
def get_list_items(
        list_id: int,
        db: Session = Depends(get_db)
):
    """Get all items in a saved list"""
    try:
        logger.info(f"Attempting to retrieve items for list {list_id}")

        # Get the list with relationships loaded
        saved_list = db.query(models.SavedList) \
            .options(joinedload(models.SavedList.saved_investors)) \
            .options(joinedload(models.SavedList.saved_funds)) \
            .filter(models.SavedList.id == list_id) \
            .first()

        if not saved_list:
            logger.error(f"List with id {list_id} not found")
            raise HTTPException(status_code=404, detail="List not found")

        logger.info(f"Found list: {saved_list.name} (type: {saved_list.list_type})")
        logger.info(f"Number of investors: {len(saved_list.saved_investors)}")
        logger.info(f"Number of funds: {len(saved_list.saved_funds)}")

        # Convert items to dictionaries based on list type
        if saved_list.list_type.lower() == 'investor':
            # Get the actual investor records
            investor_ids = [inv.id for inv in saved_list.saved_investors]
            investors = db.query(models.Investor) \
                .filter(models.Investor.id.in_(investor_ids)) \
                .all()

            items = [crud.investor.to_dict(inv) for inv in investors]
            logger.info(f"Retrieved {len(items)} investors")
        else:
            # Get the actual fund records
            fund_ids = [fund.id for fund in saved_list.saved_funds]
            funds = db.query(models.InvestmentFund) \
                .filter(models.InvestmentFund.id.in_(fund_ids)) \
                .all()

            items = [crud.investment_fund.to_dict(fund) for fund in funds]
            logger.info(f"Retrieved {len(items)} funds")

        # Return formatted response
        return {
            "list_id": list_id,
            "list_name": saved_list.name,
            "list_type": saved_list.list_type,
            "total_items": len(items),
            "items": items
        }

    except Exception as e:
        logger.error(f"Error retrieving list items: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{list_id}/items", response_model=None)
def get_list_items(
        list_id: int,
        db: Session = Depends(get_db)
):
    """Get all items in a saved list, including both investors and funds"""
    try:
        logger.info(f"Retrieving items for list {list_id}")

        # Get the list with all relationships loaded
        saved_list = db.query(models.SavedList) \
            .options(joinedload(models.SavedList.saved_investors)) \
            .options(joinedload(models.SavedList.saved_funds)) \
            .filter(models.SavedList.id == list_id) \
            .first()

        if not saved_list:
            logger.error(f"List with id {list_id} not found")
            raise HTTPException(status_code=404, detail="List not found")

        # Get investors if any exist
        investors = []
        if saved_list.saved_investors:
            investor_ids = [inv.id for inv in saved_list.saved_investors]
            db_investors = db.query(models.Investor) \
                .filter(models.Investor.id.in_(investor_ids)) \
                .all()
            investors = [crud.investor.to_dict(inv) for inv in db_investors]
            logger.info(f"Found {len(investors)} investors")

        # Get funds if any exist
        funds = []
        if saved_list.saved_funds:
            fund_ids = [fund.id for fund in saved_list.saved_funds]
            db_funds = db.query(models.InvestmentFund) \
                .filter(models.InvestmentFund.id.in_(fund_ids)) \
                .all()
            funds = [crud.investment_fund.to_dict(fund) for fund in db_funds]
            logger.info(f"Found {len(funds)} funds")

        # Combine both types of items into a single response
        response = {
            "list_id": list_id,
            "list_name": saved_list.name,
            "list_type": saved_list.list_type,
            "total_items": len(investors) + len(funds),
            "items": {
                "investors": {
                    "count": len(investors),
                    "data": investors
                },
                "funds": {
                    "count": len(funds),
                    "data": funds
                }
            }
        }

        logger.info(f"Successfully retrieved {response['total_items']} items from list")
        return response

    except Exception as e:
        logger.error(f"Error retrieving list items: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{list_id}/type", response_model=None)
async def update_list_type(
        list_id: int,
        list_type: str,
        db: Session = Depends(get_db)
):
    """Update the type of a saved list"""
    try:
        saved_list = db.query(models.SavedList).filter(models.SavedList.id == list_id).first()
        if not saved_list:
            raise HTTPException(status_code=404, detail="List not found")

        # Update list type
        saved_list.list_type = list_type
        db.commit()

        return {
            "message": "List type updated successfully",
            "list_id": list_id,
            "new_type": list_type
        }
    except Exception as e:
        logger.error(f"Error updating list type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{list_id}")
async def export_list(
        list_id: int,
        db: Session = Depends(get_db)
):
    """Export all items from a specific list"""
    try:
        # Get the list and its items
        items_response = get_list_items(list_id, db)

        # Process investors
        investor_data = items_response["items"]["investors"]["data"]
        investor_fields = [
            "id", "first_name", "last_name", "email", "phone",
            "firm_name", "city", "state", "country",
            "type_of_financing", "industry_preferences",
            "stage_preferences", "capital_managed"
        ]

        # Process funds
        fund_data = items_response["items"]["funds"]["data"]
        fund_fields = [
            "id", "firm_name", "firm_type", "contact_email",
            "firm_city", "firm_state", "firm_country",
            "financing_type", "industry_preferences",
            "stage_preferences", "capital_managed"
        ]

        # Generate CSV
        output = io.StringIO()

        # Write investors section
        writer = csv.DictWriter(output, fieldnames=investor_fields)
        writer.writeheader()
        for investor in investor_data:
            row = {k: (', '.join(map(str, v)) if isinstance(v, (list, tuple)) else v)
                   for k, v in investor.items() if k in investor_fields}
            writer.writerow(row)

        # Add separator
        output.write("\n--- Investment Funds ---\n\n")

        # Write funds section
        writer = csv.DictWriter(output, fieldnames=fund_fields)
        writer.writeheader()
        for fund in fund_data:
            row = {k: (', '.join(map(str, v)) if isinstance(v, (list, tuple)) else v)
                   for k, v in fund.items() if k in fund_fields}
            writer.writerow(row)

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=list_{list_id}_export.csv"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


