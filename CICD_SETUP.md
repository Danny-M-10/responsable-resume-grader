# CI/CD Setup Guide

This guide explains how to set up continuous integration and deployment (CI/CD) for the Recruiting Candidate Ranker application using GitHub Actions.

## Overview

The CI/CD pipeline includes:
1. **CI Workflow** (`.github/workflows/ci.yml`): Runs on pull requests and pushes to main
   - Lints Python code
   - Tests imports
   - Validates Dockerfile

2. **Deploy Workflow** (`.github/workflows/deploy-ecs.yml`): Deploys to ECS on main branch pushes or tags
   - Builds Docker image for linux/amd64
   - Pushes to Amazon ECR
   - Updates ECS service with new task definition
   - Waits for service stability

## Prerequisites

1. **GitHub Repository**: Code must be in a GitHub repository
2. **AWS Account**: Access to AWS account with ECS, ECR permissions
3. **IAM Role for GitHub Actions**: OIDC role for GitHub Actions to assume

## Setup Steps

### Step 1: Create IAM Role for GitHub Actions (OIDC)

Create an IAM role that GitHub Actions can assume using OIDC:

```bash
# Create trust policy for GitHub OIDC
cat > github-oidc-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::774305585062:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name GitHubActions-ECS-Deploy-Role \
  --assume-role-policy-document file://github-oidc-trust-policy.json \
  --region us-east-2
```

Replace `YOUR_GITHUB_USERNAME/YOUR_REPO_NAME` with your actual GitHub repository path.

### Step 2: Attach Permissions to IAM Role

Attach policies that allow ECR push and ECS update:

```bash
# Policy for ECR access
cat > ecr-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Policy for ECS access
cat > ecs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "ecs:WaitServicesStable"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::774305585062:role/ecsTaskExecutionRole",
        "arn:aws:iam::774305585062:role/recruiting-candidate-ranker-task"
      ]
    }
  ]
}
EOF

# Attach policies
aws iam put-role-policy \
  --role-name GitHubActions-ECS-Deploy-Role \
  --policy-name ECRAccess \
  --policy-document file://ecr-policy.json \
  --region us-east-2

aws iam put-role-policy \
  --role-name GitHubActions-ECS-Deploy-Role \
  --policy-name ECSAccess \
  --policy-document file://ecs-policy.json \
  --region us-east-2
```

### Step 3: Configure GitHub OIDC Provider (One-time)

If you haven't set up GitHub OIDC provider in AWS:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --region us-east-2
```

Note: The thumbprint may need to be updated. Get the current one:
```bash
openssl s_client -servername token.actions.githubusercontent.com -showcerts -connect token.actions.githubusercontent.com:443 < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -sha1 | cut -d'=' -f2 | tr -d ':'
```

### Step 4: Add GitHub Secret

Add the IAM role ARN as a GitHub secret:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `AWS_ROLE_ARN`
5. Value: `arn:aws:iam::774305585062:role/GitHubActions-ECS-Deploy-Role`
6. Click **Add secret**

### Step 5: Update Workflow File (if needed)

If your repository name or AWS account ID differs, update `.github/workflows/deploy-ecs.yml`:

- Replace `774305585062` with your AWS account ID if different
- Update `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE` if your names differ

## Usage

### Automatic Deployment

**On push to main:**
- CI workflow runs (lint/test)
- Deploy workflow runs automatically
- New Docker image is built and pushed to ECR
- ECS service is updated with new task definition

**On tag push (e.g., `v1.0.0`):**
- Same as push to main
- Useful for versioned releases

### Manual Deployment

You can trigger deployment manually:

1. Go to **Actions** tab in GitHub
2. Select **Deploy to ECS** workflow
3. Click **Run workflow**
4. Choose environment (staging/production)
5. Click **Run workflow**

### Monitoring Deployments

View deployment status:
- GitHub Actions tab shows workflow runs
- ECS Console shows service update events
- CloudWatch Logs show application logs

## Troubleshooting

### "Unable to assume role" error
- Verify `AWS_ROLE_ARN` secret is set correctly
- Check IAM role trust policy includes your repository
- Ensure OIDC provider is configured in AWS

### "Cannot pull container image" error
- Verify ECR repository exists: `aws ecr describe-repositories --repository-names recruiting-candidate-ranker`
- Check image was pushed: `aws ecr describe-images --repository-name recruiting-candidate-ranker`

### "Service update failed" error
- Check ECS service logs in CloudWatch
- Verify task definition is valid: `aws ecs describe-task-definition --task-definition recruiting-candidate-ranker`
- Check service events: `aws ecs describe-services --cluster recruiting-candidate-ranker --services recruiting-candidate-ranker`

### Build fails with "platform not supported"
- The workflow uses `docker buildx` for multi-platform builds
- Ensure GitHub Actions runner supports buildx (Ubuntu runners do)

## Security Best Practices

1. **Use OIDC instead of access keys**: The workflow uses OIDC, which is more secure
2. **Least privilege**: IAM role only has permissions needed for ECR/ECS operations
3. **Secrets management**: Never commit AWS credentials to the repository
4. **Image scanning**: Consider adding ECR image scanning in the workflow
5. **Tag strategy**: Use commit SHA for image tags to ensure traceability

## Advanced: Multi-Environment Deployment

To deploy to staging and production separately:

1. Create separate ECS services: `recruiting-candidate-ranker-staging` and `recruiting-candidate-ranker-prod`
2. Update workflow to use `workflow_dispatch` input to select environment
3. Use different ECR tags or repositories per environment
4. Add environment-specific secrets/configs

Example workflow modification:
```yaml
env:
  ECS_SERVICE: ${{ github.event.inputs.environment == 'staging' && 'recruiting-candidate-ranker-staging' || 'recruiting-candidate-ranker-prod' }}
```

## Cost Considerations

- GitHub Actions: Free tier includes 2,000 minutes/month for private repos
- ECR: First 500MB/month free, then $0.10/GB/month
- ECS: No additional cost for Fargate deployments (pay for compute only)

Typical CI/CD usage should stay within free tiers for small to medium projects.

