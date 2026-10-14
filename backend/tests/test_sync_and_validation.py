"""/users/sync idempotency and linking, input validation, rate limiting."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlmodel import Session, select

from app.database import engine
from app.models import User

from conftest import auth_header, make_token, sync


def _sync_body(sub, email):
    return {"supabase_uid": sub, "email": email, "first_name": "Asha", "last_name": "R"}


def test_concurrent_sync_creates_one_user(client):
    headers = auth_header(make_token("asha", "asha@example.com"))
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: client.post("/users/sync", headers=headers, json=_sync_body("asha", "asha@example.com")), range(8)))
    assert {r.status_code for r in results} == {200}
    assert len({r.json()["id"] for r in results}) == 1
    with Session(engine) as s:
        assert len(s.exec(select(User)).all()) == 1


def test_sync_rejects_body_uid_that_differs_from_token(client):
    headers = auth_header(make_token("asha"))
    res = client.post("/users/sync", headers=headers, json=_sync_body("someone-else", "asha@example.com"))
    assert res.status_code == 403


def test_sync_uses_token_email_not_body_email(client):
    headers = auth_header(make_token("asha", "asha@example.com"))
    res = client.post("/users/sync", headers=headers, json=_sync_body("asha", "victim@example.com"))
    assert res.json()["email"] == "asha@example.com"


def test_verified_email_links_second_login_method(client):
    first_id, _ = sync(client, "email-uid", "asha@example.com")
    second_id, _ = sync(client, "google-uid", "Asha@Example.com", email_verified=True)
    assert first_id == second_id
    with Session(engine) as s:
        assert [u.supabase_uid for u in s.exec(select(User)).all()] == ["google-uid"]


def test_unverified_email_cannot_take_over_account(client):
    sync(client, "email-uid", "asha@example.com")
    headers = auth_header(make_token("attacker-uid", "asha@example.com", email_verified=False))
    res = client.post("/users/sync", headers=headers, json=_sync_body("attacker-uid", "asha@example.com"))
    assert res.status_code == 409


@pytest.mark.parametrize("path, body", [
    ("/transactions", {"merchant_raw": "SWIGGY", "amount": 0}),
    ("/transactions", {"merchant_raw": "SWIGGY", "amount": -50}),
    ("/transactions", {"merchant_raw": "SWIGGY", "amount": 1e12}),
    ("/transactions", {"merchant_raw": "", "amount": 50}),
    ("/transactions", {"merchant_raw": "x" * 201, "amount": 50}),
    ("/income-sources", {"label": "Job", "amount": 100, "frequency": "daily"}),
    ("/income-sources", {"label": "Job", "amount": -1, "frequency": "weekly"}),
    ("/budget/optimize", {"savings_target_pct": 1.0}),
    ("/budget/optimize", {"savings_target_pct": -0.1}),
    ("/chat", {"message": "x" * 1001}),
    ("/investments/watchlist", {"symbol": "../../etc"}),
])
def test_invalid_input_rejected(client, path, body):
    uid, headers = sync(client, "asha")
    res = client.post(path, headers=headers, json={"user_id": uid, **body})
    assert res.status_code == 422, res.text


def test_risk_quiz_scores_bounded(client):
    _, headers = sync(client, "asha")
    quiz = {"age_score": 9, "income_stability": 3, "investment_horizon": 3, "loss_reaction": 3, "existing_savings_months": 3}
    assert client.post("/investments/risk-profile", headers=headers, json=quiz).status_code == 422


def test_search_rate_limited_per_user(client):
    _, asha = sync(client, "asha")
    _, ravi = sync(client, "ravi")
    # one-letter queries return [] without calling mfapi.in
    codes = [client.get("/investments/search?q=a", headers=asha).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429
    assert client.get("/investments/search?q=a", headers=ravi).status_code == 200
