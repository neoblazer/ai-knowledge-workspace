import logging
from dataclasses import dataclass
from typing import Annotated

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request, status

from config import get_settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    session_id: str | None = None


def get_current_user(request: Request) -> CurrentUser:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ") or not authorization.removeprefix("Bearer ").strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    if not settings.clerk_secret_key:
        logger.error("CLERK_SECRET_KEY is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured",
        )

    try:
        request_state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.clerk_secret_key,
                jwt_key=settings.clerk_jwt_key or None,
                authorized_parties=list(settings.clerk_authorized_parties),
                accepts_token=["session_token"],
            ),
        )
    except Exception as exc:
        logger.warning("Clerk token verification failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    payload = request_state.payload or {}
    user_id = payload.get("sub")
    if not request_state.is_signed_in or not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user_id=user_id, session_id=payload.get("sid"))


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
