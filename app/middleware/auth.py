"""
Authentication and authorization middleware.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.oauth2_token_url,
    scopes=settings.oauth2_scopes_dict,
    auto_error=False
)


class AuthenticationError(HTTPException):
    """Custom authentication error."""

    def __init__(self, detail: str = "E005: Invalid or missing authorization"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise AuthenticationError("E005: Invalid token")


def verify_scopes(token_payload: dict, required_scopes: list[str]) -> bool:
    """
    Verify that token has required scopes.

    Args:
        token_payload: Decoded token payload
        required_scopes: List of required scopes

    Returns:
        True if all scopes are present
    """
    token_scopes = token_payload.get("scopes", [])
    if isinstance(token_scopes, str):
        token_scopes = token_scopes.split()

    return all(scope in token_scopes for scope in required_scopes)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> dict:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        User information from token

    Raises:
        AuthenticationError: If authentication fails
    """
    if not settings.oauth2_enabled:
        # Auth disabled, return mock user
        return {"sub": "system", "scopes": ["sfb.read", "sfb.write"]}

    if credentials is None:
        raise AuthenticationError("E005: Authorization header missing")

    token = credentials.credentials
    payload = verify_token(token)

    # Verify required scopes
    if not verify_scopes(payload, ["sfb.read"]):
        raise AuthenticationError("E005: Insufficient permissions")

    return payload


async def get_current_user_with_write_permission(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> dict:
    """
    Dependency to get current user with write permission.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        User information from token

    Raises:
        AuthenticationError: If authentication fails or lacks write permission
    """
    if not settings.oauth2_enabled:
        return {"sub": "system", "scopes": ["sfb.read", "sfb.write"]}

    if credentials is None:
        raise AuthenticationError("E005: Authorization header missing")

    token = credentials.credentials
    payload = verify_token(token)

    # Verify write scope
    if not verify_scopes(payload, ["sfb.write"]):
        raise AuthenticationError("E005: Write permission required")

    return payload
