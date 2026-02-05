#!/bin/bash

# Script to initialize ResponsAble database schema
# Creates all required tables in the new dedicated database

set -e

AWS_REGION="us-east-2"

echo "=========================================="
echo "Initializing ResponsAble Database Schema"
echo "=========================================="
echo ""

# Get DATABASE_URL from SSM
echo "Retrieving DATABASE_URL from SSM..."
DATABASE_URL=$(aws ssm get-parameter \
    --name "/responsable-recruitment-ai/DATABASE_URL" \
    --region "$AWS_REGION" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text 2>/dev/null)

if [ -z "$DATABASE_URL" ]; then
    echo "✗ Could not retrieve DATABASE_URL from SSM"
    echo "  Run create_responsable_ssm_parameters.sh first"
    exit 1
fi

echo "✓ DATABASE_URL retrieved"
echo ""

# Export DATABASE_URL for Python script
export DATABASE_URL

# Check if we're in a virtual environment, if not try to activate one
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Initialize database schema using standalone script
echo ""
echo "Initializing database schema..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

python3 "$SCRIPT_DIR/init_database_standalone.py"

if [ $? -ne 0 ]; then
    echo "✗ Database schema initialization failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Database Initialization Complete!"
echo "=========================================="
echo "All required tables have been created."
echo ""
echo "Next steps:"
echo "1. Update ECS task definition to use new DATABASE_URL"
echo "2. Deploy updated application"
echo "3. Verify application connects to new database"
