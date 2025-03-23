from models.SubCategoryModel import SubCategory, SubCategoryOut
from bson import ObjectId
from config.database import (
    sub_category_collection,
    category_collection,
    user_collection,
    role_collection,
)
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional


async def addSubCategory(sub_category: SubCategory):
    try:
        sub_category_dict = sub_category.dict()
        sub_category_dict["_id"] = ObjectId()
        sub_category_dict["category_id"] = str(sub_category_dict["category_id"])
        sub_category_dict["role_id"] = str(sub_category_dict["role_id"])
        sub_category_dict["user_id"] = (
            str(sub_category_dict["user_id"]) if sub_category_dict["user_id"] else None
        )

        # Fetch `role_name` from `role_collection` using `role_id`
        role = await role_collection.find_one(
            {"_id": ObjectId(sub_category_dict["role_id"])}
        )
        if role:
            sub_category_dict["role_name"] = role[
                "name"
            ].lower()  #Normalize role name (e.g., "Admin" → "admin")
        else:
            raise HTTPException(status_code=400, detail="Invalid role_id provided")

        await sub_category_collection.insert_one(sub_category_dict)
        return JSONResponse(
            content={"message": "SubCategory saved successfully!!"}, status_code=201
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding subcategory: {str(e)}"
        )


async def getAllSubCategories():
    try:
        subCategories = await sub_category_collection.find().to_list(None)

        for subCat in subCategories:
            subCat["_id"] = str(subCat["_id"])
            subCat["user_id"] = (
                str(subCat["user_id"]) if subCat.get("user_id") else None
            )
            subCat["category_id"] = str(subCat["category_id"])

            # Fetch User Details (Admin or Regular User)
            user = (
                await user_collection.find_one({"_id": ObjectId(subCat["user_id"])})
                if subCat["user_id"]
                else None
            )
            subCat["user_id"] = user if user else None

            # Fetch Category Details
            category = await category_collection.find_one(
                {"_id": ObjectId(subCat["category_id"])}
            )
            subCat["category_id"] = category if category else None

            # Fetch Role Details & Convert `role_id` to Dictionary
            if subCat.get("role_id"):
                role = await role_collection.find_one(
                    {"_id": ObjectId(subCat["role_id"])}
                )
                subCat["role_id"] = (
                    {"_id": str(role["_id"]), "name": role["name"]} if role else None
                )
            else:
                subCat["role_id"] = None  # Prevents validation error

            # Ensure `role_name` is assigned
            subCat["role_name"] = role["name"].lower() if role else "user"

        return [SubCategoryOut(**subCat) for subCat in subCategories]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching all subcategories: {str(e)}"
        )


async def getSubCategoryByCategoryId(category_id: str, user_id: Optional[str] = None, role_id: Optional[str] = None):
    try:
        filters = {}

        # # Debugging: Print received parameters
        # print(f"Received category_id: {category_id}, user_id: {user_id}, role_id: {role_id}")

        # If category_id is "all", fetch all subcategories for the user
        if category_id.lower() == "all":
            filters["user_id"] = user_id
        else:
            filters["category_id"] = category_id

        # Fetch `role_name` using `role_id`
        role_name = "user"
        if role_id:
            role = await role_collection.find_one({"_id": ObjectId(role_id)})
            if role:
                role_name = role["name"].lower()

        # Fetch both admin subcategories & user-defined subcategories
        if role_name != "admin":
            filters["$or"] = [
                {"user_id": user_id},
                {"role_name": "admin"}
            ]

        # # Debugging: Print MongoDB query filters
        # print(f"MongoDB Query Filters: {filters}")

        subCategories = await sub_category_collection.find(filters).to_list(None)

        # # Debugging: Print fetched subcategories
        # print(f"Fetched Subcategories from MongoDB: {subCategories}")

        for subCat in subCategories:
            subCat["_id"] = str(subCat["_id"])
            subCat["user_id"] = str(subCat["user_id"]) if subCat.get("user_id") else None
            subCat["category_id"] = str(subCat["category_id"])
            
             # Fetch the category name (Income/Expense)
            category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
            subCat["category_type"] = category["name"].lower() if category else "unknown"
            
            # Remove "(Userdefined)" from the description if it exists
            if "description" in subCat and isinstance(subCat["description"], str):
                subCat["description"] = subCat["description"].replace("(Userdefined)", "").strip()

            # Fetch Role Details & Convert `role_id` to Dictionary
            if subCat.get("role_id"):
                role = await role_collection.find_one({"_id": ObjectId(subCat["role_id"])})
                subCat["role_id"] = {"_id": str(role["_id"]), "name": role["name"]} if role else None
            else:
                subCat["role_id"] = None  # Prevents validation error

            subCat["role_name"] = subCat.get("role_name", "user").capitalize()

        return subCategories

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subcategories: {str(e)}")
