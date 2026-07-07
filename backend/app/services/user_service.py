from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.password import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.password_update import PasswordUpdateRequest
from app.schemas.user_update import UserUpdateRequest


class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def update_profile(
        self,
        current_user: User,
        data: UserUpdateRequest,
    ) -> User:
        if data.email is not None and data.email != current_user.email:
            existing_user = self.user_repository.get_by_email(data.email)

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use",
                )

        return self.user_repository.update(
            user=current_user,
            full_name=data.full_name,
            email=data.email,
        )

    def update_password(
        self,
        current_user: User,
        data: PasswordUpdateRequest,
    ) -> User:
        if not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        new_hashed_password = hash_password(data.new_password)

        return self.user_repository.update_password(
            user=current_user,
            hashed_password=new_hashed_password,
        )