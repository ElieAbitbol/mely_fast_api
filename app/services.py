# app/service.py
from app.models import ResponseModel


class MyService:
    def get_data(self) -> ResponseModel:
        return ResponseModel(message="Hello from MyService")
