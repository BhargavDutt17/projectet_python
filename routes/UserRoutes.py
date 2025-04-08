from fastapi import APIRouter, Form, UploadFile, File,Request
from controllers import UserController
from models.UserModel import UserLogin
from pydantic import BaseModel


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