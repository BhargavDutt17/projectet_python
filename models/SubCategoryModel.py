from pydantic import BaseModel,Field,validator
from typing import List, Optional,Dict,Any
from bson import ObjectId

class SubCategory(BaseModel):
    user_id: str
    role_id: str
    name: str
    description: str
    category_id:str
    

class SubCategoryOut(SubCategory):
    id:str = Field(alias='_id') 
    user_id: Optional[Dict[str,Any]]= None
    category_id: Optional[Dict[str, Any]] = None
    role_id: Optional[Dict[str,Any]] = None


    @validator('id', pre=True, always=True)
    def convert_obectId(cls,v):
        if isinstance(v,ObjectId):
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
