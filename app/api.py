# app/main.py
from fastapi import FastAPI

from app import routers  # routers.py file
from app.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Single router that includes both ping and data
app.include_router(routers.router)
