from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from bson import ObjectId
import bcrypt

class User(BaseModel):
    firstName: str
    lastName: str
    username: str
    email: EmailStr
    password: str
    inviteCode: Optional[str] = ""
    role_id: str = ""
    status: str = "active"
    profile_image: Optional[str] = None  # Profile image URL

    @validator("password", pre=True, always=True)
    def encrypt_password(cls, v):
        return bcrypt.hashpw(v.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

class UserOut(User):
    id: str = Field(alias="_id")
    role: Optional[Dict[str, Any]] = None

    @validator("id", pre=True, always=True)
    def convert_objectId(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

    @validator("role", pre=True, always=True)
    def convert_role(cls, v):
        if isinstance(v, dict) and "_id" in v:
            v["_id"] = str(v["_id"])
        return v

class UserLogin(BaseModel):
    email_or_username: str  # Accepts either email or username
    password: str
