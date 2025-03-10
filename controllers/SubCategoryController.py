from models.SubCategoryModel import SubCategory, SubCategoryOut
from bson import ObjectId
from config.database import sub_category_collection, category_collection
from fastapi.responses import JSONResponse
from fastapi import HTTPException

async def addSubCategory(sub_category: SubCategory, user_id: str, user_role: str):
    sub_category_dict = sub_category.dict()
    sub_category_dict["created_by"] = f"user_id:{user_id},role:{user_role}"  # Store as a single string

    savedCategory = await sub_category_collection.insert_one(sub_category_dict)
    return JSONResponse(content={"message": "SubCategory saved successfully!"}, status_code=201)


# async def addSubCategory(sub_category: SubCategory, user_id: str, user_role: str):
#     sub_category_dict = sub_category.dict()  
#     sub_category_dict["created_by"] = {"user_id": user_id, "role": user_role}  # Convert to dict manually

#     savedCategory = await sub_category_collection.insert_one(sub_category_dict)
#     return JSONResponse(content={"message": "SubCategory saved successfully!"}, status_code=201)


async def getSubCategoriesByUser(user_id: str, user_role: str):
    if user_role == "admin":
        subCategories = await sub_category_collection.find().to_list(None)
    else:
        subCategories = await sub_category_collection.find(
            {"$or": [{"created_by": None}, {"created_by": user_id}]}
        ).to_list(None)
    return [SubCategoryOut(**subCat) for subCat in subCategories]  


async def getAllSubCategories():
    subCategories = await sub_category_collection.find().to_list(None)

    for subCat in subCategories:
        if "category_id" in subCat and isinstance(subCat["category_id"], ObjectId):
            subCat["category_id"] = str(subCat["category_id"])

        category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
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
            category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
            if category:
                category["_id"] = str(category["_id"])  # Convert ObjectId to string
                subCat["category_id"] = category  

    return [SubCategoryOut(**subCat) for subCat in subCategories]
