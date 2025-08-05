# app/services.py
from app.models import ResponseModel
from app.correction_service import CorrectionService


class MyService:
    def __init__(self):
        self.correction_service = CorrectionService()
    
    def get_data(self) -> ResponseModel:
        return ResponseModel(message="Hello from MyService")
    
    def get_correction_service(self) -> CorrectionService:
        return self.correction_service
