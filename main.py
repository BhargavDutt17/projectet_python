from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.RoleRoutes import router as role_router
from routes.UserRoutes import router as user_router
from routes.CategoryRoutes import router as category_router
from routes.SubCategoryRoutes import router as sub_category_router

app = FastAPI()

# Enable CORS for React frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for testing, change to ["http://localhost:5173"] for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allows all headers
)

# Register API routes
app.include_router(user_router)
app.include_router(role_router)
app.include_router(category_router)
app.include_router(sub_category_router)

