#!/bin/bash
# Script to run the migration as an ECS one-off task

set -e

echo "=========================================="
echo "Running Analysis Migration on ECS"
echo "=========================================="

# Get cluster and task definition info
CLUSTER_NAME="internal_recruiting_candidate_ranker"
TASK_DEFINITION="internal-recruiting-candidate-ranker"
REGION="us-east-2"

# Get subnet and security group from existing service
echo "Getting network configuration from existing service..."
SERVICE_NAME="internal_recruiting_candidate_ranker"
NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --region "$REGION" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' \
  --output json)

SUBNETS=$(echo "$NETWORK_CONFIG" | jq -r '.subnets[]' | tr '\n' ',' | sed 's/,$//')
SECURITY_GROUPS=$(echo "$NETWORK_CONFIG" | jq -r '.securityGroups[]?' | tr '\n' ',' | sed 's/,$//' || echo "")

echo "Subnets: $SUBNETS"
echo "Security Groups: $SECURITY_GROUPS"

# Prepare network configuration
if [ -n "$SECURITY_GROUPS" ]; then
  NETWORK_JSON="{\"awsvpcConfiguration\":{\"subnets\":[\"$(echo $SUBNETS | cut -d',' -f1)\"],\"securityGroups\":[\"$SECURITY_GROUPS\"],\"assignPublicIp\":\"DISABLED\"}}"
else
  NETWORK_JSON="{\"awsvpcConfiguration\":{\"subnets\":[\"$(echo $SUBNETS | cut -d',' -f1)\"],\"assignPublicIp\":\"DISABLED\"}}"
fi

# Get DATABASE_URL from SSM (we'll pass it as env var since task may not have SSM access)
echo "Getting DATABASE_URL from SSM..."
DATABASE_URL=$(aws ssm get-parameter --name "/recruiting-candidate-ranker/DATABASE_URL" --region "$REGION" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null)

if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: Could not retrieve DATABASE_URL from SSM Parameter Store"
  exit 1
fi

echo ""
echo "Running migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER_NAME" \
  --task-definition "$TASK_DEFINITION" \
  --launch-type FARGATE \
  --network-configuration "$NETWORK_JSON" \
  --overrides "{
    \"containerOverrides\": [{
      \"name\": \"app\",
      \"command\": [\"python3\", \"migrate_analyses.py\"],
      \"environment\": [
        {
          \"name\": \"DATABASE_URL\",
          \"value\": \"$DATABASE_URL\"
        }
      ]
    }]
  }" \
  --region "$REGION" \
  --query 'tasks[0].taskArn' \
  --output text)

echo "✓ Migration task started: $TASK_ARN"
echo ""
echo "To view logs, run:"
echo "  aws logs tail /ecs/recruiting-candidate-ranker --follow --region $REGION"
echo ""
echo "To check task status:"
echo "  aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --region $REGION"
