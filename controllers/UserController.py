from models.UserModel import User, UserOut, UserLogin
from bson import ObjectId
from config.database import user_collection, role_collection
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
import bcrypt
from utils.SendMail import send_mail
from utils.CloudinaryUtil import upload_image  # Import Cloudinary upload function

# Temporary admin invite code
ADMIN_INVITE_CODE = "ADMIN123"

async def addUser(firstName: str, lastName: str, username: str, email: str, password: str, inviteCode: str, status: str, profile_image: UploadFile):
    # Assign role based on invite code
    if inviteCode == ADMIN_INVITE_CODE:
        role = await role_collection.find_one({"name": "admin"})
    else:
        role = await role_collection.find_one({"name": "user"})

    if not role:
        raise HTTPException(status_code=500, detail="Role not found in database")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Handle profile image upload
    image_url = None
    if profile_image:
       image_url = await upload_image(profile_image)  # `profile_image.read()` is now awaited inside `upload_image`


    user_data = {
        "firstName": firstName,
        "lastName": lastName,
        "username": username,
        "email": email,
        "password": hashed_password,
        "inviteCode": inviteCode,
       "role_id": role["_id"],  # Store it as ObjectId instead of string
        "status": status,
        "profile_image": image_url
    }

    await user_collection.insert_one(user_data)
    send_mail(email, "User Created", "User created successfully")
    return JSONResponse(status_code=201, content={"message": "User created successfully"})

async def uploadUserProfileImage(user_id: str, image: UploadFile):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_url = await upload_image(image)
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"profile_image": image_url}})

    return JSONResponse(status_code=200, content={"message": "Profile image updated successfully", "profile_image": image_url})

async def getAllUsers():
    users = await user_collection.find().to_list(length=None)
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user["role_id"] = str(user["role_id"])  # Convert ObjectId to string

        role = await role_collection.find_one({"_id": user["role_id"]})  # Query with ObjectId
        if role:
            user["role"] = {"_id": str(role["_id"]), "name": role["name"]}

    return [UserOut(**user) for user in users]


async def getUserProfile(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user["username"],
        "profile_image": user.get("profile_image", None)
    }



async def loginUser(request: UserLogin):
    # Check if user exists with either email or username
    foundUser = await user_collection.find_one({
        "$or": [{"email": request.email_or_username}, {"username": request.email_or_username}]
    })

    if not foundUser:
        raise HTTPException(status_code=404, detail="User not found")

    foundUser["_id"] = str(foundUser["_id"])
    foundUser["role_id"] = str(foundUser["role_id"])

    if "password" in foundUser and bcrypt.checkpw(request.password.encode(), foundUser["password"].encode()):
        role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])})
        foundUser["role"] = role
        return {"message": "User login success", "user": UserOut(**foundUser)}
    else:
        raise HTTPException(status_code=404, detail="Invalid password")

