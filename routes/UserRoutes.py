from fastapi import APIRouter
from controllers.UserController import addUser, loginUser, getAllUsers
from models.UserModel import User,UserOut,UserLogin

router = APIRouter()

@router.post("/users/")
async def post_user(user: User):
    print("Received user data:", user.dict())  # ✅ Debugging
    return await addUser(user)

@router.get("/users/")
async def get_users():
    """API endpoint to fetch all users."""
    return await getAllUsers()

@router.post("/users/login/")
async def login_user(user: UserLogin):  # Accepts UserLogin model
    """API endpoint for user login."""
    return await loginUser(user)  # Sends UserLogin object
