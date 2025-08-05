# app/correction_service.py
import json
import os
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables
except ImportError:
    genai = None

from app.models import (
    CorrectionRequest, CorrectionResponse, CorrectionType,
    GuidanceRequest, GuidanceResponse, PatternDetected, SpecificGuidance,
    ValidationRequest, ValidationResponse, ValidationResult,
    FrequentCorrection, PatternValidationExample,
    BatchCorrectionRequest, BatchCorrectionResponse, BatchCorrectionItem
)


class DynamicPromptBuilder:
    """Builds dynamic prompts for field correction inference"""
    
    FIELD_TYPES = {
        'vessel': ['vessel_name', 'ship_name'],
        'cargo_control': ['cargo_control_number', 'ccn'],
        'po_number': ['po_number', 'purchase_order'],
        'quantity': ['quantity', 'qty'],
        'currency': ['currency', 'curr'],
        'country': ['country', 'country_code'],
        'address': ['address', 'shipper_address', 'consignee_address'],
        'package_code': ['package_code', 'pkg_code'],
        'weight': ['weight', 'cargo_weight'],
        'company_name': ['company_name', 'shipper', 'consignee', 'vendor']
    }

    def detect_field_type(self, field_name: str) -> str:
        """Detect field type based on field name"""
        field_lower = field_name.lower()
        for field_type, patterns in self.FIELD_TYPES.items():
            if any(pattern in field_lower for pattern in patterns):
                return field_type
        return 'other'

    def build_simple_prompt(self, field_name: str, current_value: str, specific_guidance: Optional[Dict] = None) -> str:
        """Build a simple prompt for LLM inference"""
        field_type = self.detect_field_type(field_name)
        
        # Base guidance
        base_guidance = {
            'vessel': {
                'description': 'Ship/vessel names for maritime transport',
                'patterns': 'M.V., M.T., M.S., proper vessel names',
                'common_errors': 'Container codes instead of names, emails, companies, too short values',
                'examples': 'M.V. ISABELLE G, Serenity Ibtihaj, Champion Pomer'
            },
            'cargo_control': {
                'description': 'Cargo Control Numbers (CCN)',
                'patterns': 'Alphanumeric format, usually 10-14 characters',
                'common_errors': 'Unwanted spaces, letter O instead of 0, dashes',
                'examples': '22NN124299, 5125PARS552243, 2205788152245'
            },
            'po_number': {
                'description': 'Purchase Order numbers',
                'patterns': 'Alphanumeric, may contain legitimate dashes/spaces',
                'common_errors': 'Multiple spaces, commas, words "ORDER" or "NUMBER"',
                'examples': 'K137-25, W065616000, 478103'
            },
            'quantity': {
                'description': 'Merchandise quantities',
                'patterns': 'Numbers with units (CARTONS, PALLETS, KG, MT, etc.)',
                'common_errors': 'Abnormally large quantities, broken decimal format',
                'examples': '381 Cartons, 19.552 MMT, 2950 Cartons'
            },
            'currency': {
                'description': 'Currency codes',
                'patterns': 'ISO 3-letter codes (USD, EUR, CAD, etc.)',
                'common_errors': 'Full names instead of codes, symbols',
                'examples': 'USD, CAD, EUR, GBP, THB'
            },
            'country': {
                'description': 'Country codes',
                'patterns': 'ISO 2-letter codes preferred',
                'common_errors': 'Full country names instead of codes',
                'examples': 'US, CA, CN, TH, BE'
            },
            'company_name': {
                'description': 'Company names (shipper, consignee, vendor)',
                'patterns': 'Proper company names',
                'common_errors': 'Mixed emails/URLs, contact information',
                'examples': 'Clean company names without contact info'
            }
        }.get(field_type, {
            'description': 'General field validation',
            'patterns': 'Appropriate format for field type',
            'common_errors': 'Format inconsistencies, contamination',
            'examples': 'Clean, properly formatted values'
        })

        # Merge with specific guidance if provided
        if specific_guidance:
            guidance = {**base_guidance, **specific_guidance}
        else:
            guidance = base_guidance

        prompt = f"""You are an expert data quality validator for shipping/logistics data extraction.

FIELD ANALYSIS:
- Field Name: {field_name}
- Field Type: {field_type}
- Current Value: "{current_value}"

FIELD GUIDANCE:
Description: {guidance.get('description', '')}
Expected Patterns: {guidance.get('patterns', '')}
Common Errors: {guidance.get('common_errors', '')}
Examples: {guidance.get('examples', '')}

TASK:
Analyze if the current value needs correction based on the field guidance.

RESPONSE FORMAT:
Return ONLY a JSON object with this exact structure:
{{
  "correction_needed": boolean,
  "corrected_value": "corrected value or null if no correction needed",
  "correction_type": "email_contamination|phone_contamination|website_contamination|prefix_removal|format_standardization|currency_standardization|quantity_formatting|no_correction",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of the decision"
}}

IMPORTANT:
- Be conservative: only suggest corrections when clearly justified
- Preserve legitimate formatting when possible
- Focus on removing contamination (emails, phones, websites) and standardizing formats
- If no correction is needed, set correction_needed to false and corrected_value to null"""

        return prompt


class CorrectionService:
    """Main service for handling correction inference and guidance"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if genai and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
        else:
            self.model = None
        
        self.prompt_builder = DynamicPromptBuilder()

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
        """Parse JSON response from LLM"""
        # Clean response
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].strip()
        else:
            json_text = response_text
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}")

    def perform_correction_inference(self, request: CorrectionRequest) -> CorrectionResponse:
        """Perform pure LLM inference for field correction"""
        
        # Build prompt
        prompt = self.prompt_builder.build_simple_prompt(
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
            reasoning=result.get('reasoning', '')
        )

    def build_company_guidance(self, request: GuidanceRequest) -> GuidanceResponse:
        """Build company-specific guidance from frequent corrections"""
        
        # Build analysis prompt
        corrections_text = ""
        for i, correction in enumerate(request.frequent_corrections[:20], 1):
            corrections_text += f"""
{i}. Field: {correction.field_name}
   Original: "{correction.original_value}"
   Corrected: "{correction.corrected_value}"
   Frequency: {correction.frequency} times
"""
        
        prompt = f"""You are an expert in data analysis and pattern detection.

OBJECTIVE: 
Analyze frequent corrections for company "{request.company_id}" to detect ERROR PATTERNS 
and propose specific guidance to improve future extractions.

IMPORTANT:
- Only consider corrections that reveal systematic PATTERNS
- Ignore isolated or specific corrections (e.g., proper names, unique values)
- Focus on recurring errors that can be predicted and avoided

FREQUENT CORRECTIONS TO ANALYZE:
{corrections_text}

INSTRUCTIONS:
1. Identify recurring ERROR PATTERNS (not isolated corrections)
2. Group patterns by field type
3. For each identified pattern, propose specific guidance
4. Guidance should help prevent these company-specific errors

RESPONSE FORMAT:
Return ONLY a valid JSON object:
{{
  "company_id": "{request.company_id}",
  "analysis_summary": "summary of detected patterns analysis",
  "patterns_detected": [
    {{
      "field_type": "field type",
      "pattern_description": "error pattern description",
      "frequency": "observed frequency",
      "examples": ["example1", "example2"]
    }}
  ],
  "proposed_specific_guidance": {{
    "field_type": {{
      "description": "company-specific description",
      "company_patterns": "specific patterns observed",
      "company_errors": "specific recurring errors",
      "company_examples": "company-specific examples",
      "prevention_tips": "tips to avoid these errors"
    }}
  }},
  "confidence": 0.0-1.0,
  "recommendations": "recommendations for implementing these guidances"
}}"""
        
        response_text = self._call_llm(prompt)
        result = self._parse_json_response(response_text)
        
        # Convert to response model
        patterns_detected = [
            PatternDetected(**pattern) for pattern in result.get('patterns_detected', [])
        ]
        
        specific_guidance = {}
        for field_type, guidance_data in result.get('proposed_specific_guidance', {}).items():
            specific_guidance[field_type] = SpecificGuidance(**guidance_data)
        
        return GuidanceResponse(
            company_id=result.get('company_id', request.company_id),
            analysis_summary=result.get('analysis_summary', ''),
            patterns_detected=patterns_detected,
            proposed_specific_guidance=specific_guidance,
            confidence=result.get('confidence', 0.0),
            recommendations=result.get('recommendations', '')
        )

    def validate_pattern_detection(self, request: ValidationRequest) -> ValidationResponse:
        """Validate LLM's ability to detect patterns for guidance integration"""
        
        results = []
        correct_predictions = 0
        
        for i, example in enumerate(request.examples):
            # Build validation prompt
            prompt = f"""You are evaluating whether a correction should be integrated into systematic guidance.

CORRECTION EXAMPLE:
Field: {example.field_name}
Original: "{example.original_value}"
Corrected: "{example.corrected_value}"

DECISION CRITERIA:
- INTEGRATE if the correction reveals a systematic pattern that could help future extractions
- IGNORE if the correction is specific/unique and won't help with other cases

Examples of patterns to INTEGRATE:
- Email/phone contamination removal
- Prefix removal (PO:, ORDER:, etc.)
- Format standardization (currency codes, country codes)
- Systematic formatting issues

Examples to IGNORE:
- Specific name corrections
- Unique value replacements
- One-off fixes

RESPONSE FORMAT:
Return ONLY a JSON object:
{{
  "should_integrate": boolean,
  "reasoning": "brief explanation of the decision"
}}"""
            
            try:
                response_text = self._call_llm(prompt)
                result = self._parse_json_response(response_text)
                
                llm_decision = result.get('should_integrate', False)
                correct_decision = example.should_integrate
                accuracy = llm_decision == correct_decision
                
                if accuracy:
                    correct_predictions += 1
                
                results.append(ValidationResult(
                    example_id=i + 1,
                    field_name=example.field_name,
                    llm_decision=llm_decision,
                    correct_decision=correct_decision,
                    accuracy=accuracy,
                    reasoning=result.get('reasoning', '')
                ))
                
            except Exception as e:
                results.append(ValidationResult(
                    example_id=i + 1,
                    field_name=example.field_name,
                    llm_decision=False,
                    correct_decision=example.should_integrate,
                    accuracy=False,
                    reasoning=f"Error: {str(e)}"
                ))
        
        total_examples = len(request.examples)
        accuracy = correct_predictions / total_examples if total_examples > 0 else 0.0
        
        summary = f"Accuracy: {accuracy:.2%} ({correct_predictions}/{total_examples} correct)"
        
        return ValidationResponse(
            total_examples=total_examples,
            correct_predictions=correct_predictions,
            accuracy=accuracy,
            results=results,
            summary=summary
        )

    def perform_batch_corrections(self, request: BatchCorrectionRequest) -> BatchCorrectionResponse:
        """Process multiple field corrections in batch (sequential)"""
        start_time = time.time()
        results = []
        corrections_made = 0
        
        for item in request.items:
            correction_request = CorrectionRequest(
                field_name=item.field_name,
                current_value=item.current_value,
                specific_guidance=item.specific_guidance
            )
            
            try:
                result = self.perform_correction_inference(correction_request)
                results.append(result)
                if result.correction_needed:
                    corrections_made += 1
            except Exception as e:
                # Handle individual errors gracefully
                error_result = CorrectionResponse(
                    field_name=item.field_name,
                    original_value=item.current_value,
                    correction_needed=False,
                    corrected_value=None,
                    correction_type=CorrectionType.NO_CORRECTION,
                    confidence=0.0,
                    reasoning=f"Error: {str(e)}"
                )
                results.append(error_result)
        
        processing_time = time.time() - start_time
        
        return BatchCorrectionResponse(
            total_items=len(request.items),
            corrections_made=corrections_made,
            results=results,
            processing_time=processing_time,
            company_id=request.company_id
        )
    
    def perform_batch_corrections_parallel(self, request: BatchCorrectionRequest, max_workers: int = 3) -> BatchCorrectionResponse:
        """Process multiple field corrections in parallel"""
        start_time = time.time()
        results = []
        corrections_made = 0
        
        def process_single_item(item: BatchCorrectionItem) -> CorrectionResponse:
            correction_request = CorrectionRequest(
                field_name=item.field_name,
                current_value=item.current_value,
                specific_guidance=item.specific_guidance
            )
            return self.perform_correction_inference(correction_request)
        
        # Parallel processing with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            try:
                results = list(executor.map(process_single_item, request.items))
                corrections_made = sum(1 for result in results if result.correction_needed)
            except Exception as e:
                # Fallback to sequential if parallel fails
                print(f"Parallel processing failed, falling back to sequential: {e}")
                return self.perform_batch_corrections(request)
        
        processing_time = time.time() - start_time
        
        return BatchCorrectionResponse(
            total_items=len(request.items),
            corrections_made=corrections_made,
            results=results,
            processing_time=processing_time,
            company_id=request.company_id
        )
