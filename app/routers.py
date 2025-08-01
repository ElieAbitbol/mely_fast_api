from fastapi import APIRouter

from app.models import ResponseModel
from app.services import MyService

router = APIRouter()
service = MyService()


@router.get("/")
def root():
    return {"message": "Welcome to the API 👋"}


@router.get("/ping")
def pong():
    return {"message": "pong"}


@router.get("/data", response_model=ResponseModel)
def read_data():
    return service.get_data()
