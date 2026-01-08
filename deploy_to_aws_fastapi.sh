#!/bin/bash

# Deployment script for FastAPI + React application to AWS ECS
# Maintains database connection from existing deployment

set -e

# Configuration
AWS_REGION="us-east-2"
ECR_REPOSITORY="recruiting-candidate-ranker"
ECS_CLUSTER="internal_recruiting_candidate_ranker"
ECS_SERVICE="internal_recruiting_candidate_ranker"
IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "=========================================="
echo "Deploying FastAPI + React to AWS ECS"
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

# Step 2: Build Docker image (multi-stage for frontend + backend)
echo "Step 2: Building Docker image (multi-stage: frontend + backend)..."
docker buildx create --use --name multiarch-builder 2>/dev/null || true
docker buildx build \
    --platform linux/amd64 \
    --tag $FULL_IMAGE_NAME \
    --tag $LATEST_IMAGE_NAME \
    --load \
    --provenance=false \
    --sbom=false \
    --no-cache \
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
TASK_DEF_NAME=$ECS_SERVICE
if ! aws ecs describe-task-definition \
    --task-definition $TASK_DEF_NAME \
    --query taskDefinition \
    --region $AWS_REGION \
    > task-definition.json 2>/dev/null; then
    echo "Task definition $TASK_DEF_NAME not found, using recruiting-candidate-ranker as template..."
    TASK_DEF_NAME="recruiting-candidate-ranker"
    aws ecs describe-task-definition \
        --task-definition $TASK_DEF_NAME \
        --query taskDefinition \
        --region $AWS_REGION \
        > task-definition.json
    # Update the family name to match the new service (use hyphens, not underscores)
    python3 << 'FAMILY_UPDATE'
import json
with open('task-definition.json', 'r') as f:
    task_def = json.load(f)
# ECS task definition family names must use hyphens, not underscores
task_def['family'] = 'internal-recruiting-candidate-ranker'
with open('task-definition.json', 'w') as f:
    json.dump(task_def, f, indent=2)
FAMILY_UPDATE
fi
echo "✓ Task definition downloaded (family: $TASK_DEF_NAME)"
echo ""

# Step 5: Update task definition with new image and port
echo "Step 5: Updating task definition with new image and configuration..."
python3 << EOF
import json

with open('task-definition.json', 'r') as f:
    task_def = json.load(f)

# Update the image and port for the 'app' container
for container in task_def.get('containerDefinitions', []):
    if container['name'] == 'app':
        container['image'] = '$FULL_IMAGE_NAME'
        # Update port from 8501 (Streamlit) to 8000 (FastAPI)
        container['portMappings'] = [{"containerPort": 8000, "protocol": "tcp"}]
        # Update environment variables
        for env_var in container.get('environment', []):
            if env_var['name'] == 'PORT':
                env_var['value'] = '8000'
        # Update health check for FastAPI
        container['healthCheck'] = {
            "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 30
        }
        print(f"Updated container 'app' image to: {container['image']}")
        print(f"Updated container port to: 8000")
        print(f"Updated health check endpoint to: /health")

# Ensure family name uses hyphens (not underscores) for ECS compatibility
if 'family' in task_def:
    task_def['family'] = task_def['family'].replace('_', '-')

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

# Step 7: Update ALB target group first (if it exists)
echo "Step 7a: Updating ALB target group port (if needed)..."
# Get target group ARN from service
TARGET_GROUP_ARN=$(aws ecs describe-services \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION \
    --query 'services[0].loadBalancers[0].targetGroupArn' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$TARGET_GROUP_ARN" ] && [ "$TARGET_GROUP_ARN" != "None" ]; then
    # Get current target group port
    CURRENT_PORT=$(aws elbv2 describe-target-groups \
        --target-group-arns "$TARGET_GROUP_ARN" \
        --region $AWS_REGION \
        --query 'TargetGroups[0].Port' \
        --output text 2>/dev/null || echo "8501")
    
    if [ "$CURRENT_PORT" != "8000" ]; then
        echo "⚠  Target group port is $CURRENT_PORT, but container uses 8000"
        echo "   Note: Target group port cannot be changed after creation."
        echo "   The service will use container port 8000, which should work with ALB routing."
        echo "   If health checks fail, you may need to create a new target group on port 8000."
    else
        echo "✓ Target group already on port 8000"
    fi
    
    # Update health check path to /health
    echo "Updating target group health check to /health..."
    aws elbv2 modify-target-group-attributes \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --attributes "Key=health_check_path,Value=/health" \
        --region $AWS_REGION \
        > /dev/null 2>&1 && echo "✓ Health check path updated to /health" || echo "⚠  Could not update health check path"
else
    echo "⚠  No target group found (service may not have load balancer)"
fi
echo ""

# Step 7b: Update ECS service
echo "Step 7b: Updating ECS service..."
# Check if service exists
if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    # Service exists, get load balancer config and update port
    LOAD_BALANCER_CONFIG=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].loadBalancers[0]' \
        --output json 2>/dev/null)
    
    if [ ! -z "$LOAD_BALANCER_CONFIG" ] && [ "$LOAD_BALANCER_CONFIG" != "null" ]; then
        # Update load balancer config to use port 8000
        TARGET_GROUP_ARN=$(echo "$LOAD_BALANCER_CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin).get('targetGroupArn', ''))")
        CONTAINER_NAME=$(echo "$LOAD_BALANCER_CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin).get('containerName', 'app'))")
        CONTAINER_PORT=$(echo "$LOAD_BALANCER_CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin).get('containerPort', 8000))")
        
        # Update service with new task definition and updated load balancer config
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --task-definition $NEW_TASK_DEF_ARN \
            --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=$CONTAINER_NAME,containerPort=8000" \
            --region $AWS_REGION \
            --force-new-deployment \
            > /dev/null
        echo "✓ ECS service updated with port 8000"
    else
        # No load balancer, just update task definition
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --task-definition $NEW_TASK_DEF_ARN \
            --region $AWS_REGION \
            --force-new-deployment \
            > /dev/null
        echo "✓ ECS service updated"
    fi
else
    echo "Service doesn't exist, creating new service..."
    # Get network config from existing service as template
    NETWORK_CONFIG=$(aws ecs describe-services --cluster recruiting-candidate-ranker --services recruiting-candidate-ranker --region $AWS_REGION --query 'services[0].networkConfiguration' --output json 2>/dev/null)
    LOAD_BALANCER=$(aws ecs describe-services --cluster recruiting-candidate-ranker --services recruiting-candidate-ranker --region $AWS_REGION --query 'services[0].loadBalancers[0]' --output json 2>/dev/null)
    
    # Create service
    aws ecs create-service \
        --cluster $ECS_CLUSTER \
        --service-name $ECS_SERVICE \
        --task-definition $NEW_TASK_DEF_ARN \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "$NETWORK_CONFIG" \
        --load-balancers "$LOAD_BALANCER" \
        --region $AWS_REGION \
        > /dev/null
    echo "✓ ECS service created"
fi
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

# Step 9: Verify deployment
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
echo "Port: 8000 (FastAPI)"
echo ""
echo "Database: Using existing DATABASE_URL from SSM Parameter Store"
echo "The application is now live on AWS!"
echo ""
echo "Note: If ALB target group port was not automatically updated,"
echo "      you may need to manually update it from 8501 to 8000"
echo ""

# Cleanup
rm -f task-definition.json task-definition-new.json

