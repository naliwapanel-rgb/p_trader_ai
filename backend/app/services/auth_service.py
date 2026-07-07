from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.password import hash_password, verify_password
from app.core.security.token import create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register_user(self, data: UserRegisterRequest) -> TokenResponse:
        existing_user = self.user_repository.get_by_email(data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed_password = hash_password(data.password)

        user = self.user_repository.create(
            full_name=data.full_name,
            email=data.email,
            hashed_password=hashed_password,
        )

        token = create_access_token(subject=str(user.id))

        return TokenResponse(access_token=token)

    def login_user(self, data: UserLoginRequest) -> TokenResponse:
        user = self.user_repository.get_by_email(data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token(subject=str(user.id))

        return TokenResponse(access_token=token)