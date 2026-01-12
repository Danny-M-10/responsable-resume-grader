#!/bin/bash
# Script to manually initialize database tables in production
# Can be run as an ECS task or manually

set -e

echo "=========================================="
echo "Database Table Initialization"
echo "=========================================="

# Get DATABASE_URL from SSM Parameter Store (same as ECS task)
AWS_REGION="us-east-2"
DATABASE_URL=$(aws ssm get-parameter --name "/recruiting-candidate-ranker/DATABASE_URL" --region $AWS_REGION --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo "")

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not found in SSM Parameter Store"
    echo "Please ensure the parameter exists at: /recruiting-candidate-ranker/DATABASE_URL"
    exit 1
fi

echo "✓ DATABASE_URL retrieved from SSM"
echo ""

# Export DATABASE_URL for Python script
export DATABASE_URL

# Run initialization script
echo "Running database initialization..."
python3 << 'PYTHON_SCRIPT'
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.init_db_async import init_db_async

async def main():
    try:
        print("Initializing database tables...")
        await init_db_async()
        print("✓ Database tables initialized successfully!")
        return 0
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Database initialization complete!"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "✗ Database initialization failed!"
    echo "=========================================="
    exit 1
fi
