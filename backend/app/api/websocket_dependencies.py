from fastapi import Depends, WebSocket, WebSocketException
from sqlalchemy.orm import Session
from app.core.security.token import verify_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
WS_UNAUTHORIZED = 4401
WS_FORBIDDEN = 4403
def get_websocket_token(
    websocket: WebSocket,
) -> str:
    authorization = websocket.headers.get(
        "authorization",
        "",
    ).strip()
    if authorization:
        scheme, separator, credentials = (
            authorization.partition(" ")
        )
        if (
            separator
            and scheme.lower() == "bearer"
            and credentials.strip()
        ):
            return credentials.strip()
    query_token = websocket.query_params.get(
        "token"
    )
    if query_token and query_token.strip():
        return query_token.strip()
    raise WebSocketException(
        code=WS_UNAUTHORIZED,
        reason="Not authenticated",
    )
def get_current_websocket_user(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> User:
    token = get_websocket_token(websocket)
    subject = verify_access_token(token)
    if subject is None:
        raise WebSocketException(
            code=WS_UNAUTHORIZED,
            reason="Invalid or expired token",
        )
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise WebSocketException(
            code=WS_UNAUTHORIZED,
            reason="Invalid token subject",
        ) from exc
    user = UserRepository(db).get_by_id(
        user_id
    )
    if user is None:
        raise WebSocketException(
            code=WS_UNAUTHORIZED,
            reason="User not found",
        )
    if not user.is_active:
        raise WebSocketException(
            code=WS_FORBIDDEN,
            reason="Inactive user",
        )
    return user
