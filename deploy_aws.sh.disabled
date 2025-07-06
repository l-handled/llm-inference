#!/bin/bash

# AWS RAG Pipeline Deployment Script
set -e

echo "🚀 Starting AWS deployment..."

# Configuration
AWS_REGION=${AWS_REGION:-eu-central-1}
ECR_REPOSITORY="rag-pipeline"
CLUSTER_NAME="rag-pipeline-cluster"
SERVICE_NAME="rag-pipeline-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

print_status "Using AWS Account: ${AWS_ACCOUNT_ID}"
print_status "Using ECR Registry: ${ECR_REGISTRY}"

# Create ECR repository if it doesn't exist
print_status "Checking ECR repository..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} &> /dev/null; then
    print_status "Creating ECR repository..."
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}
fi

# Login to ECR
print_status "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Build and tag Docker image
print_status "Building Docker image..."
cd docker
docker build -t ${ECR_REPOSITORY}:latest -f Dockerfile ..

# Tag for ECR
docker tag ${ECR_REPOSITORY}:latest ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

# Push to ECR
print_status "Pushing image to ECR..."
docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest

# Check if ECS cluster exists
print_status "Checking ECS cluster..."
if ! aws ecs describe-clusters --clusters ${CLUSTER_NAME} --region ${AWS_REGION} --query 'clusters[0].status' --output text | grep -q ACTIVE; then
    print_warning "ECS cluster ${CLUSTER_NAME} does not exist or is not active."
    print_status "You may need to create the cluster and service manually, or use AWS CDK/CloudFormation."
    exit 1
fi

# Update ECS service
print_status "Updating ECS service..."
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --force-new-deployment \
    --region ${AWS_REGION}

# Wait for deployment to complete
print_status "Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${AWS_REGION}

print_status "✅ Deployment completed successfully!"

# Get service details
print_status "Getting service details..."
SERVICE_DETAILS=$(aws ecs describe-services \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${AWS_REGION} \
    --query 'services[0]')

# Extract load balancer URL if available
LB_URL=$(echo $SERVICE_DETAILS | jq -r '.loadBalancers[0].loadBalancerName // empty')
if [ ! -z "$LB_URL" ]; then
    print_status "Load Balancer: ${LB_URL}"
fi

print_status "🎉 RAG Pipeline is now deployed and running!" 