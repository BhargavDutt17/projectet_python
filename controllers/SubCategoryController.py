from models.SubCategoryModel import SubCategory,SubCategoryOut
from bson import ObjectId
from config.database import sub_category_collection,category_collection
from fastapi import APIRouter,HTTPException
from fastapi.responses import JSONResponse

async def addSubCategory(sub_category:SubCategory):
    savedCategory = await sub_category_collection.insert_one(sub_category.dict())
    return JSONResponse(content={"message":"SubCategory saved successfully."},status_code=201)

async def getAllSubCategories():
    subCategories = await sub_category_collection.find().to_list()
    
    for subCat in subCategories:
        if "category_id" in subCat and isinstance(subCat["category_id"],ObjectId):
            subCat["category_id"] = str(subCat["category_id"])
        
        category = await category_collection.find_one({"_id":ObjectId(subCat["category_id"])})
        if category:
            category["_id"] = str(category["_id"])
            subCat["category_id"] = category    
        
    
    return [SubCategoryOut(**subCat) for subCat in subCategories]        
            

async def getSubCategoryByCategoryId(category_id: str):
    subCategories = await sub_category_collection.find({"category_id": category_id}).to_list(None)

    for subCat in subCategories:
        if "_id" in subCat and isinstance(subCat["_id"], ObjectId):
            subCat["_id"] = str(subCat["_id"])  # Convert ObjectId to string

        if "category_id" in subCat and isinstance(subCat["category_id"], str):
            # Find the category document to include its details
            category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
            if category:
                category["_id"] = str(category["_id"])  # Convert ObjectId to string
                subCat["category_id"] = category  # Keep category_id as a dictionary

    return [SubCategoryOut(**subCat) for subCat in subCategories]

            