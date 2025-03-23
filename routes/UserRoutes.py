from fastapi import APIRouter, Form, UploadFile, File
from controllers.UserController import addUser, getAllUsers, loginUser, uploadUserProfileImage , getUserProfile
from models.UserModel import UserLogin

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
    return await addUser(firstName, lastName, username, email, password, inviteCode, status, profile_image)

@router.get("/users/")
async def get_users():
    return await getAllUsers()

@router.post("/users/login/")
async def login_user(user: UserLogin):
    return await loginUser(user)

@router.post("/users/upload-profile/")
async def upload_profile_image(
    user_id: str = Form(...), 
    image: UploadFile = File(...)
):
    return await uploadUserProfileImage(user_id, image)

@router.get("/user/profile/{user_id}")
async def get_user_profile(user_id: str):
    return await getUserProfile(user_id)