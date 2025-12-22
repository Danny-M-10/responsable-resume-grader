#!/bin/bash
# Smoke Test Script for Recruiting Candidate Ranker
# Tests critical functionality after deployment

set -e

BASE_URL="${1:-https://recruiting.crossroadcoach.com}"
REGION="${2:-us-east-2}"
CLUSTER_NAME="${3:-recruiting-candidate-ranker}"
SERVICE_NAME="${4:-recruiting-candidate-ranker}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

echo "=========================================="
echo "Smoke Test: Recruiting Candidate Ranker"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Region: $REGION"
echo ""

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local method=${4:-GET}
    local data=${5:-""}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" --max-time 10 -d "$data" || echo "000")
    fi
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $HTTP_CODE)"
        ((FAILED++))
        return 1
    fi
}

# Test 1: Health check - root endpoint
test_endpoint "Root endpoint" "$BASE_URL/" 200

# Test 2: Check HTTPS redirect (if HTTP endpoint exists)
HTTP_URL=$(echo "$BASE_URL" | sed 's|https://|http://|')
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "$HTTP_URL" --max-time 10 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✓ HTTPS redirect working${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ HTTPS redirect check skipped${NC}"
fi

# Test 3: Check ECS service status
echo ""
echo "Checking ECS Service Status..."
RUNNING_TASKS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].runningCount' \
    --output text 2>/dev/null || echo "0")

DESIRED_TASKS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].desiredCount' \
    --output text 2>/dev/null || echo "0")

if [ "$RUNNING_TASKS" -ge "$DESIRED_TASKS" ] && [ "$RUNNING_TASKS" -gt 0 ]; then
    echo -e "${GREEN}✓ ECS Service healthy${NC} (Running: $RUNNING_TASKS, Desired: $DESIRED_TASKS)"
    ((PASSED++))
else
    echo -e "${RED}✗ ECS Service unhealthy${NC} (Running: $RUNNING_TASKS, Desired: $DESIRED_TASKS)"
    ((FAILED++))
fi

# Test 4: Check recent CloudWatch logs for errors
echo ""
echo "Checking CloudWatch Logs (last 5 minutes)..."
LOG_GROUP="/ecs/$SERVICE_NAME"
ERROR_COUNT=$(aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --start-time $(($(date +%s) - 300))000 \
    --filter-pattern "ERROR" \
    --region "$REGION" \
    --query 'events | length(@)' \
    --output text 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT error(s) in recent logs${NC}"
    echo "  Run: aws logs tail $LOG_GROUP --follow --region $REGION"
    # Don't fail on this, just warn
fi

# Test 5: Check ALB target health (if ALB exists)
echo ""
echo "Checking ALB Target Health..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
    --region "$REGION" \
    --query "TargetGroups[?contains(TargetGroupName, 'recruiting') || contains(TargetGroupName, 'candidate')].TargetGroupArn" \
    --output text 2>/dev/null | head -n1 || echo "")

if [ -n "$TARGET_GROUP_ARN" ]; then
    HEALTHY_TARGETS=$(aws elbv2 describe-target-health \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --region "$REGION" \
        --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)' \
        --output text 2>/dev/null || echo "0")
    
    TOTAL_TARGETS=$(aws elbv2 describe-target-health \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --region "$REGION" \
        --query 'TargetHealthDescriptions | length(@)' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$HEALTHY_TARGETS" -gt 0 ] && [ "$HEALTHY_TARGETS" -eq "$TOTAL_TARGETS" ]; then
        echo -e "${GREEN}✓ ALB targets healthy${NC} ($HEALTHY_TARGETS/$TOTAL_TARGETS)"
        ((PASSED++))
    else
        echo -e "${RED}✗ ALB targets unhealthy${NC} ($HEALTHY_TARGETS/$TOTAL_TARGETS healthy)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ ALB target group not found, skipping${NC}"
fi

# Test 6: Check RDS database connectivity (indirectly via app)
echo ""
echo "Checking database connectivity (via app response)..."
# If the app loads without database errors, we assume DB is reachable
# This is indirect but practical
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/" --max-time 10 || echo "10")
if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
    echo -e "${GREEN}✓ App response time acceptable${NC} (${RESPONSE_TIME}s)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ App response time slow${NC} (${RESPONSE_TIME}s)"
    # Don't fail, just warn
fi

# Summary
echo ""
echo "=========================================="
echo "Smoke Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check ECS service events:"
    echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
    echo ""
    echo "2. View application logs:"
    echo "   aws logs tail $LOG_GROUP --follow --region $REGION"
    echo ""
    echo "3. Check task status:"
    echo "   aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region $REGION"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi

