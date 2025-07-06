# Deployment Directory

This directory contains all files and scripts for deploying the RAG pipeline locally and to the cloud.

- `run_local.sh`: Script to run the full stack locally using Docker Compose.
- `deploy_aws.sh`: Script to build, tag, and push the Docker image to AWS ECR, and print ECS deployment hints.
- `cloud-config.yml`: Example AWS ECS/EC2 deployment config.
- `secrets.template`: Template for environment variables and secrets.

## Usage

  - Use `cloud-config.yml` as a template for ECS/EC2 deployment.
  - Store secrets in AWS Secrets Manager or as environment variables.

See the main README for a full deployment guide. 