# Deployment Directory

This directory contains all files and scripts for deploying the RAG pipeline locally and to the cloud.

- `run_local.sh`: Script to run the full stack locally using Docker Compose.
- `deploy_aws.sh.disabled`: Script to build, tag, and push the Docker image to AWS ECR, and print ECS deployment hints. (Currently disabled)
- `cloud-config.yml.disabled`: Example AWS ECS/EC2 deployment config. (Currently disabled)
- `secrets.template`: Template for environment variables and secrets.

## Usage

**Note: Cloud deployment features are currently disabled.**

- Use `cloud-config.yml` as a template for ECS/EC2 deployment (when re-enabled).
- Store secrets in AWS Secrets Manager or as environment variables.

See the main README for a full deployment guide. 