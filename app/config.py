# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional, Dict


class Settings(BaseSettings):
    app_name: str = "Data Correction API"
    debug: bool = False
    environment: str = "production"
    
    # LLM Configuration
    gemini_api_key: Optional[str] = None
    
    # Docker configuration (optional)
    docker_username: Optional[str] = None
    port: Optional[str] = "8000"
    image_name: Optional[str] = "fastapi-image"
    container_name: Optional[str] = "fastapi-container"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields


settings = Settings()


# Field Type Configurations
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

# Field Guidance Templates
FIELD_GUIDANCE = {
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
    },
    'other': {
        'description': 'General field validation',
        'patterns': 'Appropriate format for field type',
        'common_errors': 'Format inconsistencies, contamination',
        'examples': 'Clean, properly formatted values'
    }
}

# Prompt Templates
CORRECTION_PROMPT_TEMPLATE = """You are an expert data quality validator for shipping/logistics data extraction.

FIELD ANALYSIS:
- Field Name: {field_name}
- Field Type: {field_type}
- Current Value: "{current_value}"

FIELD GUIDANCE:
Description: {description}
Expected Patterns: {patterns}
Common Errors: {common_errors}
Examples: {examples}

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

GUIDANCE_PROMPT_TEMPLATE = """You are an expert in data quality pattern detection for automated correction systems.

TASK: Analyze the frequent corrections to build company-specific guidance for '{company_id}'.

FREQUENT CORRECTIONS:
{corrections_data}

PATTERN DETECTION CRITERIA:
- Systematic formatting issues (prefixes, suffixes, standardization)
- Consistent contamination removal (emails, phones, URLs)
- Repeatable transformation rules
- High frequency indicates systematic nature

ANALYSIS GOALS:
1. Identify clear patterns that can be automated
2. Recommend field-specific guidance improvements
3. Assess pattern confidence and applicability

RESPONSE FORMAT (JSON ONLY):
{{
  "patterns_detected": [
    {{
      "field_name": "field name",
      "pattern_type": "email_contamination|phone_contamination|prefix_removal|format_standardization",
      "description": "clear pattern description",
      "examples": ["example1", "example2"],
      "frequency": number,
      "confidence": 0.0-1.0
    }}
  ],
  "proposed_specific_guidance": {{
    "field_name": {{
      "description": "updated description",
      "patterns": "updated patterns",
      "common_errors": "updated common errors",
      "examples": "updated examples"
    }}
  }},
  "confidence": 0.0-1.0,
  "summary": "brief analysis summary"
}}"""

VALIDATION_PROMPT_TEMPLATE = """You are an expert in data quality pattern validation for shipping/logistics systems.

TASK: Validate pattern detection accuracy using these test examples.

TEST EXAMPLES:
{validation_examples}

VALIDATION CRITERIA:
- Should the example correction be integrated as a pattern? (true/false)
- Consider frequency, systematic nature, and automation potential
- Patterns should be repeatable across different data contexts

RESPONSE FORMAT (JSON ONLY):
{{
  "predictions": [
    {{
      "field_name": "field name",
      "should_integrate": true/false,
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation"
    }}
  ],
  "overall_accuracy": 0.0-1.0,
  "summary": "validation summary"
}}"""
