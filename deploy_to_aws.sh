#!/bin/bash

# Direct deployment script to AWS ECS
# This script builds, pushes, and deploys the application directly to AWS

set -e

# Configuration
AWS_REGION="us-east-2"
ECR_REPOSITORY="recruiting-candidate-ranker"
ECS_CLUSTER="recruiting-candidate-ranker"
ECS_SERVICE="recruiting-candidate-ranker"
IMAGE_TAG=$(git rev-parse --short HEAD)

echo "=========================================="
echo "Deploying to AWS ECS"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "ECR Repository: $ECR_REPOSITORY"
echo "ECS Cluster: $ECS_CLUSTER"
echo "ECS Service: $ECS_SERVICE"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
FULL_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
LATEST_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR Registry: $ECR_REGISTRY"
echo "Full Image Name: $FULL_IMAGE_NAME"
echo ""

# Step 1: Login to ECR
echo "Step 1: Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
echo "✓ Logged in to ECR"
echo ""

# Step 2: Build Docker image
echo "Step 2: Building Docker image..."
docker buildx create --use --name multiarch-builder 2>/dev/null || true
docker buildx build \
    --platform linux/amd64 \
    --tag $FULL_IMAGE_NAME \
    --tag $LATEST_IMAGE_NAME \
    --load \
    --provenance=false \
    --sbom=false \
    .
echo "✓ Docker image built"
echo ""

# Step 3: Push to ECR
echo "Step 3: Pushing image to ECR..."
docker push $FULL_IMAGE_NAME
docker push $LATEST_IMAGE_NAME
echo "✓ Image pushed to ECR"
echo ""

# Step 4: Download current task definition
echo "Step 4: Downloading current task definition..."
aws ecs describe-task-definition \
    --task-definition $ECS_SERVICE \
    --query taskDefinition \
    --region $AWS_REGION \
    > task-definition.json
echo "✓ Task definition downloaded"
echo ""

# Step 5: Update task definition with new image
echo "Step 5: Updating task definition with new image..."
# Use Python to update the image in the task definition
python3 << EOF
import json

with open('task-definition.json', 'r') as f:
    task_def = json.load(f)

# Update the image for the 'app' container
for container in task_def.get('containerDefinitions', []):
    if container['name'] == 'app':
        container['image'] = '$FULL_IMAGE_NAME'
        print(f"Updated container 'app' image to: {container['image']}")

# Remove fields that can't be in new task definition
task_def.pop('taskDefinitionArn', None)
task_def.pop('revision', None)
task_def.pop('status', None)
task_def.pop('requiresAttributes', None)
task_def.pop('compatibilities', None)
task_def.pop('registeredAt', None)
task_def.pop('registeredBy', None)

with open('task-definition-new.json', 'w') as f:
    json.dump(task_def, f, indent=2)
EOF

echo "✓ Task definition updated"
echo ""

# Step 6: Register new task definition
echo "Step 6: Registering new task definition..."
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://task-definition-new.json \
    --region $AWS_REGION \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
echo "✓ New task definition registered: $NEW_TASK_DEF_ARN"
echo ""

# Step 7: Update ECS service
echo "Step 7: Updating ECS service..."
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --task-definition $NEW_TASK_DEF_ARN \
    --region $AWS_REGION \
    --force-new-deployment \
    > /dev/null
echo "✓ ECS service updated"
echo ""

# Step 8: Wait for service to stabilize
echo "Step 8: Waiting for service to stabilize..."
echo "This may take a few minutes..."
aws ecs wait services-stable \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION
echo "✓ Service is stable"
echo ""

# Step 9: Get service status
echo "Step 9: Verifying deployment..."
RUNNING=$(aws ecs describe-services \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION \
    --query 'services[0].runningCount' \
    --output text)
DESIRED=$(aws ecs describe-services \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION \
    --query 'services[0].desiredCount' \
    --output text)

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Service: $ECS_SERVICE"
echo "Image: $FULL_IMAGE_NAME"
echo "Running tasks: $RUNNING / $DESIRED"
echo ""
echo "The application is now live on AWS!"
echo ""

# Cleanup
rm -f task-definition.json task-definition-new.json

