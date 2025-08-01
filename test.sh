#!/bin/bash

# Default values
PORT=${PORT:-8000}
HOST=${HOST:-localhost}
BASE_URL="http://$HOST:$PORT"

# Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
RESET="\033[0m"

# Function to test endpoint
test_endpoint() {
  local endpoint=$1
  local description=$2

  echo -n "🔍 Testing $description ($BASE_URL$endpoint)... "

  if curl --fail --silent "$BASE_URL$endpoint" > /dev/null; then
    echo -e "${GREEN}✅ OK${RESET}"
  else
    echo -e "${RED}❌ FAILED${RESET}"
    exit 1
  fi
}

# Test endpoints
test_endpoint "/data" "Data Endpoint"
test_endpoint "/ping" "Ping Endpoint"
test_endpoint "/docs" "Swagger UI"

echo -e "${GREEN}🎉 All tests passed!${RESET}"
