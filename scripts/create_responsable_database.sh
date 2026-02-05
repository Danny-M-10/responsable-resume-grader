#!/bin/bash

# Script to create dedicated RDS PostgreSQL database for ResponsAble application
# This ensures complete separation from the internal_recruiting_candidate_ranker application

set -e

AWS_REGION="us-east-2"
DB_INSTANCE_IDENTIFIER="responsable-recruitment-ai-db"
DB_NAME="responsable_appdb"
MASTER_USERNAME="responsable_admin"
DB_INSTANCE_CLASS="db.t3.micro"
ENGINE_VERSION="14.19"  # Match existing database version
STORAGE_SIZE=20
STORAGE_TYPE="gp3"
VPC_SECURITY_GROUP_ID="sg-042c0882d88facf11"  # RDS security group (allows ECS access)
DB_SUBNET_GROUP="recruiting-candidate-ranker-db-subnet-group"  # Use existing subnet group
BACKUP_RETENTION=7

echo "=========================================="
echo "Creating ResponsAble RDS Database"
echo "=========================================="
echo "Instance Identifier: $DB_INSTANCE_IDENTIFIER"
echo "Database Name: $DB_NAME"
echo "Master Username: $MASTER_USERNAME"
echo "Instance Class: $DB_INSTANCE_CLASS"
echo "Engine Version: $ENGINE_VERSION"
echo "Region: $AWS_REGION"
echo ""

# Check if database already exists
if aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --region "$AWS_REGION" \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null | grep -q "available\|creating"; then
    echo "⚠  Database $DB_INSTANCE_IDENTIFIER already exists"
    echo "   Skipping creation. Use AWS Console to delete if you want to recreate."
    exit 0
fi

# Generate secure password
echo "Generating secure master password..."
MASTER_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "✓ Password generated (will be stored in SSM)"

# Store password in SSM Parameter Store
SSM_PARAM_NAME="/responsable-recruitment-ai/DB_MASTER_PASSWORD"
echo "Storing password in AWS SSM Parameter Store..."
if aws ssm get-parameter --name "$SSM_PARAM_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "⚠  Parameter already exists, updating..."
    aws ssm put-parameter \
        --name "$SSM_PARAM_NAME" \
        --value "$MASTER_PASSWORD" \
        --type "SecureString" \
        --overwrite \
        --region "$AWS_REGION" >/dev/null
else
    aws ssm put-parameter \
        --name "$SSM_PARAM_NAME" \
        --value "$MASTER_PASSWORD" \
        --type "SecureString" \
        --description "Master password for ResponsAble RDS database" \
        --region "$AWS_REGION" >/dev/null
fi
echo "✓ Password stored in SSM Parameter Store: $SSM_PARAM_NAME"

# Create RDS database instance
echo ""
echo "Creating RDS database instance..."
echo "This may take 10-15 minutes..."

aws rds create-db-instance \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --db-instance-class "$DB_INSTANCE_CLASS" \
    --engine postgres \
    --engine-version "$ENGINE_VERSION" \
    --master-username "$MASTER_USERNAME" \
    --master-user-password "$MASTER_PASSWORD" \
    --db-name "$DB_NAME" \
    --allocated-storage "$STORAGE_SIZE" \
    --storage-type "$STORAGE_TYPE" \
    --vpc-security-group-ids "$VPC_SECURITY_GROUP_ID" \
    --db-subnet-group-name "$DB_SUBNET_GROUP" \
    --backup-retention-period "$BACKUP_RETENTION" \
    --storage-encrypted \
    --no-multi-az \
    --no-publicly-accessible \
    --region "$AWS_REGION" \
    --tags Key=Application,Value=ResponsAble Key=Environment,Value=Production

echo ""
echo "✓ Database creation initiated"
echo ""
echo "Database will be available at:"
echo "  Instance: $DB_INSTANCE_IDENTIFIER"
echo "  Database: $DB_NAME"
echo ""
echo "⚠  IMPORTANT: Master password stored in SSM Parameter Store:"
echo "   Parameter: $SSM_PARAM_NAME"
echo ""
echo "Waiting for database to become available (this may take 10-15 minutes)..."
echo "You can check status with:"
echo "  aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_IDENTIFIER --region $AWS_REGION --query 'DBInstances[0].DBInstanceStatus' --output text"
echo ""

# Wait for database to be available (with timeout)
TIMEOUT=1800  # 30 minutes
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
        --region "$AWS_REGION" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "not-found")
    
    if [ "$STATUS" = "available" ]; then
        echo "✓ Database is now available!"
        break
    elif [ "$STATUS" = "not-found" ]; then
        echo "Database not found yet, waiting..."
    else
        echo "Database status: $STATUS (waiting...)"
    fi
    
    sleep 30
    ELAPSED=$((ELAPSED + 30))
done

if [ "$STATUS" != "available" ]; then
    echo "⚠  Database creation timed out or failed"
    echo "   Check status manually:"
    echo "   aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_IDENTIFIER --region $AWS_REGION"
    exit 1
fi

# Get endpoint
ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_IDENTIFIER" \
    --region "$AWS_REGION" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

echo ""
echo "=========================================="
echo "Database Created Successfully!"
echo "=========================================="
echo "Instance Identifier: $DB_INSTANCE_IDENTIFIER"
echo "Endpoint: $ENDPOINT"
echo "Database Name: $DB_NAME"
echo "Master Username: $MASTER_USERNAME"
echo "Master Password: Stored in Secrets Manager ($SECRET_NAME)"
echo ""
echo "Next steps:"
echo "1. Create SSM parameter for DATABASE_URL"
echo "2. Initialize database schema"
echo "3. Update ECS task definition"
