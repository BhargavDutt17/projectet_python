from motor.motor_asyncio import AsyncIOMotorClient

# Database URL
MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "projectet"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]
role_collection = db["roles"]
user_collection = db["users"]
category_collection = db["categories"]
sub_category_collection = db["sub_categories"]
transaction_collection = db["transaction"]

