from fastapi import FastAPI
from app.api import offers

app = FastAPI(title="JobStack API")

app.include_router(offers.router)