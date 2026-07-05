from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
async def register_user(
    data: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    return AuthService(db).register_user(data)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    data: UserLoginRequest,
    db: Session = Depends(get_db),
):
    return AuthService(db).login_user(data)