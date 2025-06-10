from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, date # Ensured datetime and date are imported

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_user_id

router = APIRouter(
    prefix="/sips",
    tags=["sips"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SIP, status_code=201)
def create_sip_for_user(
    sip: schemas.SIPCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    return crud.create_sip(db=db, sip=sip, user_id=user_id)

@router.get("/summary", response_model=List[schemas.SIPSummary])
def get_sips_summary_for_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    sips = crud.get_sips_by_user(db=db, user_id=user_id)
    today = date.today()
    summary_dict: Dict[str, Dict[str, float]] = {}
    for sip_item in sips:
        if sip_item.start_date > today:
            months_invested = 0
        else:
            months_invested = (today.year - sip_item.start_date.year) * 12 + (today.month - sip_item.start_date.month) + 1
            if months_invested < 0: months_invested = 0
        if months_invested > 0:
            current_sip_total_invested = sip_item.monthly_amount * months_invested
            if sip_item.scheme_name not in summary_dict:
                summary_dict[sip_item.scheme_name] = {"total_invested": 0.0, "raw_months": 0}
            summary_dict[sip_item.scheme_name]["total_invested"] += current_sip_total_invested
            if months_invested > summary_dict[sip_item.scheme_name].get("raw_months", 0):
                 summary_dict[sip_item.scheme_name]["raw_months"] = months_invested
    response_list: List[schemas.SIPSummary] = []
    for scheme, data in summary_dict.items():
        response_list.append(schemas.SIPSummary(
            scheme_name=scheme,
            total_invested=data["total_invested"],
            months_invested=int(data.get("raw_months", 0))
        ))
    return response_list
