# app/models.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class ResponseModel(BaseModel):
    message: str


class CorrectionRequest(BaseModel):
    field_name: str = Field(..., description="Name of the field to analyze")
    current_value: str = Field(..., description="Current value that might need correction")
    specific_guidance: Optional[Dict[str, Any]] = Field(None, description="Company-specific guidance for this field type")


class CorrectionType(str, Enum):
    EMAIL_CONTAMINATION = "email_contamination"
    PHONE_CONTAMINATION = "phone_contamination"
    WEBSITE_CONTAMINATION = "website_contamination"
    PREFIX_REMOVAL = "prefix_removal"
    FORMAT_STANDARDIZATION = "format_standardization"
    CURRENCY_STANDARDIZATION = "currency_standardization"
    QUANTITY_FORMATTING = "quantity_formatting"
    NO_CORRECTION = "no_correction"


class CorrectionResponse(BaseModel):
    field_name: str
    original_value: str
    correction_needed: bool
    corrected_value: Optional[str] = None
    correction_type: Optional[CorrectionType] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class FrequentCorrection(BaseModel):
    field_name: str
    original_value: str
    corrected_value: str
    frequency: int


class GuidanceRequest(BaseModel):
    company_id: str
    frequent_corrections: List[FrequentCorrection]


class PatternDetected(BaseModel):
    field_name: str
    pattern_type: str
    description: str
    examples: List[str]
    frequency: int
    confidence: float = Field(..., ge=0.0, le=1.0)


class SpecificGuidance(BaseModel):
    description: str
    patterns: str
    common_errors: str
    examples: str


class GuidanceResponse(BaseModel):
    company_id: str
    patterns_detected: List[PatternDetected]
    proposed_specific_guidance: Dict[str, SpecificGuidance]
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str


class PatternValidationExample(BaseModel):
    field_name: str
    original_value: str
    corrected_value: str
    should_integrate: bool
    reason: str


class ValidationRequest(BaseModel):
    examples: List[PatternValidationExample]


class ValidationResult(BaseModel):
    field_name: str
    should_integrate: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class ValidationResponse(BaseModel):
    accuracy: float = Field(..., ge=0.0, le=1.0)
    correct_predictions: int
    total_predictions: int
    predictions: List[ValidationResult]
    summary: str


class BatchCorrectionItem(BaseModel):
    field_name: str = Field(..., description="Name of the field to analyze")
    current_value: str = Field(..., description="Current value that might need correction")
    specific_guidance: Optional[Dict[str, Any]] = Field(None, description="Company-specific guidance for this field type")


class BatchCorrectionRequest(BaseModel):
    items: List[BatchCorrectionItem] = Field(..., description="List of fields to correct")
    company_id: Optional[str] = Field(None, description="Company ID for contextual processing")


class BatchCorrectionResponse(BaseModel):
    total_items: int
    corrections_made: int
    results: List[CorrectionResponse]
    processing_time: float
    company_id: Optional[str] = None
