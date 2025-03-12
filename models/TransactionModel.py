from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from bson import ObjectId


class Transaction(BaseModel):
    user_id: str
    role_id: str
    category_id: str  # Stores Category ID instead of name
    subcategory_id: str  # Stores Subcategory ID instead of name
    amount: float
    date: str  # Date format "YYYY-MM-DD"
    description: Optional[str] = ""

class TransactionOut(Transaction):
    id: str = Field(alias='_id')
    user_id: Optional[Dict[str,Any]]= None
    category_id: Optional[Dict[str, Any]] = None
    subcategory_id: Optional[Dict[str, Any]] = None
    role_id:Optional[Dict[str,Any]] = None
    
    @validator('id', pre=True, always=True)
    def convert_object(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    @validator('user_id', pre=True, always=True)
    def convert_userId(cls, v):
       
        if isinstance(v, ObjectId):
            return str(v)
        
        if isinstance(v, Dict):
            for key, value in v.items():
                if isinstance(value, ObjectId):
                    v[key] = str(value)
            return v
        
    @validator("role_id", pre=True, always=True)
    def convert_role(cls, v):
        if isinstance(v, dict) and "_id" in v:
            v["_id"] = str(v["_id"])  # Convert role _id to string
        return v

    @validator('category_id', pre=True, always=True)
    def convert_categoryId(cls,v):
        if isinstance(v,Dict) and "_id" in v:
            v["_id"] = str(v["_id"])
        return v
    

    @validator('subcategory_id', pre=True, always=True)
    def convert_subcategoryId(cls,v):
        if isinstance(v, ObjectId):
            return str(v)
        
        if isinstance(v, Dict):
            for key, value in v.items():
                if isinstance(value, ObjectId):
                    v[key] = str(value)
            return v
        
