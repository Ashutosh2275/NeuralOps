"""
Authentication and Role-Based Access Control (RBAC) for SentinelOps AI.
Provides deterministic, application-level security independent of LLM decisions.
"""
from __future__ import annotations

from enum import Enum
import hashlib
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"

    @classmethod
    def hierarchy(cls) -> dict["Role", int]:
        return {
            cls.VIEWER: 1,
            cls.OPERATOR: 2,
            cls.ADMIN: 3,
        }

    def has_privilege(self, required_role: "Role") -> bool:
        hierarchy = self.hierarchy()
        return hierarchy.get(self, 0) >= hierarchy.get(required_role, 0)


class User(BaseModel):
    user_id: str
    username: str
    role: Role = Role.VIEWER
    is_active: bool = True


# Pre-configured or registered API keys: {hashed_key: User}
_STATIC_API_KEYS: dict[str, User] = {}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


def register_api_key(raw_key: str, user: User) -> None:
    """Register an API key for authentication."""
    key_hash = _hash_key(raw_key)
    _STATIC_API_KEYS[key_hash] = user


# Register standard default dev keys
register_api_key("sentinelops-admin-secret-key", User(user_id="usr-admin", username="admin", role=Role.ADMIN))
register_api_key("sentinelops-operator-secret-key", User(user_id="usr-op", username="operator", role=Role.OPERATOR))
register_api_key("sentinelops-viewer-secret-key", User(user_id="usr-view", username="viewer", role=Role.VIEWER))


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> User:
    """
    Authenticate request via X-API-Key or Authorization Bearer header.
    In development mode, if no key is provided, falls back to local dev user with warning.
    """
    token = api_key or (bearer_creds.credentials if bearer_creds else None)

    if token:
        token_hash = _hash_key(token)
        user = _STATIC_API_KEYS.get(token_hash)
        if user and user.is_active:
            return user
        log.warning("auth_failed_invalid_token", token_hash=token_hash[:8])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    if settings.app_env in ("development", "test"):
        # Development fallback with explicitly flagged identity
        return User(user_id="dev-default", username="dev_operator", role=Role.OPERATOR)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing required authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(min_role: Role) -> Callable[[User], User]:
    """FastAPI dependency to enforce minimum role authorization."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role.has_privilege(min_role):
            log.warning(
                "auth_forbidden_insufficient_role",
                user_id=current_user.user_id,
                user_role=current_user.role.value,
                required_role=min_role.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: '{min_role.value}', current role: '{current_user.role.value}'",
            )
        return current_user

    return role_checker


require_viewer = require_role(Role.VIEWER)
require_operator = require_role(Role.OPERATOR)
require_admin = require_role(Role.ADMIN)
