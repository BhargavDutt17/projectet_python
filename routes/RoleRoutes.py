from fastapi import APIRouter
from controllers.RoleController import getAllRoles, addRole, deleteRole, getRoleById
from models.RoleModel import Role

router = APIRouter()

@router.get("/roles/")
async def get_roles():
    """API endpoint to fetch all roles."""
    return await getAllRoles()

@router.post("/role/")
async def post_role(role: Role):
    """API endpoint to create a new role."""
    return await addRole(role)

@router.delete("/role/{roleId}")
async def delete_role(roleId: str):
    """API endpoint to delete a role by ID."""
    return await deleteRole(roleId)

@router.get("/role/{roleId}")
async def get_role_byId(roleId: str):
    """API endpoint to fetch a role by ID."""
    return await getRoleById(roleId)
