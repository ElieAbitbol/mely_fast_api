#!/usr/bin/env python3
"""
Example usage of the Data Correction API

This script demonstrates how to use the three main endpoints:
1. /correct - Perform field correction inference
2. /guidance - Build company-specific guidance
3. /validate - Validate pattern detection accuracy
"""

import requests
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"


def test_correction_endpoint():
    """Test the correction inference endpoint"""
    print("=" * 60)
    print("TESTING CORRECTION ENDPOINT")
    print("=" * 60)
    
    # Test case 1: Vessel name with email contamination
    test_data = {
        "field_name": "vessel_name",
        "current_value": "MAERSK LINE CUSTOMER.SERVICE@MAERSK.COM",
        "specific_guidance": None
    }
    
    print(f"Testing field: {test_data['field_name']}")
    print(f"Current value: {test_data['current_value']}")
    print()
    
    try:
        response = requests.post(f"{API_BASE_URL}/correct", json=test_data)
        response.raise_for_status()
        
        result = response.json()
        print("CORRECTION RESULT:")
        print(f"  Correction needed: {result['correction_needed']}")
        print(f"  Corrected value: {result['corrected_value']}")
        print(f"  Correction type: {result['correction_type']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Reasoning: {result['reasoning']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
    
    print()


def test_guidance_endpoint():
    """Test the company guidance building endpoint"""
    print("=" * 60)
    print("TESTING GUIDANCE ENDPOINT")
    print("=" * 60)
    
    # Sample frequent corrections data
    test_data = {
        "company_id": "MAERSK_GROUP",
        "frequent_corrections": [
            {
                "field_name": "vessel_name",
                "original_value": "MAERSK LINE CUSTOMER.SERVICE@MAERSK.COM",
                "corrected_value": "MAERSK LINE",
                "frequency": 15
            },
            {
                "field_name": "vessel_name",
                "original_value": "CMA CGM CONTACT: +33123456789",
                "corrected_value": "CMA CGM",
                "frequency": 12
            },
            {
                "field_name": "po_number",
                "original_value": "PO: 12345-ABC",
                "corrected_value": "12345-ABC",
                "frequency": 8
            },
            {
                "field_name": "quantity",
                "original_value": "1,250.00 CARTONS",
                "corrected_value": "1250 CARTONS",
                "frequency": 10
            }
        ]
    }
    
    print(f"Analyzing corrections for company: {test_data['company_id']}")
    print(f"Number of corrections: {len(test_data['frequent_corrections'])}")
    print()
    
    try:
        response = requests.post(f"{API_BASE_URL}/guidance", json=test_data)
        response.raise_for_status()
        
        result = response.json()
        print("GUIDANCE ANALYSIS RESULT:")
        print(f"  Company ID: {result['company_id']}")
        print(f"  Analysis Summary: {result['analysis_summary']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Patterns Detected: {len(result['patterns_detected'])}")
        
        for i, pattern in enumerate(result['patterns_detected'], 1):
            print(f"    Pattern {i}: {pattern['field_type']} - {pattern['pattern_description']}")
        
        print(f"  Recommendations: {result['recommendations']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
    
    print()


def test_validation_endpoint():
    """Test the pattern detection validation endpoint"""
    print("=" * 60)
    print("TESTING VALIDATION ENDPOINT")
    print("=" * 60)
    
    # Sample validation examples
    test_data = {
        "examples": [
            {
                "field_name": "vessel_name",
                "original_value": "MAERSK LINE INFO@MAERSK.COM",
                "corrected_value": "MAERSK LINE",
                "should_integrate": True,
                "reason": "Email contamination pattern"
            },
            {
                "field_name": "vessel_name",
                "original_value": "CONTAINER SHIP ALPHA",
                "corrected_value": "M.V. OCEAN STAR",
                "should_integrate": False,
                "reason": "Specific vessel name correction, not a pattern"
            },
            {
                "field_name": "po_number",
                "original_value": "PO: 12345-ABC",
                "corrected_value": "12345-ABC",
                "should_integrate": True,
                "reason": "PO prefix removal pattern"
            },
            {
                "field_name": "currency",
                "original_value": "US DOLLARS",
                "corrected_value": "USD",
                "should_integrate": True,
                "reason": "Currency standardization pattern"
            }
        ]
    }
    
    print(f"Testing pattern detection with {len(test_data['examples'])} examples")
    print()
    
    try:
        response = requests.post(f"{API_BASE_URL}/validate", json=test_data)
        response.raise_for_status()
        
        result = response.json()
        print("VALIDATION RESULT:")
        print(f"  Total Examples: {result['total_examples']}")
        print(f"  Correct Predictions: {result['correct_predictions']}")
        print(f"  Accuracy: {result['accuracy']:.2%}")
        print(f"  Summary: {result['summary']}")
        print()
        
        print("DETAILED RESULTS:")
        for res in result['results']:
            status = "✓" if res['accuracy'] else "✗"
            print(f"  {status} Example {res['example_id']}: {res['field_name']}")
            print(f"    LLM Decision: {res['llm_decision']}")
            print(f"    Correct Decision: {res['correct_decision']}")
            print(f"    Reasoning: {res['reasoning']}")
            print()
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")


def test_api_health():
    """Test basic API health endpoints"""
    print("=" * 60)
    print("TESTING API HEALTH")
    print("=" * 60)
    
    try:
        # Test root endpoint
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        print(f"Root endpoint: {response.json()}")
        
        # Test ping endpoint
        response = requests.get(f"{API_BASE_URL}/ping")
        response.raise_for_status()
        print(f"Ping endpoint: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
    
    print()


if __name__ == "__main__":
    print("Data Correction API - Example Usage")
    print("Make sure the API server is running on localhost:8000")
    print()
    
    # Test all endpoints
    test_api_health()
    test_correction_endpoint()
    test_guidance_endpoint()
    test_validation_endpoint()
    
    print("=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)
