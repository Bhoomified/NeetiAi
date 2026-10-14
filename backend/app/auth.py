"""
Supabase JWT verification and per-user ownership checks.

Every data route depends on `current_user`, which verifies the browser's
Supabase access token and resolves the matching backend User. The user_id the
browser sends is never trusted on its own — `ensure_owner` compares it to the
token's user.

Signing: this project's tokens are ES256, verified against the public JWKS at
{SUPABASE_URL}/auth/v1/.well-known/jwks.json (Dashboard > Settings > JWT Keys).
Legacy HS256 tokens are accepted only if SUPABASE_JWT_SECRET is set.
"""
import os

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.database import get_session
from app.models import User

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
JWT_AUDIENCE = "authenticated"
ASYMMETRIC_ALGS = {"ES256", "RS256"}

# Caches the public keys; refetches when a token carries an unknown kid (key rotation)
jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", lifespan=600) if SUPABASE_URL else None

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def verify_token(token: str) -> dict:
    """Checks signature, exp, audience and issuer; returns the token's claims."""
    try:
        alg = jwt.get_unverified_header(token).get("alg")
    except jwt.PyJWTError:
        raise _unauthorized("Malformed token.")

    if alg in ASYMMETRIC_ALGS:
        if jwks_client is None:
            raise HTTPException(status_code=503, detail="Auth not configured: SUPABASE_URL is not set.")
        try:
            key = jwks_client.get_signing_key_from_jwt(token).key
        except jwt.PyJWKClientConnectionError:
            raise HTTPException(status_code=503, detail="Could not reach Supabase to verify your session.")
        except jwt.PyJWTError:
            raise _unauthorized("Token signed with an unknown key.")
    elif alg == "HS256" and SUPABASE_JWT_SECRET:
        key = SUPABASE_JWT_SECRET
    else:
        raise _unauthorized("Unsupported token signing algorithm.")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience=JWT_AUDIENCE,
            issuer=f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None,
            options={"require": ["exp", "sub", "aud"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired — please log in again.")
    except jwt.PyJWTError:
        raise _unauthorized("Invalid token.")


def token_claims(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        raise _unauthorized("Missing bearer token.")
    claims = verify_token(creds.credentials)
    request.state.rate_key = f"user:{claims['sub']}"  # rate limits count per verified user
    return claims


def current_user(claims: dict = Depends(token_claims), session: Session = Depends(get_session)) -> User:
    user = session.exec(select(User).where(User.supabase_uid == claims["sub"])).first()
    if not user:
        raise HTTPException(status_code=403, detail="Account not synced yet — call /users/sync first.")
    return user


def ensure_owner(user_id: int, user: User):
    """403 when the user_id in a path or body isn't the logged-in user's."""
    if user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only access your own data.")
