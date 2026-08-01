import inspect

from app.api.dependencies import get_current_user
from app.api.v1.endpoints.auth import (
    login_user,
    register_user,
)
from app.api.v1.endpoints.users import (
    deactivate_my_account,
    get_my_profile,
    update_my_password,
    update_my_profile,
)


def test_blocking_identity_execution_is_synchronous() -> None:
    callables = (
        get_current_user,
        register_user,
        login_user,
        get_my_profile,
        update_my_profile,
        update_my_password,
        deactivate_my_account,
    )

    asynchronous_callables = [
        callable_object.__name__
        for callable_object in callables
        if inspect.iscoroutinefunction(callable_object)
    ]

    assert asynchronous_callables == []
