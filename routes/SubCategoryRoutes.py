from fastapi import APIRouter, Query,Body
from models.SubCategoryModel import SubCategory
from controllers import SubCategoryController

router = APIRouter()


@router.post("/addSubCategory")
async def post_sub_category(sub_cat: SubCategory):
    return await SubCategoryController.addSubCategory(sub_cat)


@router.get("/getAllSubCategories")
async def get_all_sub_categories():
    return await SubCategoryController.getAllSubCategories()


@router.get("/getSubCategoryByCategoryId/{category_id}")
async def get_sub_category_by_category_id(
    category_id: str,
    user_id: str = Query(None, description="Logged-in user's ID"),
    role_id: str = Query(None, description="User's role ID"),
):
    return await SubCategoryController.getSubCategoryByCategoryId(
        category_id, user_id, role_id
    )



@router.delete("/deleteSubCategory/{subcategory_id}")
async def delete_sub_category(subcategory_id: str):
    return await SubCategoryController.deleteSubCategory(subcategory_id)

@router.put("/editSubcategory/{sub_category_id}")
async def update_subcategory(sub_category_id: str, update_data: dict = Body(...)):
    return await  SubCategoryController.editSubCategory(sub_category_id, update_data)