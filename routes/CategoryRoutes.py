from fastapi import APIRouter,Body
from models.CategoryModel import Category
from controllers import CategoryController

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


@router.put("/updateCategory/{category_id}")
async def update_category(category_id: str, category_data: dict = Body(...)):
    return await CategoryController.updateCategory(category_id, category_data)
    