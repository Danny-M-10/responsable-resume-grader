#!/bin/bash
# Simplified test runner with better error handling

BASE_URL="https://recruiting.crossroadcoach.com"
TEST_EMAIL="testuser2026@example.com"
TEST_PASSWORD="TestPassword123!"

echo "Testing API connection..."
LOGIN_RESPONSE=$(curl -s --max-time 30 -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

echo "Login response received (length: ${#LOGIN_RESPONSE})"
echo "First 200 chars: ${LOGIN_RESPONSE:0:200}"

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    token = d.get('access_token', '')
    print(token if token else 'NO_TOKEN')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

echo "Token extracted: ${TOKEN:0:30}..."
if [ -z "$TOKEN" ] || [ "$TOKEN" = "NO_TOKEN" ] || [ "$TOKEN" = "ERROR"* ]; then
    echo "Login failed. Full response:"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "Login successful! Running full test..."
echo ""

# Run the actual test script
exec ./test_full_analysis.sh
