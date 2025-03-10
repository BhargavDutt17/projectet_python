from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from bson import ObjectId

class CreatedBy(BaseModel):  # ✅ CreatedBy model for storing user_id & role
    user_id: str
    role: str

class SubCategory(BaseModel):
    name: str
    description: str
    category_id: str
    created_by: Optional[CreatedBy] = None  # ✅ Stores user_id & role

class SubCategoryOut(SubCategory):
    id: str = Field(alias="_id") 
    category_id: Optional[Dict[str, Any]] = None  

    @validator("id", pre=True, always=True)
    def convert_objectId(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("category_id", pre=True, always=True)
    def convert_categoryId(cls, v):
        if isinstance(v, Dict) and "_id" in v:
            v["_id"] = str(v["_id"])
        return v
    
    @validator("created_by", pre=True, always=True)
    def convert_createdBy(cls, v):
        if isinstance(v, dict) and "user_id" in v:
           return v["user_id"]
        return v

    # @validator("created_by", pre=True, always=True)
    # def convert_createdBy(cls, v):
    #     if isinstance(v, ObjectId):
    #        return str(v)  # Convert ObjectId to string
    #     elif isinstance(v, dict) and "user_id" in v and "role" in v:
    #         return v  # Keep it as a dictionary
    #     return None

