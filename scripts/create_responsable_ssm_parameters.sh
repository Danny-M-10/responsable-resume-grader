#!/bin/bash

# Script to create SSM parameters for ResponsAble application
# Ensures complete separation from internal_recruiting_candidate_ranker parameters

set -e

AWS_REGION="us-east-2"
DB_INSTANCE_IDENTIFIER="responsable-recruitment-ai-db"
DB_NAME="responsable_appdb"
MASTER_USERNAME="responsable_admin"

echo "=========================================="
echo "Creating ResponsAble SSM Parameters"
echo "=========================================="
echo "Region: $AWS_REGION"
echo ""

# Get database endpoint
echo "Getting database endpoint..."
ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --region "$AWS_REGION" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text 2>/dev/null)

if [ -z "$ENDPOINT" ] || [ "$ENDPOINT" = "None" ]; then
    echo "✗ Database endpoint not found. Is the database created and available?"
    echo "  Run create_responsable_database.sh first"
    exit 1
fi

echo "✓ Database endpoint: $ENDPOINT"

# Get master password from SSM Parameter Store
SSM_PASSWORD_PARAM="/responsable-recruitment-ai/DB_MASTER_PASSWORD"
echo "Retrieving master password from SSM Parameter Store..."
MASTER_PASSWORD=$(aws ssm get-parameter \
    --name "$SSM_PASSWORD_PARAM" \
    --region "$AWS_REGION" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text 2>/dev/null)

if [ -z "$MASTER_PASSWORD" ]; then
    echo "✗ Could not retrieve master password from SSM Parameter Store"
    echo "  Parameter: $SSM_PASSWORD_PARAM"
    exit 1
fi

echo "✓ Password retrieved from SSM Parameter Store"

# Build DATABASE_URL
DATABASE_URL="postgresql://${MASTER_USERNAME}:${MASTER_PASSWORD}@${ENDPOINT}:5432/${DB_NAME}"

# Create DATABASE_URL parameter
echo ""
echo "Creating SSM parameter: /responsable-recruitment-ai/DATABASE_URL"
if aws ssm get-parameter --name "/responsable-recruitment-ai/DATABASE_URL" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "⚠  Parameter already exists, updating..."
    aws ssm put-parameter \
        --name "/responsable-recruitment-ai/DATABASE_URL" \
        --value "$DATABASE_URL" \
        --type "SecureString" \
        --overwrite \
        --region "$AWS_REGION" >/dev/null
    echo "✓ Parameter updated"
else
    aws ssm put-parameter \
        --name "/responsable-recruitment-ai/DATABASE_URL" \
        --value "$DATABASE_URL" \
        --type "SecureString" \
        --description "Database connection URL for ResponsAble application" \
        --region "$AWS_REGION" >/dev/null
    echo "✓ Parameter created"
fi

# Generate SESSION_SECRET
echo ""
echo "Generating SESSION_SECRET..."
SESSION_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Create SESSION_SECRET parameter
echo "Creating SSM parameter: /responsable-recruitment-ai/SESSION_SECRET"
if aws ssm get-parameter --name "/responsable-recruitment-ai/SESSION_SECRET" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "⚠  Parameter already exists, updating..."
    aws ssm put-parameter \
        --name "/responsable-recruitment-ai/SESSION_SECRET" \
        --value "$SESSION_SECRET" \
        --type "SecureString" \
        --overwrite \
        --region "$AWS_REGION" >/dev/null
    echo "✓ Parameter updated"
else
    aws ssm put-parameter \
        --name "/responsable-recruitment-ai/SESSION_SECRET" \
        --value "$SESSION_SECRET" \
        --type "SecureString" \
        --description "Session secret for ResponsAble application" \
        --region "$AWS_REGION" >/dev/null
    echo "✓ Parameter created"
fi

echo ""
echo "=========================================="
echo "SSM Parameters Created Successfully!"
echo "=========================================="
echo "Parameters created:"
echo "  - /responsable-recruitment-ai/DATABASE_URL"
echo "  - /responsable-recruitment-ai/SESSION_SECRET"
echo ""
echo "Next steps:"
echo "1. Initialize database schema"
echo "2. Update ECS task definition to use new parameters"
