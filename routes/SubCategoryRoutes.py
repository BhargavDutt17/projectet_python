from fastapi import APIRouter
from models.SubCategoryModel import SubCategory
from controllers import SubCategoryController

router = APIRouter()
@router.post("/addSubCategory")
async def post_sub_category(sub_cat:SubCategory):
    return await SubCategoryController.addSubCategory(sub_cat)

@router.post("/addSubCategory/{user_id}/{user_role}")
async def post_sub_category(sub_category: SubCategory, user_id: str, user_role: str):
    return await SubCategoryController.addSubCategory(sub_category, user_id, user_role)

@router.get("/getAllSubCategories")
async def get_all_sub_categories():
    return await SubCategoryController.getAllSubCategories()

@router.get("/getSubCategoryByCategoryId/{category_id}")
async def get_sub_category_by_category_id(category_id: str):
    return await SubCategoryController.getSubCategoryByCategoryId(category_id)

# 🔹 Add this route for user-specific subcategories
@router.get("/getSubCategoriesByUser/{user_id}/{user_role}")
async def get_subcategories_by_user(user_id: str, user_role: str):
    return await SubCategoryController.getSubCategoriesByUser(user_id, user_role)