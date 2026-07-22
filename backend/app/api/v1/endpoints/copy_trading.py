from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import (
    Session,
)
from app.api.dependencies import (
    get_current_user,
)
from app.database.session import (
    get_db,
)
from app.models.user import (
    User,
)
from app.schemas.copy_trading_subscription import (
    CopyTradingSubscriptionActionResult,
    CopyTradingSubscriptionCreateRequest,
    CopyTradingSubscriptionResponse,
    CopyTradingSubscriptionStatus,
)
from app.services.copy_trading_subscription_service import (
    CopyTradingSubscriptionService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/copy-trading/subscriptions",
    tags=["Copy Trading"],
)
def _serialize_subscription(
    subscription,
) -> dict:
    return (
        CopyTradingSubscriptionResponse
        .model_validate(subscription)
        .model_dump(mode="json")
    )
def _action_result(
    *,
    action: str,
    previous_status: str,
    subscription,
) -> dict:
    return (
        CopyTradingSubscriptionActionResult(
            action=action,
            previous_status=previous_status,
            status=subscription.status,
            changed=(
                previous_status
                != subscription.status
            ),
            subscription=(
                CopyTradingSubscriptionResponse
                .model_validate(
                    subscription
                )
            ),
        )
        .model_dump(mode="json")
    )
@router.get("")
async def list_my_copy_subscriptions(
    subscription_status: (
        CopyTradingSubscriptionStatus
        | None
    ) = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    subscriptions = (
        CopyTradingSubscriptionService(
            db
        )
        .list_subscriptions(
            current_user=current_user,
            subscription_status=(
                subscription_status
            ),
            limit=limit,
            offset=offset,
        )
    )
    return success_response(
        message=(
            "Copy-trading subscriptions "
            "retrieved successfully"
        ),
        data=[
            _serialize_subscription(
                subscription
            )
            for subscription
            in subscriptions
        ],
    )
@router.post("")
async def create_my_copy_subscription(
    data: (
        CopyTradingSubscriptionCreateRequest
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    subscription = (
        CopyTradingSubscriptionService(
            db
        )
        .create_subscription(
            current_user=current_user,
            data=data,
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "created successfully"
        ),
        data=_serialize_subscription(
            subscription
        ),
    )
@router.get("/{subscription_id}")
async def get_my_copy_subscription(
    subscription_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    subscription = (
        CopyTradingSubscriptionService(
            db
        )
        .get_subscription(
            current_user=current_user,
            subscription_id=(
                subscription_id
            ),
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "retrieved successfully"
        ),
        data=_serialize_subscription(
            subscription
        ),
    )
@router.delete("/{subscription_id}")
async def delete_my_copy_subscription(
    subscription_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    (
        CopyTradingSubscriptionService(
            db
        )
        .delete_subscription(
            current_user=current_user,
            subscription_id=(
                subscription_id
            ),
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "deleted successfully"
        ),
        data=None,
    )
@router.post("/{subscription_id}/pause")
async def pause_my_copy_subscription(
    subscription_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = (
        CopyTradingSubscriptionService(
            db
        )
    )
    existing = service.get_subscription(
        current_user=current_user,
        subscription_id=subscription_id,
    )
    previous_status = existing.status
    subscription = (
        service.pause_subscription(
            current_user=current_user,
            subscription_id=(
                subscription_id
            ),
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "paused successfully"
        ),
        data=_action_result(
            action="PAUSE",
            previous_status=previous_status,
            subscription=subscription,
        ),
    )
@router.post("/{subscription_id}/resume")
async def resume_my_copy_subscription(
    subscription_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = (
        CopyTradingSubscriptionService(
            db
        )
    )
    existing = service.get_subscription(
        current_user=current_user,
        subscription_id=subscription_id,
    )
    previous_status = existing.status
    subscription = (
        service.resume_subscription(
            current_user=current_user,
            subscription_id=(
                subscription_id
            ),
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "resumed successfully"
        ),
        data=_action_result(
            action="RESUME",
            previous_status=previous_status,
            subscription=subscription,
        ),
    )
@router.post("/{subscription_id}/stop")
async def stop_my_copy_subscription(
    subscription_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = (
        CopyTradingSubscriptionService(
            db
        )
    )
    existing = service.get_subscription(
        current_user=current_user,
        subscription_id=subscription_id,
    )
    previous_status = existing.status
    subscription = (
        service.stop_subscription(
            current_user=current_user,
            subscription_id=(
                subscription_id
            ),
        )
    )
    return success_response(
        message=(
            "Copy-trading subscription "
            "stopped successfully"
        ),
        data=_action_result(
            action="STOP",
            previous_status=previous_status,
            subscription=subscription,
        ),
    )
