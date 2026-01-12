# Analysis Migration Instructions

This document explains how to migrate analysis documents from the old Streamlit schema to the new FastAPI schema.

## Overview

The migration script (`migrate_analyses.py`) will:
1. Read analyses from the old schema (`reports`, `job_descriptions`, `candidate_scores` tables)
2. Convert them to the new schema (`jobs`, `analyses` tables)
3. Preserve all data including PDF paths and candidate scores

## Prerequisites

- Access to the production database (RDS PostgreSQL)
- The database is only accessible from within the AWS VPC
- You need to run the migration from within AWS (ECS task, EC2 instance, or via bastion host)

## Method 1: Run as ECS One-Off Task (Recommended)

1. Build and push the Docker image (if not already done):
   ```bash
   bash deploy_to_aws_fastapi.sh
   ```

2. Run the migration as a one-off ECS task:
   ```bash
   aws ecs run-task \
     --cluster recruiting-candidate-ranker-cluster \
     --task-definition internal-recruiting-candidate-ranker \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
     --overrides '{
       "containerOverrides": [{
         "name": "app",
         "command": ["python3", "migrate_analyses.py"]
       }]
     }'
   ```

3. Check the CloudWatch logs for the task to see the migration progress:
   ```bash
   aws logs tail /ecs/recruiting-candidate-ranker --follow --region us-east-2
   ```

## Method 2: Run via AWS Systems Manager (SSM) Session

If you have an EC2 instance or ECS task with SSM enabled:

1. Find the task/instance ID:
   ```bash
   aws ecs list-tasks --cluster recruiting-candidate-ranker-cluster --region us-east-2
   ```

2. Start an SSM session:
   ```bash
   aws ecs execute-command \
     --cluster recruiting-candidate-ranker-cluster \
     --task <TASK_ID> \
     --container app \
     --command "/bin/bash" \
     --interactive
   ```

3. Once inside the container, run:
   ```bash
   python3 migrate_analyses.py
   ```

## Method 3: Run Locally with VPN/Bastion (If Available)

If you have VPN access or a bastion host configured:

1. Connect to the VPN or bastion host
2. Set up port forwarding or SSH tunnel to the database
3. Set the DATABASE_URL environment variable
4. Run the migration script:
   ```bash
   export DATABASE_URL=$(aws ssm get-parameter \
     --name "/recruiting-candidate-ranker/DATABASE_URL" \
     --region us-east-2 \
     --with-decryption \
     --query 'Parameter.Value' \
     --output text)
   python3 migrate_analyses.py
   ```

## What Gets Migrated

For each user (`danny@crossroadcoach.com` and `shannon@crossroadcoach.com`):

- **Job Descriptions**: Converted from `job_descriptions` table to `jobs` table
- **Analyses**: Created in `analyses` table with:
  - Status: "completed"
  - Job ID: Links to the new `jobs` entry
  - Results: Contains all candidate scores and PDF path
  - Config: Default configuration (general template)
- **Candidate Scores**: Preserved in the `results` JSON field
- **PDF Paths**: Preserved and linked to the analysis

## Verification

After migration, you can verify by:

1. Checking the History page in the application for both users
2. Querying the database directly:
   ```sql
   SELECT COUNT(*) FROM analyses WHERE user_id IN (
     SELECT id FROM users WHERE email IN ('danny@crossroadcoach.com', 'shannon@crossroadcoach.com')
   );
   ```

## Rollback

If you need to rollback, the old data in `reports`, `job_descriptions`, and `candidate_scores` tables is not deleted. The migration script checks for existing analyses to avoid duplicates, so you can safely re-run it if needed.

## Notes

- The migration script checks for existing analyses to avoid duplicates (based on `created_at` timestamp)
- PDF files are not moved; only database references are updated
- The script will log detailed progress and any errors encountered
