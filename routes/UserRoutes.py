from fastapi import APIRouter
from controllers.UserController import addUser,getAllUsers,loginUser
from models.UserModel import User,UserOut,UserLogin

router = APIRouter()

@router.post("/users/")
async def post_user(user:User):
    return await addUser(user)

@router.get("/users/")
async def get_users():
    return await getAllUsers()

@router.post("/users/login/")
async def login_user(user:UserLogin):
    return await loginUser(user)