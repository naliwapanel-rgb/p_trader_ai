from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.password_update import PasswordUpdateRequest
from app.schemas.user import UserResponse
from app.schemas.user_update import UserUpdateRequest
from app.services.user_service import UserService
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


@router.put("/me")
async def update_my_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated_user = UserService(db).update_profile(
        current_user=current_user,
        data=data,
    )

    user_data = UserResponse.model_validate(updated_user).model_dump()

    return success_response(
        message="User profile updated successfully",
        data=user_data,
    )


@router.put("/me/password")
async def update_my_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserService(db).update_password(
        current_user=current_user,
        data=data,
    )

    return success_response(
        message="Password updated successfully",
    )
@router.delete("/me")
async def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    UserService(db).deactivate_account(current_user)

    return success_response(
        message="Account deactivated successfully",
    )