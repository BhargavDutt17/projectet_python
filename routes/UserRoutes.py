from fastapi import APIRouter, Form, UploadFile, File,Request,HTTPException
from controllers import UserController
from models.UserModel import UserLogin, ResetPasswordReq
from pydantic import BaseModel
from config.database import user_collection

router = APIRouter()

@router.post("/users/")
async def post_user(
    firstName: str = Form(...),
    lastName: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    inviteCode: str = Form(""),
    status: str = Form("active"),
    profile_image: UploadFile = File(None)  # Optional profile image
):
    return await UserController.addUser(firstName, lastName, username, email, password, inviteCode, status, profile_image)

@router.get("/users/")
async def get_users():
    return await UserController.getAllUsers()

@router.post("/users/login/")
async def login_user(user: UserLogin):
    return await UserController.loginUser(user)

@router.post("/users/upload-profile/")
async def upload_profile_image(
    user_id: str = Form(...), 
    image: UploadFile = File(...)
):
    return await UserController.uploadUserProfileImage(user_id, image)

@router.get("/user/profile/{user_id}")
async def get_user_profile(user_id: str):
    return await UserController.getUserProfile(user_id)


# Define request models for JSON input
class UpdateUsernameModel(BaseModel):
    new_username: str

class UpdateEmailModel(BaseModel):
    new_email: str

class UpdatePasswordModel(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


# Route to update username (Now Accepts JSON)
@router.put("/update-username/{user_id}")
async def update_user_username(user_id: str, data: UpdateUsernameModel):
    return await UserController.update_username(user_id, data.new_username)

# Route to update email (Now Accepts JSON)
@router.put("/update-email/{user_id}")
async def update_user_email(user_id: str, data: UpdateEmailModel):
    return await UserController.update_email(user_id, data.new_email)

# Route to change password (Now Accepts JSON)
@router.put("/change-password/{user_id}")
async def update_user_password(user_id: str, data: UpdatePasswordModel):
    return await UserController.change_password(user_id, data.current_password, data.new_password, data.confirm_password)

# Route to update profile picture
@router.put("/update-profile-picture/{user_id}")
async def update_profile_picture(user_id: str, image: UploadFile): 
    return await UserController.update_profile_picture(user_id, image)

# Route to deactivate a user (1-minute delay)
@router.put("/deactivate-user/{user_id}")
async def deactivate_user(user_id: str, password: str = Form(...), role: str = Form(...)):
    return await UserController.deactivate_user(user_id, password, role)

# Route to delete a user (1-minute delay)
@router.delete("/delete-user/{user_id}")
async def delete_user(user_id: str, password: str = Form(...), role: str = Form(...)):
    return await UserController.delete_user(user_id, password, role)

@router.put("/user/deactivate/{user_id}")
async def deactivate_user(user_id: str, request: Request = None):
    body = await request.json()
    role = body.get("role")
    password = body.get("password")  # Optional for admin

    return await UserController.trigger_user_deactivation(user_id, role, password)

@router.delete("/user/delete/{user_id}")
async def delete_user(user_id: str, request: Request = None):
    body = await request.json()
    role = body.get("role")
    password = body.get("password")  # Optional if admin

    return await UserController.trigger_user_deletion(user_id, role, password)

# Activate User Route
class ActivateRequest(UserLogin):
    role: str = None  # Optional role for admin-based activation

@router.post("/users/activate")
async def reactivate_account(request: ActivateRequest):
    return await UserController.activateUser(request)

@router.put("/user/cancel-delete/{user_id}")
async def cancel_user_deletion(user_id: str):
    return await UserController.cancel_user_deletion(user_id)

@router.delete("/users/delete-profile-image/{user_id}")
async def delete_profile_image(user_id: str):
    return await UserController.delete_profile_picture(user_id)

# USER REPORT ROUTES
@router.post("/user-reports/generate")
async def generate_report_with_filters(request: Request):
    return await UserController.generate_user_report(request)

@router.get("/user-reports/latest")
async def get_latest_user_excel():
    return await UserController.getLatestUserReport()

@router.get("/user-reports/{report_id}")
async def get_user_excel_by_id(report_id: str):
    return await UserController.getUserReportById(report_id)

@router.get("/user-reports/")
async def get_all_user_excel_reports():
    return await UserController.getAllUserReports()

@router.delete("/user-reports/{report_id}")
async def delete_user_excel_report(report_id: str):
    return await UserController.deleteUserReport(report_id)


def convert_objectid_to_str(user):
    user["_id"] = str(user["_id"])
    if "role" in user and "_id" in user["role"]:
        user["role"]["_id"] = str(user["role"]["_id"])
    return user

@router.get("/getUserByQuery")
async def get_user_by_query(search: str):
    try:
        query = {
            "$or": [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"firstName": {"$regex": search, "$options": "i"}},
                {"lastName": {"$regex": search, "$options": "i"}},
            ]
        }
        users = await user_collection.find(query).to_list(length=10)
        return [convert_objectid_to_str(u) for u in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user-reports/")
async def delete_all_user_excel_reports():
    return await UserController.deletealluserreports()

# @router.post("/users/forgotpassword/")
# async def forgot_password(email: str = Form(...)):
#     print("EMAIL RECEIVED:", email)
#     return await UserController.forgotPassword(email)

@router.post("/users/resetpassword/")
async def reset_password(data: ResetPasswordReq):
    return await UserController.resetPassword(data)

@router.post("/forgotpassword")
async def forgot_password(email: str):  # comes from ?email=
    print("EMAIL RECEIVED:", email)
    return await UserController.forgotPassword(email)

