from pydantic import BaseModel, Field
import bcrypt
from typing import Optional, Dict, Any

class User(BaseModel):
    username: str
    email: str
    password: str
    inviteCode: Optional[str] = None  # ✅ Invite code is now optional
    role_id: Optional[str] = None
    status: str = "active"

    def hash_password(self):
        """Hashes the user's password before saving it to the database."""
        self.password = bcrypt.hashpw(self.password.encode(), bcrypt.gensalt()).decode()

class UserOut(User):
    id: str = Field(alias="_id")
    role: Optional[Dict[str, Any]] = None  # Store role details

    @classmethod
    def from_mongo(cls, data):
        """Converts MongoDB ObjectId to string and returns UserOut instance."""
        data["id"] = str(data["_id"])
        data["role_id"] = str(data["role_id"])
        
        if "role" in data and isinstance(data["role"], dict):
            data["role"]["_id"] = str(data["role"]["_id"])  # Convert role ID to string
        
        return cls(**data)

# ✅ Add UserLogin model
class UserLogin(BaseModel):
    email: str
    password: str
