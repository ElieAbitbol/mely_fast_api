from fastapi import APIRouter, HTTPException, status

from app.models import (
    ResponseModel, CorrectionRequest, CorrectionResponse,
    GuidanceRequest, GuidanceResponse, ValidationRequest, ValidationResponse,
    BatchCorrectionRequest, BatchCorrectionResponse
)
from app.services import MyService

router = APIRouter()
service = MyService()


@router.get("/")
def root():
    return {"message": "Welcome to the Data Correction API 👋"}


@router.get("/ping")
def pong():
    return {"message": "pong"}


@router.get("/data", response_model=ResponseModel)
def read_data():
    return service.get_data()


@router.post("/correct", response_model=CorrectionResponse)
def perform_correction(request: CorrectionRequest):
    """
    Perform field correction inference using LLM.
    
    This endpoint analyzes a field value and determines if correction is needed,
    providing the corrected value along with confidence and reasoning.
    """
    try:
        correction_service = service.get_correction_service()
        return correction_service.perform_correction_inference(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/guidance", response_model=GuidanceResponse)
def build_company_guidance(request: GuidanceRequest):
    """
    Build company-specific guidance from frequent corrections.
    
    Analyzes patterns in correction data to generate customized guidance
    that can improve future data extraction accuracy.
    """
    try:
        correction_service = service.get_correction_service()
        return correction_service.build_company_guidance(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/validate", response_model=ValidationResponse)
def validate_pattern_detection(request: ValidationRequest):
    """
    Validate LLM's pattern detection accuracy for guidance integration.
    
    Tests the LLM's ability to distinguish between systematic patterns
    that should be integrated into guidance vs. specific corrections to ignore.
    """
    try:
        correction_service = service.get_correction_service()
        return correction_service.validate_pattern_detection(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/correct/batch", response_model=BatchCorrectionResponse)
def perform_batch_corrections(request: BatchCorrectionRequest):
    """
    Perform batch field corrections on multiple fields.
    
    Processes multiple field_name/current_value pairs efficiently,
    with automatic parallel processing for large datasets (>5 items).
    """
    try:
        correction_service = service.get_correction_service()
        
        # Use parallel processing for larger batches
        if len(request.items) > 5:
            return correction_service.perform_batch_corrections_parallel(request)
        else:
            return correction_service.perform_batch_corrections(request)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
