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
from apscheduler.jobstores.base import JobLookupError


# Temporary admin invite code
ADMIN_INVITE_CODE = "ADMIN123"

scheduled_deletion_jobs = {}
scheduled_deactivation_jobs = {}
admin_scheduled_deactivation_jobs = {}
admin_scheduled_deletion_jobs = {}
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
    try:
        users = await user_collection.find().to_list(None)

        for user in users:
            user["_id"] = str(user["_id"])
            user["role_id"] = str(user["role_id"])

            # Fetch and Convert Role
            role = await role_collection.find_one({"_id": ObjectId(user["role_id"])})
            user["role"] = {
                "_id": str(role["_id"]),
                "name": role["name"]
            } if role else None

        return [UserOut(**user) for user in users]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


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
    # Step 1: Check if user exists with either email or username
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

    user_id = str(foundUser["_id"])

    # Step 2: Validate password before any cancellation
    if not bcrypt.checkpw(request.password.encode(), foundUser["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Step 3: Cancel SELF-TRIGGERED DEACTIVATION
    if (
        foundUser["status"] == "pending_deactivation"
        and user_id in scheduled_deactivation_jobs
        and user_id not in admin_scheduled_deactivation_jobs
    ):
        try:
            scheduled_deactivation_jobs[user_id].remove()
        except Exception as e:
            print(f"[WARNING] Failed to cancel self-deactivation for user {user_id}: {str(e)}")
        scheduled_deactivation_jobs.pop(user_id, None)
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "active"}}
        )
        print(f"[INFO] User {user_id} cancelled self-deactivation by logging in.")

    # Step 4: Cancel SELF-TRIGGERED DELETION
    if (
        foundUser["status"] == "pending_deletion"
        and user_id in scheduled_deletion_jobs
        and user_id not in admin_scheduled_deletion_jobs
    ):
        try:
            scheduled_deletion_jobs[user_id].remove()
        except Exception as e:
            print(f"[WARNING] Failed to cancel self-deletion for user {user_id}: {str(e)}")
        scheduled_deletion_jobs.pop(user_id, None)
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "active"}}
        )
        print(f"[INFO] User {user_id} cancelled self-deletion by logging in.")

    # Step 5: Re-fetch user after potential cancellations
    foundUser = await user_collection.find_one({"_id": ObjectId(user_id)})

   # Step 6: Block login if status is not active
    if foundUser["status"] == "pending_deactivation" and user_id in admin_scheduled_deactivation_jobs:
       raise HTTPException(status_code=403, detail="Your account is being deactivated by the admin. Please contact support.")

    if foundUser["status"] == "pending_deletion" and user_id in admin_scheduled_deletion_jobs:
       raise HTTPException(status_code=403, detail="Your account is being deleted by the admin. Please contact support.")

    if foundUser["status"] != "active":
       raise HTTPException(status_code=403, detail="User is deactivated or pending admin action")

    # Step 7: Final formatting and return
    foundUser["_id"] = str(foundUser["_id"])
    foundUser["role_id"] = str(foundUser["role_id"])
    role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])})
    foundUser["role"] = role

    return {"message": "User login success", "user": UserOut(**foundUser)}

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

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": "pending_deactivation"}}
    )
    if role == "admin":
     schedule_admin_deactivate(user_id)
    else:
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

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": "pending_deletion"}}
    )
    if role == "admin":
     schedule_admin_delete(user_id, user["email"])
    else:
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
    user_id = str(user_id)  # Ensure it's a string key

    if user_id in scheduled_deactivation_jobs:
        try:
            scheduled_deactivation_jobs[user_id].remove()
        except JobLookupError:
            print(f"[WARNING] No scheduled deactivation job found for user: {user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to remove deactivation job for user {user_id}: {str(e)}")
        scheduled_deactivation_jobs.pop(user_id, None)

    job = scheduler.add_job(
        lambda: loop.create_task(deactivate_user(user_id)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=2),
    )
    scheduled_deactivation_jobs[user_id] = job

def schedule_delete(user_id: str, email: str):
    loop = asyncio.get_event_loop()

    # Cancel any existing deletion job for this user
    if user_id in scheduled_deletion_jobs:
        try:
           scheduled_deletion_jobs[user_id].remove()
        except JobLookupError:
         print(f"[WARNING] Scheduled deletion job not found for user {user_id}")
        except Exception as e:
         print(f"[ERROR] Failed to remove deletion job for {user_id}: {str(e)}")
    scheduled_deletion_jobs.pop(user_id, None)


    # Schedule new deletion
    job = scheduler.add_job(
        lambda: loop.create_task(delete_user(user_id, email)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=3),
    )

    # Store the job reference
    scheduled_deletion_jobs[user_id] = job
    
def schedule_admin_deactivate(user_id: str):
    loop = asyncio.get_event_loop()
    if user_id in admin_scheduled_deactivation_jobs:
        try:
            admin_scheduled_deactivation_jobs[user_id].remove()
        except JobLookupError:
            print(f"[Admin] No deactivation job found for user {user_id}")
    admin_scheduled_deactivation_jobs.pop(user_id, None)

    job = scheduler.add_job(
        lambda: loop.create_task(deactivate_user(user_id)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=2),
    )
    admin_scheduled_deactivation_jobs[user_id] = job

def schedule_admin_delete(user_id: str, email: str):
    loop = asyncio.get_event_loop()
    if user_id in admin_scheduled_deletion_jobs:
        try:
            admin_scheduled_deletion_jobs[user_id].remove()
        except JobLookupError:
            print(f"[Admin] No deletion job found for user {user_id}")
    admin_scheduled_deletion_jobs.pop(user_id, None)

    job = scheduler.add_job(
        lambda: loop.create_task(delete_user(user_id, email)),
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=3),
    )
    admin_scheduled_deletion_jobs[user_id] = job

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

# Reactivate User Account
async def activateUser(request: UserLogin):
    user = await user_collection.find_one({
        "$or": [
            {"email": request.email_or_username},
            {"username": request.email_or_username}
        ]
    })

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["status"] not in ["inactive", "pending_deactivation"]:
       return {"status": False, "message": "Account cannot be reactivated in its current state"}


    # Allow admin to activate without password
    if getattr(request, "role", None) != "admin":
        if not bcrypt.checkpw(request.password.encode(), user["password"].encode()):
            raise HTTPException(status_code=401, detail="Incorrect password")

    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"status": "active"}}
    )

    return {"status": True, "message": "Account reactivated successfully"}

# Admin Cancel Deletion (Supports both user- and admin-triggered deletions)
async def cancel_user_deletion(user_id: str):
    try:
        deleted = False

        # ✅ Cancel user-triggered deletion
        if user_id in scheduled_deletion_jobs:
            scheduled_deletion_jobs[user_id].remove()
            scheduled_deletion_jobs.pop(user_id, None)
            deleted = True

        # ✅ Cancel admin-triggered deletion
        if user_id in admin_scheduled_deletion_jobs:
            admin_scheduled_deletion_jobs[user_id].remove()
            admin_scheduled_deletion_jobs.pop(user_id, None)
            deleted = True

        if deleted:
            await user_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"status": "active"}}
            )
            print(f"[ADMIN] Cancelled scheduled deletion for user {user_id}")
            return {"message": "User deletion cancelled by admin"}
        else:
            raise HTTPException(status_code=404, detail="No scheduled deletion found for this user")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling deletion: {str(e)}")

