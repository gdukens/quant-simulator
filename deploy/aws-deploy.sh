#!/bin/bash
# AWS Deployment Script for QuantLib Pro
# Deploys to AWS ECS with Fargate

set -e

echo " QuantLib Pro - AWS Deployment Script"
echo "========================================"

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-quantlib-pro-cluster}"
SERVICE_NAME="${SERVICE_NAME:-quantlib-pro-service}"
TASK_FAMILY="${TASK_FAMILY:-quantlib-pro-task}"
ECR_REPO="${ECR_REPO:-quantlib-pro}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo " AWS CLI not found. Please install it first."
    exit 1
fi

echo " Configuration:"
echo "  Region: $AWS_REGION"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo " Step 1: Setting up ECR repository..."
aws ecr describe-repositories \
    --repository-names $ECR_REPO \
    --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository \
    --repository-name $ECR_REPO \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true

ECR_URI=$(aws ecr describe-repositories \
    --repository-names $ECR_REPO \
    --region $AWS_REGION \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo " ECR Repository: $ECR_URI"

# Step 2: Build and push Docker image
echo ""
echo " Step 2: Building and pushing Docker image..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_URI

docker build -t $ECR_REPO:$IMAGE_TAG .
docker tag $ECR_REPO:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:$IMAGE_TAG

echo " Image pushed to ECR"

# Step 3: Create ECS Cluster
echo ""
echo "  Step 3: Creating ECS Cluster..."
aws ecs describe-clusters \
    --clusters $CLUSTER_NAME \
    --region $AWS_REGION 2>/dev/null || \
aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --region $AWS_REGION

echo " Cluster ready"

# Step 4: Create Task Execution Role
echo ""
echo " Step 4: Setting up IAM roles..."
ROLE_NAME="ecsTaskExecutionRole"

aws iam get-role --role-name $ROLE_NAME 2>/dev/null || \
aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

echo " IAM roles configured"

# Step 5: Register Task Definition
echo ""
echo " Step 5: Registering task definition..."

cat > task-definition.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "$ROLE_ARN",
  "taskRoleArn": "$ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "quantlib-app",
      "image": "$ECR_URI:$IMAGE_TAG",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "APP_ENV", "value": "production"},
        {"name": "STREAMLIT_SERVER_PORT", "value": "8501"},
        {"name": "STREAMLIT_SERVER_ADDRESS", "value": "0.0.0.0"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$TASK_FAMILY",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group \
    --log-group-name "/ecs/$TASK_FAMILY" \
    --region $AWS_REGION 2>/dev/null || true

aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region $AWS_REGION

echo " Task definition registered"

# Step 6: Create or Update Service
echo ""
echo " Step 6: Creating/Updating ECS service..."

# Get default VPC and subnets
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region $AWS_REGION)

SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].SubnetId' \
    --output text \
    --region $AWS_REGION | tr '\t' ',')

# Create security group
SG_NAME="quantlib-pro-sg"
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $AWS_REGION 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SG_NAME \
        --description "Security group for QuantLib Pro" \
        --vpc-id $VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' \
        --output text)
    
    # Allow inbound traffic on port 8501
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION
fi

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].status' \
    --output text 2>/dev/null)

if [ "$SERVICE_EXISTS" == "ACTIVE" ]; then
    echo "Updating existing service..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --force-new-deployment \
        --region $AWS_REGION
else
    echo "Creating new service..."
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 1 \
        --launch-type FARGATE \
        --platform-version LATEST \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
fi

echo " Service deployed"

# Step 7: Wait for service to stabilize
echo ""
echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

# Get service endpoint
TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

ENI_ID=$(aws ecs describe-tasks \
    --cluster $CLUSTER_NAME \
    --tasks $TASK_ARN \
    --region $AWS_REGION \
    --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
    --output text)

PUBLIC_IP=$(aws ec2 describe-network-interfaces \
    --network-interface-ids $ENI_ID \
    --region $AWS_REGION \
    --query 'NetworkInterfaces[0].Association.PublicIp' \
    --output text)

echo ""
echo " Deployment Complete!"
echo "========================================"
echo " Application URL: http://$PUBLIC_IP:8501"
echo ""
echo " Monitoring:"
echo "  CloudWatch Logs: /ecs/$TASK_FAMILY"
echo "  ECS Console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services/$SERVICE_NAME"
echo ""
echo " Useful Commands:"
echo "  View logs: aws logs tail /ecs/$TASK_FAMILY --follow --region $AWS_REGION"
echo "  Scale service: aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 2 --region $AWS_REGION"
echo "  Delete service: aws ecs delete-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force --region $AWS_REGION"
echo ""

# Cleanup
rm -f task-definition.json
