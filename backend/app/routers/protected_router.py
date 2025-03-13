from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, get_current_admin
from app.entity.models import User

router = APIRouter(prefix="/protected", tags=["Protected"])


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin_only")
async def admin_panel(admin_user: User = Depends(get_current_admin)):
    return {"msg": f"Hello, admin {admin_user.email}"}
