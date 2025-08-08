# app/services.py
import json
import os
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    genai = None

from app.models import (
    ResponseModel, CorrectionRequest, CorrectionResponse, CorrectionType,
    GuidanceRequest, GuidanceResponse, PatternDetected, SpecificGuidance,
    ValidationRequest, ValidationResponse, ValidationResult,
    FrequentCorrection, PatternValidationExample,
    BatchCorrectionRequest, BatchCorrectionResponse, BatchCorrectionItem
)
from app.config import (
    settings, FIELD_TYPES, FIELD_GUIDANCE,
    CORRECTION_PROMPT_TEMPLATE, GUIDANCE_PROMPT_TEMPLATE, VALIDATION_PROMPT_TEMPLATE
)


class MyService:
    """Legacy service for backward compatibility"""
    def __init__(self):
        self.correction_service = CorrectionService()
    
    def get_data(self) -> ResponseModel:
        return ResponseModel(message="Hello from MyService")
    
    def get_correction_service(self) -> 'CorrectionService':
        return self.correction_service


class CorrectionService:
    """Main service for handling correction inference and guidance"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if genai and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.model = None

    def _detect_field_type(self, field_name: str) -> str:
        """Detect field type based on field name"""
        field_lower = field_name.lower()
        for field_type, patterns in FIELD_TYPES.items():
            if any(pattern in field_lower for pattern in patterns):
                return field_type
        return 'other'

    def _build_correction_prompt(self, field_name: str, current_value: str, specific_guidance: Optional[Dict] = None) -> str:
        """Build correction prompt using template"""
        field_type = self._detect_field_type(field_name)
        guidance = FIELD_GUIDANCE.get(field_type, FIELD_GUIDANCE['other'])
        
        # Merge with specific guidance if provided
        if specific_guidance:
            guidance = {**guidance, **specific_guidance}
        
        return CORRECTION_PROMPT_TEMPLATE.format(
            field_name=field_name,
            field_type=field_type,
            current_value=current_value,
            description=guidance.get('description', ''),
            patterns=guidance.get('patterns', ''),
            common_errors=guidance.get('common_errors', ''),
            examples=guidance.get('examples', '')
        )

    def _build_guidance_prompt(self, company_id: str, frequent_corrections: List[FrequentCorrection]) -> str:
        """Build guidance prompt using template"""
        corrections_data = ""
        for i, correction in enumerate(frequent_corrections, 1):
            corrections_data += f"""{i}. Field: {correction.field_name}
   Pattern: "{correction.original_value}" → "{correction.corrected_value}"
   Frequency: {correction.frequency} occurrences
   
"""
        
        return GUIDANCE_PROMPT_TEMPLATE.format(
            company_id=company_id,
            corrections_data=corrections_data
        )

    def _build_validation_prompt(self, examples: List[PatternValidationExample]) -> str:
        """Build validation prompt using template"""
        validation_examples = ""
        for i, example in enumerate(examples, 1):
            validation_examples += f"""{i}. Field: {example.field_name}
   Original: "{example.original_value}"
   Corrected: "{example.corrected_value}"
   Should integrate as pattern: {example.should_integrate}
   
"""
        
        return VALIDATION_PROMPT_TEMPLATE.format(
            validation_examples=validation_examples
        )

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with error handling"""
        if not self.model:
            raise ValueError("LLM not configured. Please set GEMINI_API_KEY environment variable.")
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"LLM API error: {str(e)}")

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with simple repair"""
        # Extract JSON from response
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].strip()
        else:
            json_text = response_text.strip()
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Simple repair attempt
            try:
                # Remove trailing commas and fix common issues
                repaired = json_text.replace(',}', '}').replace(',]', ']')
                return json.loads(repaired)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON response: {str(e)}")

    def perform_correction_inference(self, request: CorrectionRequest) -> CorrectionResponse:
        """Perform pure LLM inference for field correction"""
        
        # Build prompt
        prompt = self._build_correction_prompt(
            field_name=request.field_name,
            current_value=request.current_value,
            specific_guidance=request.specific_guidance
        )
        
        # Call LLM
        response_text = self._call_llm(prompt)
        result = self._parse_json_response(response_text)
        
        # Map string correction type to enum
        correction_type_str = result.get('correction_type', 'no_correction')
        try:
            correction_type = CorrectionType(correction_type_str)
        except ValueError:
            correction_type = CorrectionType.NO_CORRECTION
        
        return CorrectionResponse(
            field_name=request.field_name,
            original_value=request.current_value,
            correction_needed=result.get('correction_needed', False),
            corrected_value=result.get('corrected_value'),
            correction_type=correction_type,
            confidence=result.get('confidence', 0.0),
            reasoning=result.get('reasoning', 'LLM analysis completed')
        )

    def perform_batch_corrections(self, request: BatchCorrectionRequest) -> BatchCorrectionResponse:
        """Perform batch corrections with automatic parallel/sequential processing"""
        
        start_time = time.time()
        total_items = len(request.items)
        
        # Use parallel processing for larger batches
        if total_items > 5:
            return self._perform_batch_corrections_parallel(request, start_time)
        else:
            return self._perform_batch_corrections_sequential(request, start_time)

    def _perform_batch_corrections_sequential(self, request: BatchCorrectionRequest, start_time: float) -> BatchCorrectionResponse:
        """Perform batch corrections sequentially"""
        
        results = []
        corrections_made = 0
        
        for item in request.items:
            correction_request = CorrectionRequest(
                field_name=item.field_name,
                current_value=item.current_value,
                specific_guidance=item.specific_guidance
            )
            
            try:
                correction_response = self.perform_correction_inference(correction_request)
                results.append(correction_response)
                
                if correction_response.correction_needed:
                    corrections_made += 1
                    
            except Exception as e:
                # Handle individual item failures gracefully
                error_response = CorrectionResponse(
                    field_name=item.field_name,
                    original_value=item.current_value,
                    correction_needed=False,
                    corrected_value=None,
                    correction_type=CorrectionType.NO_CORRECTION,
                    confidence=0.0,
                    reasoning=f"Error during processing: {str(e)}"
                )
                results.append(error_response)
        
        processing_time = time.time() - start_time
        
        return BatchCorrectionResponse(
            total_items=len(request.items),
            corrections_made=corrections_made,
            processing_time=round(processing_time, 2),
            results=results
        )

    def _perform_batch_corrections_parallel(self, request: BatchCorrectionRequest, start_time: float) -> BatchCorrectionResponse:
        """Perform batch corrections in parallel"""
        
        def process_single_item(item) -> BatchCorrectionItem:
            correction_request = CorrectionRequest(
                field_name=item.field_name,
                current_value=item.current_value,
                specific_guidance=item.specific_guidance
            )
            
            try:
                correction_response = self.perform_correction_inference(correction_request)
                
                return correction_response
                
            except Exception as e:
                return CorrectionResponse(
                    field_name=item.field_name,
                    original_value=item.current_value,
                    correction_needed=False,
                    corrected_value=None,
                    correction_type=CorrectionType.NO_CORRECTION,
                    confidence=0.0,
                    reasoning=f"Error during processing: {str(e)}"
                )
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=min(8, len(request.items))) as executor:
            results = list(executor.map(process_single_item, request.items))
        
        corrections_made = sum(1 for result in results if result.correction_needed)
        processing_time = time.time() - start_time
        
        return BatchCorrectionResponse(
            total_items=len(request.items),
            corrections_made=corrections_made,
            processing_time=round(processing_time, 2),
            results=results
        )

    def build_company_guidance(self, request: GuidanceRequest) -> GuidanceResponse:
        """Build company-specific guidance from frequent corrections"""
        
        # Build prompt
        prompt = self._build_guidance_prompt(
            company_id=request.company_id,
            frequent_corrections=request.frequent_corrections
        )
        
        # Call LLM
        response_text = self._call_llm(prompt)
        result = self._parse_json_response(response_text)
        
        # Parse patterns
        patterns_detected = []
        for pattern_data in result.get('patterns_detected', []):
            pattern = PatternDetected(
                field_name=pattern_data.get('field_name', ''),
                pattern_type=pattern_data.get('pattern_type', ''),
                description=pattern_data.get('description', ''),
                examples=pattern_data.get('examples', []),
                frequency=pattern_data.get('frequency', 0),
                confidence=pattern_data.get('confidence', 0.0)
            )
            patterns_detected.append(pattern)
        
        # Parse specific guidance
        proposed_guidance = {}
        guidance_data = result.get('proposed_specific_guidance', {})
        for field_name, guidance_info in guidance_data.items():
            specific_guidance = SpecificGuidance(
                description=guidance_info.get('description', ''),
                patterns=guidance_info.get('patterns', ''),
                common_errors=guidance_info.get('common_errors', ''),
                examples=guidance_info.get('examples', '')
            )
            proposed_guidance[field_name] = specific_guidance
        
        return GuidanceResponse(
            company_id=request.company_id,
            patterns_detected=patterns_detected,
            proposed_specific_guidance=proposed_guidance,
            confidence=result.get('confidence', 0.0),
            summary=result.get('summary', 'Company guidance analysis completed')
        )

    def validate_pattern_detection(self, request: ValidationRequest) -> ValidationResponse:
        """Validate pattern detection effectiveness"""
        
        # Build prompt
        prompt = self._build_validation_prompt(request.examples)
        
        # Call LLM
        response_text = self._call_llm(prompt)
        result = self._parse_json_response(response_text)
        
        # Parse validation results
        validation_results = []
        for prediction in result.get('predictions', []):
            validation_result = ValidationResult(
                field_name=prediction.get('field_name', ''),
                should_integrate=prediction.get('should_integrate', False),
                confidence=prediction.get('confidence', 0.0),
                reasoning=prediction.get('reasoning', '')
            )
            validation_results.append(validation_result)
        
        # Calculate accuracy
        correct_predictions = 0
        total_predictions = len(request.examples)
        
        for i, example in enumerate(request.examples):
            if i < len(validation_results):
                predicted = validation_results[i].should_integrate
                actual = example.should_integrate
                if predicted == actual:
                    correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
        return ValidationResponse(
            accuracy=accuracy,
            correct_predictions=correct_predictions,
            total_predictions=total_predictions,
            predictions=validation_results,
            summary=result.get('summary', f"{accuracy*100:.1f}% accuracy achieved")
        )
