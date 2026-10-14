"""
Liveness and readiness probes.

/health        — the process is up (always 200 if the API answers at all).
/health/ready  — the database answers and every trained model loaded;
                 503 with a list of reasons otherwise.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine, db_state, ensure_db, mark_db_down, migration_status
from app import ml_categorizer, ml_forecast, ml_chatbot, ml_investments, ml_recommend, ml_rephrase

router = APIRouter(tags=["health"])


def model_status() -> dict:
    """True when the trained artifact is loaded (False = running on a rule-based fallback)."""
    return {
        "categorizer": ml_categorizer._model is not None,
        "forecaster": ml_forecast._total_model is not None,
        "intent_classifier": ml_chatbot._model is not None and ml_chatbot._label_encoder is not None,
        "risk_classifier": ml_investments._risk_model is not None,
        "peer_profiles": ml_recommend._peers_df is not None,
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready():
    reasons = []

    database_ok = ensure_db()
    if database_ok:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except OperationalError as e:
            mark_db_down(e)
            database_ok = False
    if not database_ok:
        reasons.append(f"database: {db_state.error}")
    else:
        pending = migration_status()
        if pending:
            reasons.append(f"migrations: {pending}")

    models = model_status()
    reasons += [f"model not loaded: {name}" for name, loaded in models.items() if not loaded]

    body = {
        "status": "ready" if not reasons else "degraded",
        "database": database_ok,
        "models": models,
        # Optional: chat falls back to the factual template without it
        "rephrase_layer": ml_rephrase._client is not None,
        "reasons": reasons,
    }
    return JSONResponse(body, status_code=200 if not reasons else 503)
