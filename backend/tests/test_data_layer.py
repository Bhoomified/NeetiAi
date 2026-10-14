"""Phase 2: paginated transactions, UTC timestamps, forecaster history window."""
from datetime import timedelta

from sqlmodel import Session

from app.database import engine
from app.models import Transaction, utcnow
from app.routers import FORECAST_WINDOW_WEEKS, load_forecast_rows

from conftest import sync


def _add(user_id, merchant, amount, days_ago):
    with Session(engine) as s:
        s.add(Transaction(user_id=user_id, merchant_raw=merchant, amount=amount, category="food",
                          date=utcnow() - timedelta(days=days_ago)))
        s.commit()


def test_transactions_paginated_newest_first(client):
    uid, h = sync(client, "asha")
    for i in range(25):
        _add(uid, f"M{i}", 10 + i, days_ago=i)     # M0 is the newest
    first = client.get(f"/transactions/{uid}?limit=10", headers=h).json()
    assert first["total"] == 25 and first["limit"] == 10 and first["offset"] == 0
    assert [t["merchant_raw"] for t in first["items"]] == [f"M{i}" for i in range(10)]
    last = client.get(f"/transactions/{uid}?limit=10&offset=20", headers=h).json()
    assert [t["merchant_raw"] for t in last["items"]] == [f"M{i}" for i in range(20, 25)]


def test_pagination_bounds_validated(client):
    uid, h = sync(client, "asha")
    for q in ("limit=0", "limit=101", "offset=-1"):
        assert client.get(f"/transactions/{uid}?{q}", headers=h).status_code == 422, q


def test_timestamps_serialized_as_utc(client):
    uid, h = sync(client, "asha")
    client.post("/transactions", headers=h, json={"user_id": uid, "merchant_raw": "SWIGGY", "amount": 120})
    date = client.get(f"/transactions/{uid}", headers=h).json()["items"][0]["date"]
    assert date.endswith("Z") or date.endswith("+00:00"), date


def test_forecaster_only_loads_recent_window(client):
    uid, h = sync(client, "asha")
    _add(uid, "OLD", 999, days_ago=FORECAST_WINDOW_WEEKS * 7 + 30)
    _add(uid, "NEW", 50, days_ago=2)
    with Session(engine) as s:
        rows = load_forecast_rows(uid, s)
    assert [r.amount for r in rows] == [50]
    assert set(rows[0]._fields) == {"date", "amount", "category"}
    assert client.get(f"/forecast/{uid}", headers=h).status_code == 200


def test_chat_timeframes_work_with_aware_and_naive_dates(client):
    uid, h = sync(client, "asha")
    _add(uid, "SWIGGY", 200, days_ago=0)
    res = client.post("/chat", headers=h, json={"user_id": uid, "message": "how much did I spend on food this week?"})
    assert res.status_code == 200, res.text
