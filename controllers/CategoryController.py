from models.CategoryModel import Category,CategoryOut
from bson import ObjectId
from fastapi import APIRouter,HTTPException
from fastapi.responses import JSONResponse
from config.database import category_collection

async def addCategory(category:Category):
    savedCategory = await category_collection.insert_one(category.dict())
    return JSONResponse(content={"message":"category saved successfully"},status_code=201)


async def getAllCategories():
    categories = await category_collection.find().to_list()
    return [CategoryOut(**cat) for cat in categories]

async def deleteCategory(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category ID")

    result = await category_collection.delete_one({"_id": ObjectId(category_id)})

    if result.deleted_count == 1:
        return JSONResponse(content={"message": "Category deleted successfully"}, status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Category not found")
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId

async def updateCategory(category_id: str, updated_data: dict):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(category_id):
            raise HTTPException(status_code=400, detail="Invalid Category ID format.")

        # Fetch existing category
        existing_category = await category_collection.find_one({"_id": ObjectId(category_id)})
        if not existing_category:
            raise HTTPException(status_code=404, detail="Category not found.")

        # Fields allowed to be updated
        allowed_fields = ["name", "description"]
        update_fields = {key: updated_data[key] for key in allowed_fields if key in updated_data}

        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        # Perform update
        await category_collection.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": update_fields}
        )

        return JSONResponse(content={"message": "Category updated successfully"}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating category: {str(e)}")
