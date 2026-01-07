"""
JWT Authentication utilities for Supabase Auth integration.
Validates JWT tokens from Supabase and extracts user information.
"""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


class TokenData(BaseModel):
    """Extracted data from a validated JWT token."""
    user_id: str
    email: Optional[str] = None


# Security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=False)


def get_supabase_jwt_secret() -> str:
    """
    Get the Supabase JWT secret from environment variables.
    This secret is used to validate tokens issued by Supabase Auth.
    """
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET environment variable is not set")
    return secret


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a Supabase JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        TokenData with user_id and email extracted from the token

    Raises:
        HTTPException: If token is invalid, expired, or missing required claims
    """
    try:
        secret = get_supabase_jwt_secret()

        # Decode and verify the token
        # Supabase uses HS256 algorithm by default
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated"
        )

        # Extract user ID from the 'sub' claim (standard JWT subject claim)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token missing user ID (sub claim)"
            )

        # Extract email if available
        email = payload.get("email")

        return TokenData(user_id=user_id, email=email)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token audience"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except ValueError as e:
        # This catches the missing JWT secret error
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    FastAPI dependency to get the current authenticated user.

    Use this as a dependency in protected routes:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}

    Args:
        credentials: Bearer token credentials from the Authorization header

    Returns:
        TokenData with the authenticated user's information

    Raises:
        HTTPException: If no token provided or token is invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid Bearer token."
        )

    return verify_token(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[TokenData]:
    """
    FastAPI dependency to optionally get the current user.
    Returns None if no valid token is provided (for public endpoints
    that have enhanced functionality for authenticated users).

    Args:
        credentials: Bearer token credentials from the Authorization header

    Returns:
        TokenData if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None
