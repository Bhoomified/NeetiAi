import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from app.database import create_db_and_tables, db_state, mark_db_down, migration_status
from app.routers import router
from app.health import router as health_router
from app.rate_limit import limiter
from slowapi.errors import RateLimitExceeded

# Comma-separated list of exact frontend origins, e.g. "http://localhost:3000,https://neetiai.vercel.app"
CORS_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
if "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must list exact origins; '*' is not allowed together with credentials.")

app = FastAPI(title="NeetiAi API")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)
app.include_router(health_router)


@app.on_event("startup")
def on_startup():
    if not create_db_and_tables():
        print(f"⚠️  Database unreachable — {db_state.error} | API up in degraded mode, see GET /health/ready")
    elif pending := migration_status():
        print(f"⚠️  Schema out of date — {pending}")


@app.exception_handler(RateLimitExceeded)
def rate_limited_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"detail": f"Too many requests ({exc.detail}) — try again in a minute."}, status_code=429)


@app.exception_handler(OperationalError)
def db_down_handler(request: Request, exc: OperationalError):
    # DB dropped mid-request (after startup succeeded): flip to degraded and answer 503, not 500
    mark_db_down(exc)
    return JSONResponse({"detail": f"Database unavailable — {db_state.error}"}, status_code=503)


@app.get("/")
def root():
    return {"status": "NeetiAi backend running"}
