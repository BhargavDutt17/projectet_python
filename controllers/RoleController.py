from config.database import role_collection
from models.RoleModel import Role, RoleOut
from bson import ObjectId
from fastapi import HTTPException

async def getAllRoles():
    try:
        roles = await role_collection.find().to_list(None)

        def convert_objectid_to_str(data):
            """Recursively converts ObjectId fields to strings."""
            if isinstance(data, ObjectId):
                return str(data)
            elif isinstance(data, dict):
                return {k: convert_objectid_to_str(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_objectid_to_str(i) for i in data]
            return data

        roles = convert_objectid_to_str(roles)
        return [RoleOut.from_mongo(role) for role in roles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def addRole(role: Role):
    existing_role = await role_collection.find_one({"name": role.name})
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    result = await role_collection.insert_one(role.dict())
    return {"message": "Role created successfully"}

async def deleteRole(roleId: str):
    result = await role_collection.delete_one({"_id": ObjectId(roleId)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}

async def getRoleById(roleId: str):
    role = await role_collection.find_one({"_id": ObjectId(roleId)})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleOut.from_mongo(role)