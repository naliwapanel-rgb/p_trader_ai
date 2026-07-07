from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
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