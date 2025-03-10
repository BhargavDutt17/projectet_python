from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from bson import ObjectId

class CreatedBy(BaseModel):
    user_id: str
    role: str

class Transaction(BaseModel):
    category_id: str  # Stores Category ID instead of name
    subcategory_id: str  # Stores Subcategory ID instead of name
    amount: float
    date: str  # Date format "YYYY-MM-DD"
    description: Optional[str] = ""
    created_by: CreatedBy  # Stores user_id & role

class TransactionOut(Transaction):
    id: str = Field(alias="_id")
    category: Optional[Dict[str, Any]] = None  # Stores category details
    subcategory: Optional[Dict[str, Any]] = None  # Stores subcategory details

    @validator("id", pre=True, always=True)
    def convert_objectId(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("category", pre=True, always=True)
    def convert_category(cls, v):
        if isinstance(v, Dict) and "_id" in v:
            v["_id"] = str(v["_id"])  # Convert ObjectId to string
        return v

    @validator("subcategory", pre=True, always=True)
    def convert_subcategory(cls, v):
        if isinstance(v, Dict) and "_id" in v:
            v["_id"] = str(v["_id"])  # Convert ObjectId to string
        return v
