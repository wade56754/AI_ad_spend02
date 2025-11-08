from functools import wraps
from typing import Callable, Iterable

from fastapi import Depends, HTTPException, status

from backend.core.error_codes import ErrorCode
from backend.core.security import AuthenticatedUser, get_current_user


def require_roles(*roles: str) -> Callable:
    allowed_roles: Iterable[str] = roles

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, current_user: AuthenticatedUser = Depends(get_current_user), **kwargs):
            if allowed_roles and current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": ErrorCode.PERMISSION_DENIED, "message": "权限不足"},
                )
            return func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator

