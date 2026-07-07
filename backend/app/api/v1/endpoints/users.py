from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.responses import success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    user_data = UserResponse.model_validate(current_user).model_dump()

    return success_response(
        message="User profile retrieved successfully",
        data=user_data,
    )