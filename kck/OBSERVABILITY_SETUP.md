# CloudWatch Observability Setup

This document describes the CloudWatch monitoring and alerting setup for the Recruiting Candidate Ranker application.

## Quick Setup

Run the setup script:

```bash
./setup_observability.sh
```

This will create:
- CloudWatch log groups with 30-day retention
- SNS topic for alerts
- ECS service alarms (CPU, memory, task count)
- RDS database alarms (CPU, connections, storage, latency)

## What Gets Monitored

### ECS Service (`recruiting-candidate-ranker`)

**Alarms:**
1. **CPU Utilization > 80%**
   - Triggers when average CPU exceeds 80% for 10 minutes (2 periods × 5 min)
   - Action: Sends alert to SNS topic

2. **Memory Utilization > 85%**
   - Triggers when average memory exceeds 85% for 10 minutes
   - Action: Sends alert to SNS topic

3. **Running Tasks < 1**
   - Triggers when fewer than 1 task is running for 2 minutes
   - Action: Sends alert to SNS topic

### RDS Database (`recruiting-candidate-ranker-db`)

**Alarms:**
1. **CPU Utilization > 80%**
   - Triggers when average CPU exceeds 80% for 10 minutes
   - Action: SNS alert

2. **Database Connections > 40**
   - Triggers when average connections exceed 40 for 10 minutes
   - Action: SNS alert

3. **Free Storage < 2GB**
   - Triggers when free storage drops below 2GB
   - Action: SNS alert

4. **Read Latency > 1s**
   - Triggers when average read latency exceeds 1 second for 10 minutes
   - Action: SNS alert

## CloudWatch Logs

**Log Group:** `/ecs/recruiting-candidate-ranker`
- **Retention:** 30 days
- **Contains:** All application logs from ECS tasks

View logs:
```bash
aws logs tail /ecs/recruiting-candidate-ranker --follow --region us-east-2
```

Or in AWS Console:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#logsV2:log-groups/log-group/%2Fecs%2Frecruiting-candidate-ranker

## SNS Topic

**Topic Name:** `recruiting-candidate-ranker-alerts`

Subscribe your email to receive alerts:
```bash
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region us-east-2
```

Check the topic ARN:
```bash
aws sns list-topics --region us-east-2 --query "Topics[?contains(TopicArn, 'recruiting-candidate-ranker-alerts')]"
```

## Viewing Alarms

**AWS Console:**
https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#alarmsV2:

**CLI:**
```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix recruiting-candidate-ranker \
  --region us-east-2 \
  --query 'MetricAlarms[*].{name:AlarmName,state:StateValue,threshold:Threshold}' \
  --output table
```

## Custom Metrics (Optional)

You can add custom application metrics using CloudWatch PutMetricData API:

```python
import boto3

cloudwatch = boto3.client('cloudwatch', region_name='us-east-2')

cloudwatch.put_metric_data(
    Namespace='RecruitingCandidateRanker',
    MetricData=[
        {
            'MetricName': 'CandidatesProcessed',
            'Value': 1,
            'Unit': 'Count'
        }
    ]
)
```

## Cost Considerations

- **CloudWatch Logs:** First 5GB/month free, then $0.50/GB
- **CloudWatch Metrics:** First 10 custom metrics free, then $0.30/metric/month
- **CloudWatch Alarms:** First 10 alarms free, then $0.10/alarm/month
- **SNS:** First 1M requests/month free, then $0.50/1M requests

With the current setup (standard AWS metrics, 1 log group, ~8 alarms), you should stay well within free tier limits for typical usage.

## Troubleshooting

### Alarms not triggering
1. Check alarm state: `aws cloudwatch describe-alarms --alarm-name <ALARM_NAME>`
2. Verify metric data exists: Check CloudWatch Metrics console
3. Ensure SNS topic has subscribers

### Logs not appearing
1. Verify ECS task definition has log configuration
2. Check task execution role has `logs:CreateLogStream` and `logs:PutLogEvents` permissions
3. Verify log group exists: `aws logs describe-log-groups --log-group-name-prefix /ecs/`

### High costs
- Reduce log retention period (currently 30 days)
- Delete unused alarms
- Consider using log sampling for verbose logs

