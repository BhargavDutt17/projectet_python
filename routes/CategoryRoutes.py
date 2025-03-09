from fastapi import APIRouter
from models.CategoryModel import Category
from controllers import CategoryController

router = APIRouter()

@router.post("/addCategory")
async def post_category(category: Category):
    return await CategoryController.addCategory(category)

@router.get("/getAllCategories")
async def get_all_categories():
    return await CategoryController.getAllCategories()