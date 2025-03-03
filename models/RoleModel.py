from pydantic import BaseModel, Field, validator
from bson import ObjectId

class Role(BaseModel):
    name: str
    description: str

class RoleOut(Role):
    id: str = Field(alias="_id")

    @validator("id", pre=True, always=True)
    def convert_objectid(cls, v):
        """Ensures ObjectId is converted to a string."""
        return str(v) if isinstance(v, ObjectId) else v

    @classmethod
    def from_mongo(cls, data):
        """Converts MongoDB ObjectId to string and returns RoleOut instance."""
        data["_id"] = str(data["_id"])
        return cls(**data)
