#!/usr/bin/env python3
"""
Startup script for the Data Correction API

This script loads environment variables and starts the FastAPI server.
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    # Check if Gemini API key is configured
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("WARNING: GEMINI_API_KEY not configured!")
        print("Please set your Gemini API key in the .env file")
        print("The API will still start but LLM features will not work")
        print()
    else:
        print("Gemini API key configured")
    
    print(f"Starting Data Correction API on port {port}")
    print(f"Debug mode: {debug}")
    print(f"API docs available at: http://localhost:{port}/docs")
    print()
    
    # Start the server
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=port,
        reload=debug
    )
