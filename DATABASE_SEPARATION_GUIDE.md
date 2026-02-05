# Database Separation Guide for ResponsAble Application

This guide documents the setup of a dedicated database for the ResponsAble application, ensuring complete separation from the `internal_recruiting_candidate_ranker` application.

## Overview

The ResponsAble application now has its own dedicated database infrastructure:

- **RDS Database**: `responsable-recruitment-ai-db`
- **Database Name**: `responsable_appdb`
- **Master Username**: `responsable_admin`
- **SSM Parameters**: `/responsable-recruitment-ai/DATABASE_URL` and `/responsable-recruitment-ai/SESSION_SECRET`

## Resources Created

### 1. RDS Database Instance

- **Instance Identifier**: `responsable-recruitment-ai-db`
- **Engine**: PostgreSQL 14.19
- **Instance Class**: `db.t3.micro`
- **Storage**: 20GB gp3 (encrypted)
- **Backup Retention**: 7 days
- **Security Group**: `sg-042c0882d88facf11` (allows ECS access)
- **Subnet Group**: `recruiting-candidate-ranker-db-subnet-group`
- **Endpoint**: `responsable-recruitment-ai-db.cneomuesmsp1.us-east-2.rds.amazonaws.com`

### 2. SSM Parameters

#### `/responsable-recruitment-ai/DATABASE_URL`
- Type: SecureString
- Contains: Full PostgreSQL connection string
- Format: `postgresql://responsable_admin:password@host:5432/responsable_appdb`

#### `/responsable-recruitment-ai/SESSION_SECRET`
- Type: SecureString
- Contains: Random session secret for ResponsAble application

#### `/responsable-recruitment-ai/DB_MASTER_PASSWORD`
- Type: SecureString
- Contains: Master password for RDS database (backup)

### 3. CloudWatch Log Group

- **Log Group**: `/ecs/responsable-recruitment-ai`
- Created automatically by ECS task definition

## Complete Separation Checklist

### ✅ Separate Resources

- [x] **S3 Bucket**: `responsable-recruitment-ai-uploads-us-east-2-774305585062`
- [x] **RDS Database**: `responsable-recruitment-ai-db`
- [x] **Database Name**: `responsable_appdb`
- [x] **SSM Parameters**: `/responsable-recruitment-ai/*`
- [x] **ECS Cluster**: `responsAble_recruitment_ai_app`
- [x] **ECS Service**: `responsAble_recruitment_ai_app`
- [x] **Target Group**: `responsable-recruitment-tg-8000`
- [x] **CloudWatch Log Group**: `/ecs/responsable-recruitment-ai`

### 🔧 Shared Resources (by design)

- **VPC**: `vpc-0520ba7971d490ddf` (shared network)
- **Subnet Group**: `recruiting-candidate-ranker-db-subnet-group` (shared subnets)
- **Security Group**: `sg-042c0882d88facf11` (allows ECS access, both apps use same security group)
- **Task Role**: `recruiting-candidate-ranker-task` (has permissions for both apps' SSM parameters)

## Database Initialization

### Option 1: Initialize from ECS Task (Recommended)

The database can be initialized from within the ECS task since it has network access to RDS:

```bash
# Run a one-off ECS task to initialize the database
aws ecs run-task \
  --cluster responsAble_recruitment_ai_app \
  --task-definition responsable-recruitment-ai-app \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-08bf8df99bef147da,subnet-05ff66619e9aa10d5],securityGroups=[sg-06040dc838d6fa2ce],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"app","command":["python3","-m","backend.database.init_db_async"]}]}' \
  --region us-east-2
```

### Option 2: Initialize from Local Machine (If VPC Access Available)

If you have VPC access (VPN, bastion host, etc.):

```bash
# Get DATABASE_URL from SSM
export DATABASE_URL=$(aws ssm get-parameter \
  --name "/responsable-recruitment-ai/DATABASE_URL" \
  --region us-east-2 \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text)

# Run initialization script
python3 scripts/init_database_standalone.py
```

### Option 3: Use Database Client from ECS Container

If the application is already running, you can connect to a running container:

```bash
# Get task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster responsAble_recruitment_ai_app \
  --service-name responsable-recruitment-ai-app \
  --region us-east-2 \
  --query 'taskArns[0]' \
  --output text | cut -d'/' -f3)

# Execute command in running container
aws ecs execute-command \
  --cluster responsAble_recruitment_ai_app \
  --task $TASK_ID \
  --container app \
  --command "python3 -m backend.database.init_db_async" \
  --interactive \
  --region us-east-2
```

## Deployment

The deployment script (`deploy_to_aws_responsable.sh`) has been updated to use ResponsAble-specific resources:

- **DATABASE_URL**: `/responsable-recruitment-ai/DATABASE_URL`
- **SESSION_SECRET**: `/responsable-recruitment-ai/SESSION_SECRET`
- **Storage Bucket**: `responsable-recruitment-ai-uploads-us-east-2-774305585062`
- **Log Group**: `/ecs/responsable-recruitment-ai`

## Verification

### Verify Database Separation

```bash
# Check RDS instance
aws rds describe-db-instances \
  --db-instance-identifier responsable-recruitment-ai-db \
  --region us-east-2 \
  --query 'DBInstances[0].{Identifier:DBInstanceIdentifier,Endpoint:Endpoint.Address,Status:DBInstanceStatus}'

# Check SSM parameters
aws ssm get-parameters \
  --names "/responsable-recruitment-ai/DATABASE_URL" "/responsable-recruitment-ai/SESSION_SECRET" \
  --region us-east-2 \
  --query 'Parameters[*].Name'
```

### Verify ECS Task Definition

```bash
# Check task definition secrets
aws ecs describe-task-definition \
  --task-definition responsable-recruitment-ai-app \
  --region us-east-2 \
  --query 'taskDefinition.containerDefinitions[0].secrets'
```

### Verify Application Connection

Check application logs to confirm it's connecting to the correct database:

```bash
# View application logs
aws logs tail /ecs/responsable-recruitment-ai --follow --region us-east-2
```

## Security Notes

1. **Database Access**: The database is in a private subnet and only accessible from within the VPC (specifically from ECS tasks)

2. **Password Storage**: Master password is stored in SSM Parameter Store (`/responsable-recruitment-ai/DB_MASTER_PASSWORD`) as a backup

3. **IAM Permissions**: The ECS task role (`recruiting-candidate-ranker-task`) has permissions to read SSM parameters (including ResponsAble parameters)

4. **Network Security**: The RDS security group (`sg-042c0882d88facf11`) allows inbound PostgreSQL (5432) from the ECS security group

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database:

1. Verify security group allows traffic from ECS tasks:
   ```bash
   aws ec2 describe-security-groups \
     --group-ids sg-042c0882d88facf11 \
     --region us-east-2
   ```

2. Check SSM parameter exists and is accessible:
   ```bash
   aws ssm get-parameter \
     --name "/responsable-recruitment-ai/DATABASE_URL" \
     --region us-east-2 \
     --with-decryption
   ```

3. Verify task role has SSM permissions:
   ```bash
   aws iam get-role-policy \
     --role-name recruiting-candidate-ranker-task \
     --policy-name recruiting-candidate-ranker-task-inline \
     --region us-east-2
   ```

### Schema Initialization Issues

If schema initialization fails:

1. Verify database is accessible from ECS tasks (security groups)
2. Check DATABASE_URL is correct and accessible
3. Review application logs for connection errors
4. Try running initialization from a running ECS task

## Maintenance

### Database Backups

Backups are automatically configured with 7-day retention. Manual snapshots can be created:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier responsable-recruitment-ai-db \
  --db-snapshot-identifier responsable-db-snapshot-$(date +%Y%m%d) \
  --region us-east-2
```

### Password Rotation

To rotate the database password:

1. Update password in RDS:
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier responsable-recruitment-ai-db \
     --master-user-password <new-password> \
     --apply-immediately \
     --region us-east-2
   ```

2. Update DATABASE_URL in SSM:
   ```bash
   aws ssm put-parameter \
     --name "/responsable-recruitment-ai/DATABASE_URL" \
     --value "postgresql://responsable_admin:new-password@host:5432/responsable_appdb" \
     --type "SecureString" \
     --overwrite \
     --region us-east-2
   ```

3. Update backup password in SSM:
   ```bash
   aws ssm put-parameter \
     --name "/responsable-recruitment-ai/DB_MASTER_PASSWORD" \
     --value "<new-password>" \
     --type "SecureString" \
     --overwrite \
     --region us-east-2
   ```

4. Restart ECS service to pick up new password:
   ```bash
   aws ecs update-service \
     --cluster responsAble_recruitment_ai_app \
     --service responsable-recruitment-ai-app \
     --force-new-deployment \
     --region us-east-2
   ```

## Scripts

The following scripts were created to manage the database:

- `scripts/create_responsable_database.sh` - Creates RDS database instance
- `scripts/create_responsable_ssm_parameters.sh` - Creates SSM parameters
- `scripts/init_responsable_database.sh` - Initializes database schema (requires VPC access)
- `scripts/init_database_standalone.py` - Standalone Python script for schema initialization

## Summary

The ResponsAble application now has complete separation from the internal application:

- ✅ Dedicated RDS database
- ✅ Separate SSM parameters
- ✅ Isolated data storage
- ✅ Separate CloudWatch logs
- ✅ Independent S3 bucket

Both applications can run simultaneously without interfering with each other's data or resources.
