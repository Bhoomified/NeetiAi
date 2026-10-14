"""Token verification: only valid, unexpired Supabase tokens for this project get in."""
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from conftest import auth_header, make_token, sync


def test_missing_token_rejected(client):
    assert client.get("/transactions/1").status_code == 401


def test_valid_token_accepted(client):
    uid, headers = sync(client, "alice")
    assert client.get(f"/transactions/{uid}", headers=headers).status_code == 200


@pytest.mark.parametrize("token_kwargs, reason", [
    ({"exp_in": -60}, "expired"),
    ({"key": ec.generate_private_key(ec.SECP256R1())}, "forged: signed by a different key"),
    ({"kid": "attacker-kid"}, "unknown signing key id"),
    ({"aud": "anon"}, "wrong audience"),
    ({"iss": "https://other-project.supabase.co/auth/v1"}, "token from another project"),
])
def test_bad_tokens_rejected(client, token_kwargs, reason):
    uid, _ = sync(client, "alice")
    bad = make_token("alice", **token_kwargs)
    assert client.get(f"/transactions/{uid}", headers=auth_header(bad)).status_code == 401, reason


def test_alg_none_rejected(client):
    uid, _ = sync(client, "alice")
    unsigned = jwt.encode({"sub": "alice", "aud": "authenticated"}, None, algorithm="none")
    assert client.get(f"/transactions/{uid}", headers=auth_header(unsigned)).status_code == 401


def test_garbage_token_rejected(client):
    assert client.get("/transactions/1", headers=auth_header("not-a-jwt")).status_code == 401


def test_legacy_hs256_secret_supported(client):
    uid, _ = sync(client, "alice")
    good = make_token("alice", key="test-legacy-hs256-secret", alg="HS256")
    forged = make_token("alice", key="guessed-secret", alg="HS256")
    assert client.get(f"/transactions/{uid}", headers=auth_header(good)).status_code == 200
    assert client.get(f"/transactions/{uid}", headers=auth_header(forged)).status_code == 401


def test_valid_token_for_unsynced_user_forbidden(client):
    token = make_token("never-synced")
    assert client.get("/transactions/1", headers=auth_header(token)).status_code == 403
