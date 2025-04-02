from fastapi import APIRouter, Depends
from controllers.AdController import get_ads
from models.AdModel import AdResponse
from typing import List

router = APIRouter()

@router.get("/ads/{user_id}", response_model=List[AdResponse])
async def fetch_ads(user_id: str):
    return await get_ads(user_id)

# @router.get("/ads/{user_id}", response_model=List[AdResponse])
# async def fetch_ads(user_id: str):
#     ads = await get_ads(user_id)
#     print(f"Swagger Response: {ads}")  # ✅ Debugging
#     return ads


# @router.get("/ads/{user_id}", response_model=List[AdResponse] | None)
# async def fetch_ads(user_id: str):
#     ads = await get_ads(user_id)
#     return ads if ads else None  # Return None instead of an empty list

# @router.get("/ads/{user_id}", response_model=List[AdResponse])
# async def fetch_ads(user_id: str):
#     ads = await get_ads(user_id)
#     return ads if ads else []  # ✅ Ensure response is always a list
