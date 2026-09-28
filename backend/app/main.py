from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import offers
from app.database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wykonuje się podczas startu kontenera
    create_db_and_tables()
    yield
    # Tutaj opcjonalny kod wykonywany przy wyłączaniu aplikacji

app = FastAPI(title="JobStack API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(offers.router)