from fastapi import APIRouter,Body
from models.CategoryModel import Category
from controllers import CategoryController
from typing import List
from pydantic import BaseModel

router = APIRouter()

@router.post("/addCategory")
async def post_category(category: Category):
    return await CategoryController.addCategory(category)

@router.get("/getAllCategories")
async def get_all_categories():
    return await CategoryController.getAllCategories()

@router.delete("/deleteCategory/{category_id}")
async def delete_category(category_id: str):
    return await CategoryController.deleteCategory(category_id)

class CategoryDeleteRequest(BaseModel):
    category_ids: List[str]

@router.post("/delete-selected-categories")
async def delete_selected_categories(payload: CategoryDeleteRequest):
    return await CategoryController.deleteSelectedCategories(payload.category_ids)

@router.delete("/delete-all-categories")
async def delete_all_categories():
    return await CategoryController.deleteAllCategories()


@router.put("/updateCategory/{category_id}")
async def update_category(category_id: str, category_data: dict = Body(...)):
    return await CategoryController.updateCategory(category_id, category_data)
    