# Deployment Checklist

Use this checklist to ensure a successful deployment of the Recruiting Candidate Ranker application.

## Pre-Deployment

- [ ] All code changes committed and pushed to repository
- [ ] Tests pass locally (`python -m pytest` or manual testing)
- [ ] Environment variables documented and configured in SSM Parameter Store
- [ ] Database migrations completed (if any)
- [ ] Docker image builds successfully locally
- [ ] Review CloudWatch alarms configuration

## Deployment Steps

### 1. Build and Push Docker Image

**Option A: Manual Build**
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin 774305585062.dkr.ecr.us-east-2.amazonaws.com

# Build for linux/amd64 (required for ECS Fargate)
docker buildx build --platform linux/amd64 -t recruiting-candidate-ranker:latest .

# Tag and push
docker tag recruiting-candidate-ranker:latest \
  774305585062.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker:latest

docker push 774305585062.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker:latest
```

**Option B: CI/CD (Recommended)**
- Push to `main` branch or create a tag (e.g., `v1.0.1`)
- GitHub Actions will automatically build and deploy

### 2. Update ECS Service

**If using CI/CD:** Deployment happens automatically

**If manual:**
```bash
# Update task definition with new image
aws ecs update-service \
  --cluster recruiting-candidate-ranker \
  --service recruiting-candidate-ranker \
  --force-new-deployment \
  --region us-east-2
```

### 3. Monitor Deployment

```bash
# Watch service events
aws ecs describe-services \
  --cluster recruiting-candidate-ranker \
  --services recruiting-candidate-ranker \
  --region us-east-2 \
  --query 'services[0].events[0:5]'

# Watch logs
aws logs tail /ecs/recruiting-candidate-ranker --follow --region us-east-2
```

### 4. Run Smoke Tests

```bash
./smoke_test.sh https://recruiting.crossroadcoach.com us-east-2
```

Or manually verify:
- [ ] Application loads at https://recruiting.crossroadcoach.com
- [ ] Login/registration page appears
- [ ] Can upload a test resume
- [ ] Can process a job description
- [ ] PDF report generates and downloads
- [ ] No errors in CloudWatch logs

## Post-Deployment Verification

- [ ] ECS service shows desired count = running count
- [ ] ALB target health shows all targets healthy
- [ ] CloudWatch alarms are in OK state
- [ ] Application responds within acceptable time (< 2s for initial load)
- [ ] Database connections are stable (check RDS metrics)
- [ ] No 5xx errors in ALB access logs

## Rollback Procedure

If deployment fails:

```bash
# Option 1: Revert to previous task definition
PREVIOUS_REVISION=$(aws ecs describe-task-definition \
  --task-definition recruiting-candidate-ranker \
  --region us-east-2 \
  --query 'taskDefinition.revision' \
  --output text)

aws ecs update-service \
  --cluster recruiting-candidate-ranker \
  --service recruiting-candidate-ranker \
  --task-definition recruiting-candidate-ranker:$((PREVIOUS_REVISION - 1)) \
  --region us-east-2

# Option 2: Use specific image tag
aws ecs update-service \
  --cluster recruiting-candidate-ranker \
  --service recruiting-candidate-ranker \
  --force-new-deployment \
  --region us-east-2
```

Then update task definition to use previous image tag.

## Staging vs Production

### Staging Environment

If you have a separate staging environment:

1. Deploy to staging first
2. Run full smoke tests
3. Test critical user flows
4. Monitor for 24-48 hours
5. If stable, promote to production

### Production Deployment

1. Schedule maintenance window (if needed)
2. Notify stakeholders
3. Deploy during low-traffic period
4. Monitor closely for first hour
5. Have rollback plan ready

## Common Issues and Solutions

### Issue: Service won't start
- Check task definition: `aws ecs describe-task-definition --task-definition recruiting-candidate-ranker`
- Check CloudWatch logs for errors
- Verify environment variables/secrets are accessible
- Check IAM role permissions

### Issue: Health checks failing
- Verify container port matches task definition (8501)
- Check health check command: `curl -f http://localhost:8501/`
- Review application logs for startup errors

### Issue: Database connection errors
- Verify `DATABASE_URL` secret is correct in SSM
- Check RDS security group allows ECS tasks
- Verify RDS instance is running
- Test connection from ECS task: `psql $DATABASE_URL`

### Issue: High memory/CPU usage
- Check CloudWatch metrics
- Review application logs for memory leaks
- Consider increasing task CPU/memory allocation
- Review recent code changes for performance issues

## Monitoring After Deployment

Monitor these metrics for 24-48 hours:

- **ECS**: CPU utilization, memory utilization, running task count
- **RDS**: CPU utilization, database connections, read/write latency
- **ALB**: Request count, 5xx error rate, response time
- **Application**: Error rate, response time, user-reported issues

## Documentation Updates

After successful deployment:

- [ ] Update CHANGELOG.md (if exists)
- [ ] Update deployment notes with version/tag
- [ ] Document any configuration changes
- [ ] Update runbooks if procedures changed

