# Deployment Status

## Deployment Date
2026-01-12

## Changes Deployed
1. **History Page 404 Fix** - Fixed route ordering in `backend/api/analysis.py`
   - Moved `list_analyses` route (empty string) before `get_analysis` route (path parameter)
   - This ensures `/api/analysis` matches the list route correctly

## Deployment Process
- ✅ Docker image built successfully
- ✅ Image pushed to ECR (tag: e0701cb)
- ✅ Task definition registered (revision: 58)
- ✅ ECS service updated
- ⚠️ Service is starting up (0 running tasks initially)

## Image Details
- **Image**: `774305585062.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker:e0701cb`
- **Tag**: e0701cb
- **Task Definition**: internal-recruiting-candidate-ranker:58

## Service Status
The service was updated and is starting up. It may take a few minutes for tasks to become healthy.

## Next Steps
1. Wait for service to stabilize (tasks to become running/healthy)
2. Verify History page loads correctly (should no longer return 404)
3. Test analysis workflow to check if crashes are resolved
4. Check CloudWatch logs for any errors

## Verification Commands
```bash
# Check service status
aws ecs describe-services --cluster internal_recruiting_candidate_ranker --services internal_recruiting_candidate_ranker --region us-east-2

# Check logs
aws logs tail /ecs/internal_recruiting_candidate_ranker --since 10m --region us-east-2

# Test Health endpoint
curl https://recruiting.crossroadcoach.com/health
```
