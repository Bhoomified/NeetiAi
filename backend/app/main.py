from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import router

app = FastAPI(title="NeetiAi API")

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"status": "NeetiAi backend running"}