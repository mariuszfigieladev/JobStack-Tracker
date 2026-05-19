from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import offers

app = FastAPI(title="JobStack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(offers.router)