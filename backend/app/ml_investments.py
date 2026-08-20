"""
Investment module: risk profiling (trained Decision Tree) + mutual fund
NAV tracking via mfapi.in (free, no API key) + opportunity detection
(rolling z-score — flags when a watched fund's NAV drops meaningfully
below its recent average, a classic "buy the dip" signal, purely
informational — NOT financial advice, see disclaimer in the API response).
"""
import os
import joblib
import httpx
import numpy as np

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "risk_classifier.pkl")

_risk_model = None
if os.path.exists(ARTIFACT_PATH):
    _risk_model = joblib.load(ARTIFACT_PATH)
    print(f"✅ Loaded risk profiling classifier from {ARTIFACT_PATH}")
else:
    print(f"⚠️  No risk classifier found at {ARTIFACT_PATH} — using rule-based fallback")


def classify_risk_profile(age_score, income_stability, investment_horizon, loss_reaction, existing_savings_months):
    features = [[age_score, income_stability, investment_horizon, loss_reaction, existing_savings_months]]
    if _risk_model is not None:
        return _risk_model.predict(features)[0]
    # fallback: simple average-based rule, same spirit as the training label logic
    avg = np.mean(features[0])
    return "conservative" if avg < 2.3 else ("moderate" if avg < 3.6 else "aggressive")


async def fetch_fund_nav_history(scheme_code: str):
    """mfapi.in is free, no key required. Returns list of {date, nav} dicts, most recent first."""
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return data.get("data", []), data.get("meta", {})


def detect_opportunity(nav_history: list, window: int = 20, z_threshold: float = -1.5):
    if len(nav_history) < window + 1:
        return None

    navs = [float(pt["nav"]) for pt in nav_history[:window + 1]]
    latest = navs[0]
    recent_window = navs[1:window + 1]

    mean = np.mean(recent_window)
    std = np.std(recent_window)
    if std == 0:
        return None

    z_score = (latest - mean) / std

    return {
        "latest_nav": float(latest),
        "recent_mean": round(float(mean), 2),
        "z_score": round(float(z_score), 2),
        "is_opportunity": bool(z_score <= z_threshold),   # explicit bool() cast — the actual fix
        "note": "Statistical signal only — not investment advice. Consult a registered advisor before investing.",
    }

async def search_funds(query: str):
    url = f"https://api.mfapi.in/mf/search?q={query}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return resp.json()