AWS Beta Launch (us-east-2)
===========================

Target: `https://recruiting.crossroadcoach.com`
Runtime: ECS Fargate + ALB + RDS Postgres + S3
Region: us-east-2

Prerequisites
-------------
- AWS CLI v2 configured with permissions for ECS, ECR, RDS, ACM, Route 53, IAM, S3, VPC.
- Domain hosted in Route 53 (crossroadcoach.com) or ability to add DNS records there.
- Docker available locally (for image build/push).
- GitHub repo access (for CI/CD workflow).

Architecture (beta)
-------------------
- ECS Fargate service behind ALB (HTTPS only; HTTP redirected).
- Public subnets for ALB; private subnets for ECS tasks and RDS.
- RDS Postgres (single-AZ for beta); SG allows inbound from ECS tasks only.
- S3 bucket for resumes/reports; default encryption enabled; bucket not public.
- IAM task role granting scoped S3 access.
- Secrets/config from SSM Parameter Store or Secrets Manager (recommended: Secrets Manager for DB URL).
- ACM certificate for `recruiting.crossroadcoach.com` in us-east-2; ALB uses it.

Step-by-Step
------------
1) ECR repository
   - Create repo: `recruiting-candidate-ranker` in us-east-2.
   - Authenticate: `aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <acct>.dkr.ecr.us-east-2.amazonaws.com`
   - Build & push:
     ```
     docker build -t recruiting-candidate-ranker .
     docker tag recruiting-candidate-ranker:latest <acct>.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker:latest
     docker push <acct>.dkr.ecr.us-east-2.amazonaws.com/recruiting-candidate-ranker:latest
     ```

2) VPC + subnets + networking
   - VPC: /16 (e.g., 10.0.0.0/16)
   - Public subnets (2 AZs, e.g., 10.0.1.0/24, 10.0.2.0/24) with IGW route.
   - Private subnets (2 AZs, e.g., 10.0.11.0/24, 10.0.12.0/24) with NAT Gateway route.
   - ALB in public subnets; ECS tasks and RDS in private subnets.

3) Security groups
   - ALB SG: inbound 80/443 from 0.0.0.0/0; outbound 0.0.0.0/0.
   - ECS SG: inbound from ALB SG on app port (8501); outbound 0.0.0.0/0.
   - RDS SG: inbound 5432 from ECS SG; outbound 0.0.0.0/0.

4) RDS Postgres (beta)
   - Engine: Postgres 14+ (e.g., db.t3.micro).
   - Storage: 20GB gp3 (auto-scale optional).
   - Multi-AZ: off (beta), backups on.
   - Place in private subnets; attach RDS SG.
   - Create master user/pass; store as secret.
   - Build `DATABASE_URL` (postgres://user:pass@host:5432/dbname) and store in Secrets Manager or SSM.

5) S3 bucket
   - Name: e.g., `recruiting-candidate-ranker-uploads-us-east-2`.
   - Block public access: on.
   - Default encryption: SSE-S3 (or KMS if desired).
   - Optional: lifecycle to transition/delete after retention period.

6) IAM roles/policies
   - Task execution role: `AmazonECSTaskExecutionRolePolicy`.
   - Task role: custom policy with least-privilege S3 access to the bucket/prefix used for uploads/reports.
   - Allow read of SSM/Secrets Manager parameters for app config.

7) ACM + Route 53
   - Request public cert in us-east-2 for `recruiting.crossroadcoach.com`.
   - Validate via DNS in Route 53.
   - ALB HTTPS listener uses this cert; HTTP listener redirects to HTTPS.
   - Create Route 53 ALIAS A record `recruiting.crossroadcoach.com` → ALB DNS.

8) ECS Fargate service
   - Cluster: e.g., `recruiting-candidate-ranker`.
   - Task definition (see task-def.template.json):
     - CPU/mem: 0.5 vCPU / 1GB (start small).
     - Container port: 8501.
     - Image: ECR image tag (latest or versioned).
     - Env vars: `PORT=8501`, `STORAGE_BUCKET`, `STORAGE_REGION=us-east-2`, `DATABASE_URL`, `SESSION_SECRET`, `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` (if used).
     - Logging: awslogs to /ecs/recruiting-candidate-ranker.
   - Service: desired count 1 (beta); attach to ALB target group (port 8501, health check path `/` with 200 expected).

9) CI/CD (GitHub Actions template: .github/workflows/deploy-ecs.yml)
   - On tag/main: build → push to ECR → update ECS service (staging, then prod).
   - Inject AWS creds via GitHub OIDC or secrets.

10) Observability
   - CloudWatch Logs group per service; retention 14–30 days.
   - CloudWatch Alarms:
     - ALB 5xx > threshold
     - ECS task CPU/mem high
     - RDS free storage / connections high
   - (Optional) X-Ray for tracing later.

Environment Variables (runtime)
------------------------------
- PORT=8501
- DATABASE_URL=postgres://... (from Secrets Manager/SSM)
- STORAGE_BUCKET=<s3-bucket-name>
- STORAGE_REGION=us-east-2
- SESSION_SECRET=<random-string>
- OPENAI_API_KEY / ANTHROPIC_API_KEY (if features enabled)

Task Definition Template
------------------------
See `task-def.template.json` for a ready-to-fill example (staging/prod can differ by names and env sources).

Health Checks
-------------
- ALB target group: HTTP on port 8501, path `/`, matcher 200.
- Deregistration delay: ~30s is fine for beta.

Staging vs Prod
---------------
- Create separate ECS services and, ideally, separate RDS DBs (or at least separate schemas) and S3 prefixes.
- Use different task definitions or env var sets via SSM/Secrets.
- Optionally use a staging subdomain (e.g., `staging.recruiting.crossroadcoach.com`) with its own cert/ALB listener or a distinct ALB.

Manual Smoke Test
-----------------
- After deploy, hit `https://recruiting.crossroadcoach.com` and ensure:
  - Auth gate renders.
  - File upload and processing complete.
  - PDF download works.
  - No 5xx in ALB or ECS logs.

Rollbacks
---------
- ECS: revert task definition revision or image tag.
- RDS: rely on automated backups/snapshots.
- S3: versioning optional for retained artifacts.

