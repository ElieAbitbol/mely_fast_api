# Data Correction API

A FastAPI application for performing intelligent data correction inference using LLM technology. This API provides endpoints for:

1. **Field Correction Inference** - Analyze field values and suggest corrections
2. **Company-Specific Guidance Building** - Generate custom correction guidance from patterns
3. **Pattern Detection Validation** - Validate the accuracy of pattern detection for guidance integration

## Features

- **Pure LLM Inference**: Direct field correction using Google Gemini
- **Company Guidance Builder**: Analyze correction patterns to build specific guidance
- **Pattern Detection Validator**: Test LLM accuracy in detecting systematic vs. specific corrections
- **Optimized for Shipping/Logistics Data**: Pre-configured for maritime shipping fields (vessel names, PO numbers, quantities, etc.)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. Run the application:
   ```bash
   uvicorn app.api:app --reload --port 8000
   ```

## API Endpoints

### 1. Field Correction (`POST /correct`)

Analyze a field value and determine if correction is needed.

**Request Body:**
```json
{
  "field_name": "vessel_name",
  "current_value": "MAERSK LINE EMAIL@COMPANY.COM",
  "specific_guidance": null
}
```

**Response:**
```json
{
  "field_name": "vessel_name",
  "original_value": "MAERSK LINE EMAIL@COMPANY.COM",
  "correction_needed": true,
  "corrected_value": "MAERSK LINE",
  "correction_type": "email_contamination",
  "confidence": 0.95,
  "reasoning": "Removed email contamination from vessel name"
}
```

### 2. Company Guidance Building (`POST /guidance`)

Build company-specific guidance from frequent correction patterns.

**Request Body:**
```json
{
  "company_id": "MAERSK_GROUP",
  "frequent_corrections": [
    {
      "field_name": "vessel_name",
      "original_value": "MAERSK LINE INFO@MAERSK.COM",
      "corrected_value": "MAERSK LINE",
      "frequency": 15
    }
  ]
}
```

**Response:**
```json
{
  "company_id": "MAERSK_GROUP",
  "analysis_summary": "Detected systematic email contamination patterns",
  "patterns_detected": [...],
  "proposed_specific_guidance": {...},
  "confidence": 0.88,
  "recommendations": "Implement email filtering in extraction pipeline"
}
```

### 3. Pattern Validation (`POST /validate`)

Validate LLM's ability to detect systematic patterns vs. specific corrections.

**Request Body:**
```json
{
  "examples": [
    {
      "field_name": "vessel_name",
      "original_value": "SHIP ALPHA",
      "corrected_value": "M.V. OCEAN STAR",
      "should_integrate": false,
      "reason": "Specific correction, not a pattern"
    }
  ]
}
```

**Response:**
```json
{
  "total_examples": 1,
  "correct_predictions": 1,
  "accuracy": 1.0,
  "results": [...],
  "summary": "Accuracy: 100% (1/1 correct)"
}
```

## Supported Field Types

The API is optimized for shipping/logistics data with built-in support for:

- **vessel_name**: Ship/vessel names
- **cargo_control**: Cargo Control Numbers (CCN)
- **po_number**: Purchase Order numbers
- **quantity**: Merchandise quantities
- **currency**: Currency codes (USD, EUR, etc.)
- **country**: Country codes (US, CA, etc.)
- **company_name**: Company names (shipper, consignee, vendor)
- **address**: Postal addresses
- **weight**: Cargo weights

## Common Correction Types

- `email_contamination`: Remove email addresses from fields
- `phone_contamination`: Remove phone numbers from fields
- `website_contamination`: Remove website URLs from fields
- `prefix_removal`: Remove prefixes like "PO:", "ORDER:", etc.
- `format_standardization`: Standardize formats (currency codes, country codes)
- `quantity_formatting`: Fix quantity number formatting
- `no_correction`: No correction needed

## Testing

Use the provided example script to test all endpoints:

```bash
python examples/test_api.py
```

Make sure the API server is running before executing the test script.

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `APP_NAME`: Application name (optional)
- `DEBUG`: Debug mode (optional)
- `PORT`: Server port (optional, default: 8000)

## Docker Support

The application includes Docker support with the existing Dockerfile and Makefile configurations.

## Development

The application follows FastAPI best practices with:

- **Pydantic models** for request/response validation
- **Service layer** for business logic separation
- **Error handling** with proper HTTP status codes
- **Type hints** throughout the codebase
- **Modular structure** for easy maintenance

## Original Scripts Integration

This API integrates the functionality from three original Python scripts:

1. **5 - pure_llm_inference.py** → `/correct` endpoint
2. **6 - company_guidance_builder.py** → `/guidance` endpoint  
3. **7 - pattern_detection_validator.py** → `/validate` endpoint

All scripts have been translated to English and optimized for FastAPI integration while maintaining their core functionality.
