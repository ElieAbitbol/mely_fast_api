# app/models.py
from pydantic import BaseModel


class ResponseModel(BaseModel):
    message: str
