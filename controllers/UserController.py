from models.UserModel import User, UserOut, UserLogin
from bson import ObjectId
from config.database import user_collection, role_collection, deleted_user_collection
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
import bcrypt
from utils.SendMail import send_mail
from utils.CloudinaryUtil import upload_image  # Import Cloudinary upload function
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

# Temporary admin invite code
ADMIN_INVITE_CODE = "ADMIN123"

scheduled_deletion_jobs = {}
scheduled_deactivation_jobs = {}
scheduler = BackgroundScheduler()
scheduler.start()


async def addUser(
    firstName: str,
    lastName: str,
    username: str,
    email: str,
    password: str,
    inviteCode: str,
    status: str,
    profile_image: UploadFile,
):
    # Assign role based on invite code
    if inviteCode == ADMIN_INVITE_CODE:
        role = await role_collection.find_one({"name": "admin"})
    else:
        role = await role_collection.find_one({"name": "user"})

    if not role:
        raise HTTPException(status_code=500, detail="Role not found in database")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

    # Handle profile image upload
    image_url = None
    if profile_image:
        image_url = await upload_image(
            profile_image
        )  # `profile_image.read()` is now awaited inside `upload_image`

    user_data = {
        "firstName": firstName,
        "lastName": lastName,
        "username": username,
        "email": email,
        "password": hashed_password,
        "inviteCode": inviteCode,
        "role_id": role["_id"],  # Store it as ObjectId instead of string
        "status": status,
        "profile_image": image_url,
    }

    await user_collection.insert_one(user_data)
    send_mail(email, "User Created", "User created successfully")
    return JSONResponse(
        status_code=201, content={"message": "User created successfully"}
    )


async def uploadUserProfileImage(user_id: str, image: UploadFile):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_url = await upload_image(image)
    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"profile_image": image_url}}
    )

    return JSONResponse(
        status_code=200,
        content={
            "message": "Profile image updated successfully",
            "profile_image": image_url,
        },
    )


async def getAllUsers():
    users = await user_collection.find().to_list(length=None)
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        user["role_id"] = str(user["role_id"])  # Convert ObjectId to string

        role = await role_collection.find_one(
            {"_id": user["role_id"]}
        )  # Query with ObjectId
        if role:
            user["role"] = {"_id": str(role["_id"]), "name": role["name"]}

    return [UserOut(**user) for user in users]


async def getUserProfile(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user["username"],
        "email": user["email"],
        "profile_image": user.get("profile_image", None),
    }


async def loginUser(request: UserLogin):
    # Check if user exists with either email or username
    foundUser = await user_collection.find_one(
        {
            "$or": [
                {"email": request.email_or_username},
                {"username": request.email_or_username},
            ]
        }
    )

    if not foundUser:
        raise HTTPException(status_code=404, detail="User not found")

    if foundUser.get("status") != "active":
        raise HTTPException(status_code=403, detail="User is deactivated")

    # Cancel scheduled deletion if exists
    user_id = str(foundUser["_id"])
    if user_id in scheduled_deletion_jobs:
        scheduled_deletion_jobs[user_id].remove()
        scheduled_deletion_jobs.pop(user_id)
        print(f"Canceled scheduled deletion for user: {user_id}")

    # Cancel scheduled deactivation if exists
    if user_id in scheduled_deactivation_jobs:
        scheduled_deactivation_jobs[user_id].remove()
        scheduled_deactivation_jobs.pop(user_id)
        print(f"Canceled scheduled deactivation for user: {user_id}")

    foundUser["_id"] = str(foundUser["_id"])
    foundUser["role_id"] = str(foundUser["role_id"])

    if "password" in foundUser and bcrypt.checkpw(
        request.password.encode(), foundUser["password"].encode()
    ):
        role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])})
        foundUser["role"] = role
        return {"message": "User login success", "user": UserOut(**foundUser)}
    else:
        raise HTTPException(status_code=404, detail="Invalid password")


# Update Username
async def update_username(user_id: str, new_username: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"username": new_username}}
    )
    return {"message": "Username updated successfully"}


# Update Email
async def update_email(user_id: str, new_email: str):
    existing_user = await user_collection.find_one({"email": new_email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"email": new_email}}
    )
    return {"message": "Email updated successfully"}


# Change Password
async def change_password(
    user_id: str, current_password: str, new_password: str, confirm_password: str
):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if current password matches
    if not bcrypt.checkpw(current_password.encode(), user["password"].encode()):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Ensure new password and confirm password match
    if new_password != confirm_password:
        raise HTTPException(
            status_code=400, detail="New password and confirm password do not match"
        )

    # Hash the new password
    hashed_password = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}}
    )
    return {"message": "Password updated successfully"}


# Trigger Deactivate
async def trigger_user_deactivation(user_id: str, role: str, password: str = None):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if role != "admin":
        if not password or not bcrypt.checkpw(
            password.encode(), user["password"].encode()
        ):
            raise HTTPException(status_code=403, detail="Invalid password")

    schedule_deactivate(user_id)
    return {"message": "User deactivation scheduled. Will be inactive in 1 minute."}


# Trigger Delete
async def trigger_user_deletion(user_id: str, role: str, password: str = None):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if role != "admin":
        if not password or not bcrypt.checkpw(
            password.encode(), user["password"].encode()
        ):
            raise HTTPException(status_code=403, detail="Invalid password")

    schedule_delete(user_id, user["email"])
    return {"message": "User deletion scheduled. Will be deleted in 1 minute."}


# Update Profile Picture
async def update_profile_picture(user_id: str, image: UploadFile):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Upload new image to Cloudinary
    image_url = await upload_image(image)

    # Update the database with the new image URL
    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"profile_image": image_url}}
    )

    return {
        "message": "Profile picture updated successfully",
        "profile_image": image_url,
    }


# Helper: Schedule deactivation using global scheduler
def schedule_deactivate(user_id: str):
    loop = asyncio.get_event_loop()

    # Cancel previous job if exists
    if user_id in scheduled_deactivation_jobs:
        scheduled_deactivation_jobs[user_id].remove()
        scheduled_deactivation_jobs.pop(user_id)

    # Schedule deactivation
    job = scheduler.add_job(
        lambda: loop.create_task(deactivate_user(user_id)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=1),
    )

    scheduled_deactivation_jobs[user_id] = job


def schedule_delete(user_id: str, email: str):
    loop = asyncio.get_event_loop()

    # Cancel any existing deletion job for this user
    if user_id in scheduled_deletion_jobs:
        old_job = scheduled_deletion_jobs.pop(user_id)
        old_job.remove()

    # Schedule new deletion
    job = scheduler.add_job(
        lambda: loop.create_task(delete_user(user_id, email)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=1),
    )

    # Store the job reference
    scheduled_deletion_jobs[user_id] = job


# APScheduler Task: Deactivate User
async def deactivate_user(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        print(f"User {user_id} not found.")
        return

    await user_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"status": "inactive"}}
    )
    print(f"User {user_id} deactivated.")


# APScheduler Task: Delete User
async def delete_user(user_id: str, email: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        print(f"User {user_id} not found.")
        return

    # ➕ Add status before archiving
    user["status"] = "permanently_deleted"

    # Move user to deleted_user_collection with status
    await deleted_user_collection.insert_one(user)

    # Delete user from main user collection
    await user_collection.delete_one({"_id": ObjectId(user_id)})

    print(f"User {email} deleted, archived, and marked as permanently_deleted.")
