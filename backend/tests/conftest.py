"""
Test setup: a throwaway SQLite DB, no HuggingFace calls, and Supabase-style
ES256 tokens signed by a test key that stands in for the project's JWKS.
Env vars are set before `app` is imported so backend/.env never applies.
"""
import os
import tempfile
import time

_tmpdir = tempfile.mkdtemp(prefix="neetiai-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["SUPABASE_URL"] = "https://test-ref.supabase.co"
os.environ["SUPABASE_JWT_SECRET"] = "test-legacy-hs256-secret"
os.environ["HF_TOKEN"] = ""            # never call the rephrase API from tests
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app import auth
from app.database import engine
from app.main import app
from app.rate_limit import limiter

ISSUER = "https://test-ref.supabase.co/auth/v1"
SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
KID = "test-kid"


class _FakeJWKSClient:
    """Mimics PyJWKClient: returns the test public key for the known kid only."""
    def get_signing_key_from_jwt(self, token):
        if jwt.get_unverified_header(token).get("kid") != KID:
            raise jwt.PyJWKClientError("unknown kid")
        return type("Key", (), {"key": SIGNING_KEY.public_key()})()


auth.jwks_client = _FakeJWKSClient()


def make_token(sub, email=None, *, exp_in=3600, aud="authenticated", iss=ISSUER,
               key=SIGNING_KEY, alg="ES256", kid=KID, email_verified=True):
    claims = {
        "sub": sub,
        "email": email or f"{sub}@example.com",
        "aud": aud,
        "iss": iss,
        "role": "authenticated",
        "exp": int(time.time()) + exp_in,
        "user_metadata": {"email_verified": email_verified},
    }
    return jwt.encode(claims, key, algorithm=alg, headers={"kid": kid})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    limiter.reset()
    with TestClient(app) as c:
        yield c


def sync(client, sub, email=None, **token_kwargs):
    """Logs a user in the way the frontend does; returns (backend user id, auth headers)."""
    token = make_token(sub, email, **token_kwargs)
    res = client.post("/users/sync", headers=auth_header(token), json={
        "supabase_uid": sub, "email": email or f"{sub}@example.com", "first_name": sub.title(), "last_name": "",
    })
    assert res.status_code == 200, res.text
    return res.json()["id"], auth_header(token)
