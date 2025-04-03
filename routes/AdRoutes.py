from fastapi import APIRouter, HTTPException
from controllers.AdController import get_ads
from models.AdModel import AdResponse
from typing import List

router = APIRouter()


@router.get("/ads/income/{user_id}", response_model=List[AdResponse])
async def fetch_income_ads(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return await get_ads(user_id, "income")


@router.get("/ads/expense/{user_id}", response_model=List[AdResponse])
async def fetch_expense_ads(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return await get_ads(user_id, "expense")
