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
from typing import Optional , List


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
            sub_category_dict["role_name"] = role["name"].lower()
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


async def getAllSubCategories(user_id: str = None, role_id: str = None):
    try:
        query = {}
        role_name = "user"

        # Determine role_name from role_id
        if role_id:
            role = await role_collection.find_one({"_id": ObjectId(role_id)})
            if role:
                role_name = role["name"].lower()
            else:
                raise HTTPException(status_code=400, detail="Invalid role_id provided")
            print(f"Role: {role_name}, User ID: {user_id}, Query: {query}")

        # Validate user_id if not admin
        if role_name != "admin" and not user_id:
            raise HTTPException(status_code=400, detail="user_id is required for non-admin users")

        # Build query based on role
        if role_name == "admin":
            query["role_name"] = "admin"
        else:
            query = {
                "user_id": user_id,
                "role_name": "user"
            }
            print(f"Query being executed: {query}")


        subCategories = await sub_category_collection.find(query).to_list(None)
        print(f"Fetched subCategories: {subCategories}")  # Log fetched data


        for subCat in subCategories:
            subCat["_id"] = str(subCat["_id"])
            subCat["user_id"] = str(subCat["user_id"]) if subCat.get("user_id") else None
            subCat["category_id"] = str(subCat["category_id"])

            user = await user_collection.find_one({"_id": ObjectId(subCat["user_id"])}) if subCat["user_id"] else None
            subCat["user_id"] = user if user else None

            category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
            subCat["category_id"] = category if category else None

            if subCat.get("role_id"):
                role = await role_collection.find_one({"_id": ObjectId(subCat["role_id"])})
                subCat["role_id"] = {"_id": str(role["_id"]), "name": role["name"]} if role else None
            else:
                subCat["role_id"] = None

            subCat["role_name"] = subCat.get("role_name", "user")
            

        return [SubCategoryOut(**subCat) for subCat in subCategories]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching all subcategories: {str(e)}"
        )


async def getSubCategoryByCategoryId(category_id: str, user_id: Optional[str] = None, role_id: Optional[str] = None):
    try:
        filters = {}
        role_name = "user"

        if role_id:
            role = await role_collection.find_one({"_id": ObjectId(role_id)})
            if role:
                role_name = role["name"].lower()
            else:
                raise HTTPException(status_code=400, detail="Invalid role_id provided")

        if category_id.lower() == "all":
            if role_name == "admin":
                filters["role_name"] = "admin"
            else:
                filters = {
            "user_id": ObjectId(user_id),
            "role_name": "user"
            }

        else:
            if role_name == "admin":
                filters = {
                    "category_id": category_id,
                    "role_name": "admin"
                }
            else:
                filters["$or"] = [
                    {"category_id": category_id, "user_id": user_id},
                    {"category_id": category_id, "role_name": "admin"},
                ]

        subCategories = await sub_category_collection.find(filters).to_list(None)

        for subCat in subCategories:
            subCat["_id"] = str(subCat["_id"])
            subCat["user_id"] = str(subCat["user_id"]) if subCat.get("user_id") else None
            subCat["category_id"] = str(subCat["category_id"])

            user = await user_collection.find_one({"_id": ObjectId(subCat["user_id"])}) if subCat["user_id"] else None
            subCat["user_id"] = user if user else None

            category = await category_collection.find_one({"_id": ObjectId(subCat["category_id"])})
            subCat["category_id"] = category if category else None

            if subCat.get("role_id"):
                role = await role_collection.find_one({"_id": ObjectId(subCat["role_id"])})
                subCat["role_id"] = {"_id": str(role["_id"]), "name": role["name"]} if role else None
            else:
                subCat["role_id"] = None

            subCat["role_name"] = subCat.get("role_name", "user")

        return [SubCategoryOut(**subCat) for subCat in subCategories]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subcategories: {str(e)}")



async def deleteSubCategory(subcategory_id: str):
    try:
        result = await sub_category_collection.delete_one({"_id": ObjectId(subcategory_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="SubCategory not found")
        return {"message": "SubCategory deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting subcategory: {str(e)}")
    

# Delete selected subcategories by IDs
async def deleteSelectedSubCategories(sub_category_ids: List[str]):
    if not all(ObjectId.is_valid(sub_cat_id) for sub_cat_id in sub_category_ids):
        raise HTTPException(status_code=400, detail="Invalid subcategory IDs")

    object_ids = [ObjectId(sub_cat_id) for sub_cat_id in sub_category_ids]
    result = await sub_category_collection.delete_many({"_id": {"$in": object_ids}})

    if result.deleted_count > 0:
        return JSONResponse(
            content={"message": f"{result.deleted_count} subcategories deleted successfully"},
            status_code=200,
        )
    else:
        raise HTTPException(status_code=404, detail="No subcategories found to delete")


# Delete all subcategories based on role
async def deleteAllSubCategories(user_id: str, role_id: str):
    if not user_id.strip() or not role_id.strip():
        raise HTTPException(status_code=400, detail="Missing user_id or role_id")

    # Fetch role to determine if it's admin
    try:
        role = await role_collection.find_one({"_id": ObjectId(role_id)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid role_id: {e}")

    if not role or "name" not in role:
        raise HTTPException(status_code=400, detail="Invalid role_id")

    role_name = role["name"].lower()

    # Build query based on role
    if role_name == "admin":
        query = {"role_name": "admin"}
    else:
        query = {"user_id": user_id}  # Keep as string to match your DB

    # Delete matching subcategories
    result = await sub_category_collection.delete_many(query)

    if result.deleted_count > 0:
        return JSONResponse(
            content={"message": f"{result.deleted_count} subcategories deleted successfully"},
            status_code=200,
        )
    else:
        raise HTTPException(status_code=404, detail="No subcategories found to delete")


async def editSubCategory(sub_category_id: str, updated_data: dict):
    try:
        if not ObjectId.is_valid(sub_category_id):
            raise HTTPException(status_code=400, detail="Invalid SubCategory ID format.")

        existing_sub_category = await sub_category_collection.find_one({"_id": ObjectId(sub_category_id)})
        if not existing_sub_category:
            raise HTTPException(status_code=404, detail="SubCategory not found.")

        allowed_fields = ["name", "description", "category_id"]
        update_fields = {key: updated_data[key] for key in allowed_fields if key in updated_data}

        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        await sub_category_collection.update_one(
            {"_id": ObjectId(sub_category_id)},
            {"$set": update_fields}
        )

        return {"message": "SubCategory updated successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating subcategory: {str(e)}")
