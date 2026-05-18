from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import create_db_and_tables # Dodano app.
from app.config import settings               # Dodano app.
from app.api import offers

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Register the routes from api/offers.py
app.include_router(offers.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME}