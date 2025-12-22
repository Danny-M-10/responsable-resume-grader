#!/bin/bash
# CloudWatch Observability Setup for Recruiting Candidate Ranker
# Sets up log groups, alarms, and monitoring for ECS and RDS

set -e

REGION="us-east-2"
CLUSTER_NAME="recruiting-candidate-ranker"
SERVICE_NAME="recruiting-candidate-ranker"
DB_IDENTIFIER="recruiting-candidate-ranker-db"
SNS_TOPIC_NAME="recruiting-candidate-ranker-alerts"

echo "=========================================="
echo "Setting up CloudWatch Observability"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create/Update CloudWatch Log Groups
echo -e "${YELLOW}Step 1: Setting up CloudWatch Log Groups${NC}"
LOG_GROUP="/ecs/${SERVICE_NAME}"

if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --region "$REGION" --query "logGroups[?logGroupName=='$LOG_GROUP']" --output text | grep -q "$LOG_GROUP"; then
    echo "  ✓ Log group $LOG_GROUP already exists"
    aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 30 --region "$REGION"
    echo "  ✓ Updated retention to 30 days"
else
    aws logs create-log-group --log-group-name "$LOG_GROUP" --region "$REGION"
    aws logs put-retention-policy --log-group-name "$LOG_GROUP" --retention-in-days 30 --region "$REGION"
    echo "  ✓ Created log group $LOG_GROUP with 30-day retention"
fi

# Step 2: Create SNS Topic for Alerts (optional but recommended)
echo ""
echo -e "${YELLOW}Step 2: Setting up SNS Topic for Alerts${NC}"
SNS_TOPIC_ARN=$(aws sns list-topics --region "$REGION" --query "Topics[?contains(TopicArn, '$SNS_TOPIC_NAME')].TopicArn" --output text 2>/dev/null || echo "")

if [ -z "$SNS_TOPIC_ARN" ]; then
    SNS_TOPIC_ARN=$(aws sns create-topic --name "$SNS_TOPIC_NAME" --region "$REGION" --query 'TopicArn' --output text 2>/dev/null || echo "")
    if [ -n "$SNS_TOPIC_ARN" ]; then
        echo "  ✓ Created SNS topic: $SNS_TOPIC_NAME"
        echo "  ⚠  Please subscribe your email to: $SNS_TOPIC_ARN"
    else
        echo "  ⚠  Could not create SNS topic (permissions required). Alarms will be created without email notifications."
        echo "     You can view alarms in CloudWatch Console and set up SNS later if needed."
    fi
else
    echo "  ✓ SNS topic already exists: $SNS_TOPIC_ARN"
fi

# Step 3: Create ECS Alarms
echo ""
echo -e "${YELLOW}Step 3: Creating ECS CloudWatch Alarms${NC}"

# ECS CPU Utilization Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${SERVICE_NAME}-ecs-cpu-high \
    --alarm-description \"Alert when ECS service CPU utilization exceeds 80%\" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=$SERVICE_NAME Name=ClusterName,Value=$CLUSTER_NAME \
    --region $REGION \
    --treat-missing-data breaching"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ CPU utilization alarm configured" || echo "  ⚠  Alarm ${SERVICE_NAME}-ecs-cpu-high already exists or failed"

# ECS Memory Utilization Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${SERVICE_NAME}-ecs-memory-high \
    --alarm-description \"Alert when ECS service memory utilization exceeds 85%\" \
    --metric-name MemoryUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 85 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=ServiceName,Value=$SERVICE_NAME Name=ClusterName,Value=$CLUSTER_NAME \
    --region $REGION \
    --treat-missing-data breaching"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ Memory utilization alarm configured" || echo "  ⚠  Alarm ${SERVICE_NAME}-ecs-memory-high already exists or failed"

# ECS Running Task Count Alarm (too few tasks)
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${SERVICE_NAME}-ecs-tasks-low \
    --alarm-description \"Alert when ECS service has fewer than desired tasks running\" \
    --metric-name RunningTaskCount \
    --namespace AWS/ECS \
    --statistic Average \
    --period 60 \
    --evaluation-periods 2 \
    --threshold 1 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=ServiceName,Value=$SERVICE_NAME Name=ClusterName,Value=$CLUSTER_NAME \
    --region $REGION \
    --treat-missing-data breaching"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ Running task count alarm configured" || echo "  ⚠  Alarm ${SERVICE_NAME}-ecs-tasks-low already exists or failed"

# Step 4: Create RDS Alarms
echo ""
echo -e "${YELLOW}Step 4: Creating RDS CloudWatch Alarms${NC}"

# RDS CPU Utilization Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${DB_IDENTIFIER}-cpu-high \
    --alarm-description \"Alert when RDS CPU utilization exceeds 80%\" \
    --metric-name CPUUtilization \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value=$DB_IDENTIFIER \
    --region $REGION \
    --treat-missing-data breaching"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ RDS CPU utilization alarm configured" || echo "  ⚠  Alarm ${DB_IDENTIFIER}-cpu-high already exists or failed"

# RDS Database Connections Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${DB_IDENTIFIER}-connections-high \
    --alarm-description \"Alert when RDS database connections exceed 80% of max\" \
    --metric-name DatabaseConnections \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 40 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value=$DB_IDENTIFIER \
    --region $REGION \
    --treat-missing-data notBreaching"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ RDS connections alarm configured" || echo "  ⚠  Alarm ${DB_IDENTIFIER}-connections-high already exists or failed"

# RDS Free Storage Space Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${DB_IDENTIFIER}-storage-low \
    --alarm-description \"Alert when RDS free storage space is below 2GB\" \
    --metric-name FreeStorageSpace \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 2147483648 \
    --comparison-operator LessThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value=$DB_IDENTIFIER \
    --region $REGION \
    --treat-missing-data notBreaching \
    --unit Bytes"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ RDS storage space alarm configured" || echo "  ⚠  Alarm ${DB_IDENTIFIER}-storage-low already exists or failed"

# RDS Read Latency Alarm
ALARM_CMD="aws cloudwatch put-metric-alarm \
    --alarm-name ${DB_IDENTIFIER}-read-latency-high \
    --alarm-description \"Alert when RDS read latency exceeds 1 second\" \
    --metric-name ReadLatency \
    --namespace AWS/RDS \
    --statistic Average \
    --period 300 \
    --evaluation-periods 2 \
    --threshold 1.0 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=DBInstanceIdentifier,Value=$DB_IDENTIFIER \
    --region $REGION \
    --treat-missing-data notBreaching \
    --unit Seconds"

if [ -n "$SNS_TOPIC_ARN" ]; then
    ALARM_CMD="$ALARM_CMD --alarm-actions $SNS_TOPIC_ARN"
fi

eval $ALARM_CMD > /dev/null 2>&1 && echo "  ✓ RDS read latency alarm configured" || echo "  ⚠  Alarm ${DB_IDENTIFIER}-read-latency-high already exists or failed"

# Step 5: Summary
echo ""
echo -e "${GREEN}=========================================="
echo "Observability Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Created/Updated:"
echo "  ✓ CloudWatch Log Group: $LOG_GROUP (30-day retention)"
echo "  ✓ SNS Topic: $SNS_TOPIC_NAME"
echo "  ✓ ECS Alarms:"
echo "    - CPU utilization > 80%"
echo "    - Memory utilization > 85%"
echo "    - Running tasks < 1"
echo "  ✓ RDS Alarms:"
echo "    - CPU utilization > 80%"
echo "    - Database connections > 40"
echo "    - Free storage < 2GB"
echo "    - Read latency > 1s"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Subscribe to SNS topic for email alerts:"
echo "   aws sns subscribe --topic-arn $SNS_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com --region $REGION"
echo ""
echo "2. View alarms in CloudWatch Console:"
echo "   https://console.aws.amazon.com/cloudwatch/home?region=$REGION#alarmsV2:"
echo ""
echo "3. View logs in CloudWatch Logs:"
echo "   https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups/log-group/$LOG_GROUP"
echo ""

