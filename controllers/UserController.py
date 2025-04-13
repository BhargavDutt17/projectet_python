from models.UserModel import User, UserOut, UserLogin, ResetPasswordReq
from bson import ObjectId
from config.database import user_collection, role_collection, deleted_user_collection
from fastapi import HTTPException, UploadFile,Request
from fastapi.responses import JSONResponse
import bcrypt, asyncio
from utils.SendMail import send_mail
from utils.CloudinaryUtil import upload_image,delete_image
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from controllers.UserReportController import (
    generate_user_report,
    get_latest_user_report,
    get_user_report_by_id,
    get_all_user_reports,
    delete_user_report,
    delete_all_user_reports
)
import jwt

ADMIN_INVITE_CODE = "ADMIN123"
scheduled_deletion_jobs, scheduled_deactivation_jobs = {}, {}
admin_scheduled_deactivation_jobs, admin_scheduled_deletion_jobs = {}, {}
scheduler = BackgroundScheduler()
scheduler.start()

# -------------------------- USER CRUD -------------------------- #

async def addUser(firstName, lastName, username, email, password, inviteCode, status, profile_image: UploadFile):
    role = await role_collection.find_one({"name": "admin" if inviteCode == ADMIN_INVITE_CODE else "user"})
    if not role:
        raise HTTPException(status_code=500, detail="Role not found in database")

    image_info = await upload_image(profile_image) if profile_image else None
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    await user_collection.insert_one({
        "firstName": firstName, "lastName": lastName, "username": username, "email": email,
        "password": hashed_password, "inviteCode": inviteCode, "role_id": role["_id"],
        "status": status,
        "profile_image": image_info["secure_url"] if image_info else None,
        "public_id": image_info["public_id"] if image_info else None
    })
    loginlink=f"http://localhost:5173/login"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f0f4f8; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; padding: 30px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">

          <h2 style="text-align: center; color: #4B0082;">🎉 Welcome to Expense Tracker!</h2>
          <p style="font-size: 16px; color: #333;">Hi <strong>{firstName} {lastName}</strong>,</p>
          <p style="font-size: 15px; color: #444;">Your account has been successfully created. Below are your details:</p>

          <ul style="font-size: 15px; color: #444; line-height: 1.8;">
            <li><strong>Username:</strong> {username}</li>
            <li><strong>Email:</strong> {email}</li>
            <li><strong>Status:</strong> {status.capitalize()}</li>
            <li><strong>Role:</strong> {"Admin" if inviteCode == ADMIN_INVITE_CODE else "User"}</li>
          </ul>

          <div style="text-align: center; margin: 25px 0;">
            <a href={loginlink}
               style="background: linear-gradient(to right, #4B0082, #8A2BE2); color: white; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: bold;">
              🚀 Login to Your Account
            </a>
          </div>

          <div style="text-align: center; margin-top: 20px;">
            <img src="https://media.giphy.com/media/xUPGcgtKxm3yPvgpRK/giphy.gif" 
                 alt="Welcome" style="width: 100%; max-width: 300px; border-radius: 10px;" />
          </div>

          <p style="font-size: 14px; color: #888; text-align: center; margin-top: 30px;">
            Need help? Just reply to this email or visit our <a href={loginlink} style="color: #8A2BE2;">support center</a>.
          </p>

        </div>
      </body>
    </html>
    """

    send_mail(email, "🎉 Welcome to Expense Tracker!", body)
    return JSONResponse(status_code=201, content={"message": "User created successfully"})


async def getAllUsers():
    users = await user_collection.find().to_list(None)
    for user in users:
        user["_id"], user["role_id"] = str(user["_id"]), str(user["role_id"])
        role = await role_collection.find_one({"_id": ObjectId(user["role_id"])})
        user["role"] = {"_id": str(role["_id"]), "name": role["name"]} if role else None
    return [UserOut(**user) for user in users]


async def getUserProfile(user_id):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "email": user["email"], "profile_image": user.get("profile_image")}

async def update_profile_picture(user_id, image: UploadFile):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete old image if it exists
    old_public_id = user.get("public_id")
    if old_public_id:
        await delete_image(old_public_id)

    # Upload new image
    image_info = await upload_image(image)

    #  Update user document with new image info
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "profile_image": image_info["secure_url"],
                "public_id": image_info["public_id"]
            }
        }
    )

    return {
        "message": "Profile picture updated successfully",
        "profile_image": image_info["secure_url"]
    }

async def delete_profile_picture(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    public_id = user.get("public_id")
    if public_id:
        await delete_image(public_id)  # Deletes from Cloudinary

    # Remove profile image fields from DB
    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$unset": {"profile_image": "", "public_id": ""}}
    )

    return {"message": "Profile picture deleted successfully"}


async def uploadUserProfileImage(user_id, image: UploadFile):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User  not found")
    image_info = await upload_image(image)
    await user_collection.update_one(
    {"_id": ObjectId(user_id)},
    {
        "$set": {
            "profile_image": image_info["secure_url"],
            "public_id": image_info["public_id"]
        }
    }
    )
    return JSONResponse(status_code=200, content={"message": "Profile image updated", "profile_image": image_info["secure_url"]})


# -------------------------- LOGIN & AUTH -------------------------- #

async def loginUser(request: UserLogin):
    foundUser = await user_collection.find_one({
        "$or": [{"email": request.email_or_username}, {"username": request.email_or_username}]
    })
    if not foundUser:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = str(foundUser["_id"])

    if not bcrypt.checkpw(request.password.encode(), foundUser["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    if foundUser["status"] == "pending_deactivation" and user_id in scheduled_deactivation_jobs and user_id not in admin_scheduled_deactivation_jobs:
        scheduled_deactivation_jobs[user_id].remove()
        scheduled_deactivation_jobs.pop(user_id)
        await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active"}})

    if foundUser["status"] == "pending_deletion" and user_id in scheduled_deletion_jobs and user_id not in admin_scheduled_deletion_jobs:
        scheduled_deletion_jobs[user_id].remove()
        scheduled_deletion_jobs.pop(user_id)
        await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active"}})

    foundUser = await user_collection.find_one({"_id": ObjectId(user_id)})

    if foundUser["status"] == "pending_deletion":
        if user_id in admin_scheduled_deletion_jobs:
            raise HTTPException(status_code=423, detail=" Your account is being deleted by the admin. Contact support immediately.")
        raise HTTPException(status_code=409, detail=" Your account is scheduled for deletion. You can still cancel by logging in.")

    if foundUser["status"] == "pending_deactivation":
        if user_id in admin_scheduled_deactivation_jobs:
            raise HTTPException(status_code=423, detail=" Your account is being deactivated by the admin. Please contact support.")
        raise HTTPException(status_code=409, detail=" Your account is scheduled for deactivation. You can still cancel by logging in.")

    if foundUser["status"] != "active":
        raise HTTPException(status_code=423, detail="Your account is inactive.")

    foundUser["_id"], foundUser["role_id"] = str(foundUser["_id"]), str(foundUser["role_id"])
    role = await role_collection.find_one({"_id": ObjectId(foundUser["role_id"])})
    foundUser["role"] = role
    return {"message": "User login success", "user": UserOut(**foundUser)}

# -------------------------- PROFILE UPDATES -------------------------- #

async def update_username(user_id, new_username):
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": new_username}})
    return {"message": "Username updated successfully"}


async def update_email(user_id, new_email):
    if await user_collection.find_one({"email": new_email}):
        raise HTTPException(status_code=400, detail="Email already in use")
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"email": new_email}})
    return {"message": "Email updated successfully"}


async def change_password(user_id, current_password, new_password, confirm_password):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not bcrypt.checkpw(current_password.encode(), user["password"].encode()):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed}})
    return {"message": "Password updated successfully"}

# -------------------------- DEACTIVATE / DELETE -------------------------- #

async def trigger_user_deactivation(user_id, role, password=None):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if role != "admin" and (not password or not bcrypt.checkpw(password.encode(), user["password"].encode())):
        raise HTTPException(status_code=403, detail="Invalid password")
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "pending_deactivation"}})
    (schedule_admin_deactivate if role == "admin" else schedule_deactivate)(str(user_id))
    return {"message": "User deactivation scheduled."}


async def trigger_user_deletion(user_id, role, password=None):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if role != "admin" and (not password or not bcrypt.checkpw(password.encode(), user["password"].encode())):
        raise HTTPException(status_code=403, detail="Invalid password")
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "pending_deletion"}})
    (schedule_admin_delete if role == "admin" else schedule_delete)(str(user_id), user["email"])
    return {"message": "User deletion scheduled."}


async def cancel_user_deletion(user_id):
    deleted = False
    for job_dict in [scheduled_deletion_jobs, admin_scheduled_deletion_jobs]:
        if user_id in job_dict:
            job_dict[user_id].remove()
            job_dict.pop(user_id)
            deleted = True
    if deleted:
        await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active"}})
        return {"message": "User deletion cancelled by admin"}
    raise HTTPException(status_code=404, detail="No scheduled deletion found")


async def activateUser(request: UserLogin):
    user = await user_collection.find_one({
        "$or": [{"email": request.email_or_username}, {"username": request.email_or_username}]
    })
    if not user or user["status"] not in ["inactive", "pending_deactivation"]:
        return {"status": False, "message": "Account cannot be reactivated in current state"}

    if getattr(request, "role", None) != "admin" and not bcrypt.checkpw(request.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Incorrect password")

    await user_collection.update_one({"_id": user["_id"]}, {"$set": {"status": "active"}})
    return {"status": True, "message": "Account reactivated successfully"}

# -------------------------- SCHEDULERS -------------------------- #

def schedule_deactivate(user_id):
    _schedule(user_id, deactivate_user, 2, scheduled_deactivation_jobs)


def schedule_delete(user_id, email):
    _schedule(user_id, lambda: delete_user(user_id, email), 3, scheduled_deletion_jobs)


def schedule_admin_deactivate(user_id):
    _schedule(user_id, deactivate_user, 2, admin_scheduled_deactivation_jobs)


def schedule_admin_delete(user_id, email):
    _schedule(user_id, lambda: delete_user(user_id, email), 3, admin_scheduled_deletion_jobs)


def _schedule(user_id, task, minutes, job_dict):
    loop = asyncio.get_event_loop()
    if user_id in job_dict:
        try: job_dict[user_id].remove()
        except: pass
        job_dict.pop(user_id, None)
    job = scheduler.add_job(lambda: loop.create_task(task(user_id)), trigger="date", run_date=datetime.now() + timedelta(minutes=minutes))
    job_dict[user_id] = job


async def deactivate_user(user_id):
    await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "inactive"}})


async def delete_user(user_id, email):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user["status"] = "permanently_deleted"
        await deleted_user_collection.insert_one(user)
        await user_collection.delete_one({"_id": ObjectId(user_id)})
        
#---------------- Forget and Reset Password --------------#

SECRET_KEY = "royal"

def generate_token(email: str):
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {"sub": email, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

async def forgotPassword(email: str):
    foundUser = await user_collection.find_one({"email": email})
    if not foundUser:
        raise HTTPException(status_code=404, detail="Email not found")

    token = generate_token(email)
    resetLink = f"http://localhost:5173/resetpassword/{token}"
    username = foundUser.get("username", "user")

    body = f"""
<html>
  <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #000; color: #fff;">
    <div style="max-width: 600px; margin: auto; padding: 20px; border-radius: 12px; background: #fff; box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);">

      <!-- Header -->
      <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="color: #4B0082; font-size: 28px; margin: 0;">🔐 Password Reset</h2>
        <p style="font-size: 16px; color: #8A2BE2;">Click the button below to reset your password.</p>
      </div>

      <!-- Greeting -->
      <p style="font-size: 16px; color: #000;">Hey <strong>{username}</strong>,</p>
      <p style="font-size: 16px; color: #000;">It seems like you forgot your password.</p>
      <p style="font-size: 16px; color: #000;">
        Did <strong style="color: #4B0082;">Will Smith</strong> use one of those flashy thingies from Men in Black on you? 👽
      </p>

      <!-- Fun GIF -->
      <div style="text-align: center; margin: 20px 0;">
        <img src="https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExcng2azZ3MjB5bHdscGZlMTlndXdiMmk5bnNhMHQxa2YwMGQyYTEwcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wRc3lYsawNj20/giphy.gif"
             alt="Will Smith Flashy Thing" style="max-width: 100%; height: auto; border-radius: 10px;" />
      </div>

      <!-- Reset Action -->
      <p style="font-size: 16px; color: #000;">Click the button below to reset your password. Be sure to use a strong and unique password that you haven't used elsewhere:</p>
      <div style="text-align: center; margin: 25px 0;">
        <a href="{resetLink}" 
           style="background: linear-gradient(to right, #4B0082, #8A2BE2); color: white; padding: 12px 25px; border-radius: 50px; text-decoration: none; font-size: 16px; font-weight: bold; border: none;">
          Reset Password
        </a>
      </div>

      <!-- Reminder -->
      <p style="font-size: 14px; color: #444; text-align: center;">
        If you didn’t request a password reset, just ignore this email and go do something fun. It's a nice day. ☀️
      </p>

      <hr style="margin: 30px 0; border-color: #ccc;" />

      <!-- Username Reminder -->
      <p style="font-size: 14px; color: #8A2BE2; text-align: center;">
        <strong>Forgot Username?</strong><br/>
        Your username is: <strong>{username}</strong>
      </p>

      <!-- Footer -->
      <div style="font-size: 12px; color: #888; text-align: center; margin-top: 30px;">
        <p style="margin: 0;">Home ・ Upgrade ・ Support ・ Privacy ・ TOS ・ Jobs ・ Blog ・ Unsubscribe</p>
      </div>

    </div>
  </body>
</html>

    """
    send_mail(email, "Password Reset", body)
    return {"message": "Reset password link sent to your email"}


async def resetPassword(data: ResetPasswordReq):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=421, detail="Invalid token")

        hashed_password = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await user_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
        return {"message": "Password reset successful"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

# ---------------- USER REPORT FUNCTIONS ---------------- #

async def generateUserReport():
    return await generate_user_report()

async def getLatestUserReport():
    return await get_latest_user_report()

async def getUserReportById(report_id: str):
    return await get_user_report_by_id(report_id)

async def getAllUserReports():
    return await get_all_user_reports()

async def deleteUserReport(report_id: str):
    return await delete_user_report(report_id)

async def deletealluserreports():
    return await delete_all_user_reports()
