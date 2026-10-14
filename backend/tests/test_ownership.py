"""User A cannot read or write user B's data through any route."""
import pytest
from sqlmodel import Session

from app.database import engine
from app.models import IncomeSource

from conftest import sync


@pytest.fixture
def two_users(client):
    a_id, a = sync(client, "alice")
    b_id, b = sync(client, "bob")
    tx = client.post("/transactions", headers=a, json={"user_id": a_id, "merchant_raw": "SWIGGY*ORD883726", "amount": 250})
    assert tx.status_code == 200, tx.text
    src = client.post("/income-sources", headers=a, json={"user_id": a_id, "label": "Tutoring", "amount": 3000, "frequency": "monthly"})
    assert src.status_code == 200, src.text
    return {"a_id": a_id, "a": a, "b_id": b_id, "b": b, "tx_id": tx.json()["id"], "src_id": src.json()["id"]}


def test_owner_can_read_own_data(client, two_users):
    u = two_users
    assert client.get(f"/transactions/{u['a_id']}", headers=u["a"]).json()[0]["id"] == u["tx_id"]
    assert client.get(f"/transactions/{u['tx_id']}/explain", headers=u["a"]).status_code == 200
    assert client.get(f"/income-sources/{u['a_id']}", headers=u["a"]).status_code == 200
    assert client.get(f"/users/{u['a_id']}", headers=u["a"]).status_code == 200
    # exercises DistilBERT end to end (regression: OpenMP deadlock hung every /chat)
    chat = client.post("/chat", headers=u["a"], json={"user_id": u["a_id"], "message": "how much did I spend on food?"})
    assert chat.status_code == 200 and chat.json()["response"]


@pytest.mark.parametrize("path", [
    "/users/{a_id}",
    "/transactions/{a_id}",
    "/forecast/{a_id}",
    "/income-sources/{a_id}",
    "/recommendations/{a_id}",
    "/investments/opportunities/{a_id}",
])
def test_cannot_read_other_users_data(client, two_users, path):
    u = two_users
    res = client.get(path.format(a_id=u["a_id"]), headers=u["b"])
    assert res.status_code == 403, res.text


@pytest.mark.parametrize("path, body", [
    ("/transactions", {"merchant_raw": "ZOMATO", "amount": 100}),
    ("/income-sources", {"label": "Fake", "amount": 1, "frequency": "weekly"}),
    ("/budget/optimize", {"savings_target_pct": 0.1}),
    ("/chat", {"message": "how much did I spend on food?"}),
    ("/investments/watchlist", {"symbol": "119551"}),
])
def test_cannot_write_as_other_user(client, two_users, path, body):
    u = two_users
    res = client.post(path, headers=u["b"], json={"user_id": u["a_id"], **body})
    assert res.status_code == 403, res.text


def test_cannot_explain_other_users_transaction(client, two_users):
    u = two_users
    assert client.get(f"/transactions/{u['tx_id']}/explain", headers=u["b"]).status_code == 404


def test_cannot_delete_other_users_income_source(client, two_users):
    u = two_users
    assert client.delete(f"/income-sources/{u['src_id']}", headers=u["b"]).status_code == 404
    with Session(engine) as s:
        assert s.get(IncomeSource, u["src_id"]) is not None
    assert client.delete(f"/income-sources/{u['src_id']}", headers=u["a"]).status_code == 200


def test_legacy_unauthenticated_user_create_removed(client):
    assert client.post("/users", json={"name": "x", "email": "x@example.com"}).status_code in (404, 405)
