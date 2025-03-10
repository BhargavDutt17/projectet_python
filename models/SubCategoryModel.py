from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from bson import ObjectId

class CreatedBy(BaseModel):  # CreatedBy model for storing user_id & role
    user_id: str
    role: str

class SubCategory(BaseModel):
    name: str
    description: str
    category_id: str
    created_by: Optional[CreatedBy] = None  # Stores user_id & role

class SubCategoryOut(SubCategory):
    id: str = Field(alias="_id") 
    category_id: Optional[str] = None  

    @validator("id", pre=True, always=True)
    def convert_objectId(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("category_id", pre=True, always=True)
    def convert_categoryId(cls, v):
        return str(v) if isinstance(v, ObjectId) else v
    
    @validator("created_by", pre=True, always=True)
    def convert_createdBy(cls, v):
        if isinstance(v, dict) and "user_id" in v and "role" in v:
            return v
        return None
