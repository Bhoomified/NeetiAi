from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from app.database import create_db_and_tables, db_state, mark_db_down
from app.routers import router
from app.health import router as health_router

app = FastAPI(title="NeetiAi API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(health_router)


@app.on_event("startup")
def on_startup():
    if not create_db_and_tables():
        print(f"⚠️  Database unreachable — {db_state.error} | API up in degraded mode, see GET /health/ready")


@app.exception_handler(OperationalError)
def db_down_handler(request: Request, exc: OperationalError):
    # DB dropped mid-request (after startup succeeded): flip to degraded and answer 503, not 500
    mark_db_down(exc)
    return JSONResponse({"detail": f"Database unavailable — {db_state.error}"}, status_code=503)


@app.get("/")
def root():
    return {"status": "NeetiAi backend running"}
