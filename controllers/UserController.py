from models.UserModel import User, UserOut , UserLogin
from bson import ObjectId
from config.database import user_collection, role_collection
from fastapi import HTTPException
import bcrypt

async def addUser(user: User):
    """Registers a new user and assigns a role based on the invite code."""
    
    print("Received user data:", user.dict())  # ✅ Debugging: Print received data

    # Assign role based on invite code (if provided)
    role_name = "admin" if user.inviteCode and user.inviteCode == "SECRET123" else "user"
    role = await role_collection.find_one({"name": role_name})

    if not role:
        print("Error: Role not found")  # ✅ Debugging
        raise HTTPException(status_code=400, detail="Role not found")

    user.role_id = str(role["_id"])  # ✅ Convert role_id to string for MongoDB

    # ✅ Hash the password before storing it
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed_password

    # ✅ Insert user into MongoDB
    result = await user_collection.insert_one(user.dict(by_alias=True, exclude={"inviteCode"}))

    if result.inserted_id:
        print("User registered successfully!")  # ✅ Debugging
        return {"message": "User created successfully"}

    print("Error: User registration failed")  # ✅ Debugging
    raise HTTPException(status_code=500, detail="User registration failed")

async def getAllUsers():
    """Fetches all users with their role details."""
    users = await user_collection.find().to_list(None)

    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user["role_id"] = str(user["role_id"])  # Convert role_id to string

        role = await role_collection.find_one({"_id": ObjectId(user["role_id"])})
        if role:
            role["_id"] = str(role["_id"])  # Convert role ID to string
            user["role"] = role  # Attach role details

    return [UserOut.from_mongo(user) for user in users]

async def loginUser(request: UserLogin):
    """Handles user login and verifies credentials."""
    print("Checking user:", request.email)  # ✅ Debugging: Check email

    foundUser = await user_collection.find_one({"email": request.email})
    
    if not foundUser:
        print("User not found in database")  # ✅ Debugging
        raise HTTPException(status_code=404, detail="User not found")

    if foundUser["status"] != "active":
        raise HTTPException(status_code=403, detail="User account is not active")

    if bcrypt.checkpw(request.password.encode(), foundUser["password"].encode()):
        # ✅ Convert ObjectId to string
        foundUser["_id"] = str(foundUser["_id"])
        foundUser["role_id"] = str(foundUser["role_id"])

        # ✅ Fetch and attach role details, ensuring role_id is converted
        role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])})
        if role:
            role["_id"] = str(role["_id"])  # Convert role ObjectId to string
            foundUser["role"] = role
        else:
            foundUser["role"] = {"name": "user"}  # Default role

        return {"message": "Login successful", "user": foundUser}

    raise HTTPException(status_code=401, detail="Invalid password")



