from config.database import role_collection
from models.RoleModel import Role, RoleOut
from bson import ObjectId
from fastapi import HTTPException

async def getAllRoles():
    """Fetches all roles from the database."""
    roles = await role_collection.find().to_list(None)
    return [RoleOut.from_mongo(role) for role in roles]

async def addRole(role: Role):
    """Adds a new role to the database, ensuring unique names."""
    existing_role = await role_collection.find_one({"name": role.name})
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    result = await role_collection.insert_one(role.dict())
    return {"message": "Role created successfully"}

async def deleteRole(roleId: str):
    """Deletes a role by its ID."""
    result = await role_collection.delete_one({"_id": ObjectId(roleId)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}

async def getRoleById(roleId: str):
    """Fetches a single role by ID."""
    role = await role_collection.find_one({"_id": ObjectId(roleId)})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleOut.from_mongo(role)
