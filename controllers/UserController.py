from models.UserModel import User, UserOut, UserLogin
from bson import ObjectId
from config.database import user_collection, role_collection
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import bcrypt
from utils.SendMail import send_mail

# Temporary admin invite code (change/remove when proper role assignment is implemented)
ADMIN_INVITE_CODE = "ADMIN123"

async def addUser(user: User):
    # Assign role based on invite code
    if user.inviteCode == ADMIN_INVITE_CODE:
        role = await role_collection.find_one({"name": "admin"})
    else:
        role = await role_collection.find_one({"name": "user"})
    
    if not role:
        raise HTTPException(status_code=500, detail="Role not found in database")
    
    user.role_id = ObjectId(role["_id"])  # Convert role ID to ObjectId
    
    result = await user_collection.insert_one(user.dict())
    send_mail(user.email,"User Created","User created successfully")
    return JSONResponse(status_code=201, content={"message": "User created successfully"})

async def getAllUsers():
    users = await user_collection.find().to_list(length=None)
    for user in users:
        if "role_id" in user and isinstance(user["role_id"], ObjectId):
            user["role_id"] = str(user["role_id"])
        role = await role_collection.find_one({"_id": ObjectId(user["role_id"])});
        if role:
            role["_id"] = str(role["_id"])
            user["role"] = role
    return [UserOut(**user) for user in users]

async def loginUser(request: UserLogin):
    foundUser = await user_collection.find_one({"email": request.email})
    if not foundUser:
        raise HTTPException(status_code=404, detail="User not found")
    
    foundUser["_id"] = str(foundUser["_id"])
    foundUser["role_id"] = str(foundUser["role_id"])
    
    if "password" in foundUser and bcrypt.checkpw(request.password.encode(), foundUser["password"].encode()):
        role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])});
        foundUser["role"] = role
        return {"message": "User login success", "user": UserOut(**foundUser)}
    else:
        raise HTTPException(status_code=404, detail="Invalid password")
