#!/bin/bash
set -e

IMAGE_TAG="migration-20260109-113350"
ECR_REPO="774305585062.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker"
FULL_IMAGE="$ECR_REPO:$IMAGE_TAG"

echo "Getting DATABASE_URL..."
DATABASE_URL=$(aws ssm get-parameter --name "/recruiting-candidate-ranker/DATABASE_URL" --region us-east-2 --with-decryption --query 'Parameter.Value' --output text)

echo "Getting network config..."
NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster internal_recruiting_candidate_ranker \
  --services internal_recruiting_candidate_ranker \
  --region us-east-2 \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' \
  --output json)

SUBNETS=$(echo "$NETWORK_CONFIG" | jq -r '.subnets[0]')
SECURITY_GROUPS=$(echo "$NETWORK_CONFIG" | jq -r '.securityGroups[0] // empty')

if [ -n "$SECURITY_GROUPS" ]; then
  NETWORK_JSON="{\"awsvpcConfiguration\":{\"subnets\":[\"$SUBNETS\"],\"securityGroups\":[\"$SECURITY_GROUPS\"],\"assignPublicIp\":\"DISABLED\"}}"
else
  NETWORK_JSON="{\"awsvpcConfiguration\":{\"subnets\":[\"$SUBNETS\"],\"assignPublicIp\":\"DISABLED\"}}"
fi

echo "Running migration task with image: $FULL_IMAGE"
TASK_ARN=$(aws ecs run-task \
  --cluster internal_recruiting_candidate_ranker \
  --task-definition internal-recruiting-candidate-ranker \
  --launch-type FARGATE \
  --network-configuration "$NETWORK_JSON" \
  --overrides "{\"containerOverrides\":[{\"name\":\"app\",\"image\":\"$FULL_IMAGE\",\"command\":[\"python3\",\"migrate_analyses.py\"],\"environment\":[{\"name\":\"DATABASE_URL\",\"value\":\"$DATABASE_URL\"}]}]}" \
  --region us-east-2 \
  --query 'tasks[0].taskArn' \
  --output text)

echo "✓ Migration task started: $TASK_ARN"
echo ""
echo "To monitor logs:"
echo "  aws logs tail /ecs/recruiting-candidate-ranker --follow --region us-east-2"
echo ""
echo "To check status:"
echo "  aws ecs describe-tasks --cluster internal_recruiting_candidate_ranker --tasks $TASK_ARN --region us-east-2"
