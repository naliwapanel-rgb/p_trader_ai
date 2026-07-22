from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)
from sqlalchemy.orm import (
    Session,
)
from app.core.security.token import (
    verify_access_token,
)
from app.database.session import (
    get_db,
)
from app.models.user import (
    User,
)
from app.repositories.user_repository import (
    UserRepository,
)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)
def _authentication_error(
    detail: str,
) -> HTTPException:
    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    subject = verify_access_token(
        token
    )
    if subject is None:
        raise _authentication_error(
            "Invalid or expired token"
        )
    try:
        user_id = int(subject)
    except (
        TypeError,
        ValueError,
    ) as error:
        raise _authentication_error(
            "Invalid token subject"
        ) from error
    if user_id <= 0:
        raise _authentication_error(
            "Invalid token subject"
        )
    user = UserRepository(
        db
    ).get_by_id(
        user_id
    )
    if user is None:
        raise _authentication_error(
            "User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Inactive user",
        )
    return user
