# Docker Directory

This directory contains Docker-related files for building and orchestrating the RAG pipeline.

- `Dockerfile`: Builds the FastAPI app image with all dependencies.
- `docker-compose.yml`: Orchestrates API, Qdrant, and Prometheus for local development and testing.
- `README.md`: This file.

## Usage

- The Dockerfile is used by both local and cloud builds.
- The docker-compose.yml is used for local development (see `../deployment/run_local.sh`).

See the main README for more details on running and deploying the stack.

# Environment Setup

The `.env` file containing environment variables must be placed in the `docker/` directory. When running `../run_local.sh` from the project root, if `docker/.env` does not exist, it will be created from the project root `.env.template` file. You must fill in your secrets in `docker/.env` before running the pipeline.

## Steps
1. Run `../run_local.sh` from the project root.
2. If `docker/.env` is missing, it will be created from `.env.template` and you will be prompted to fill it in.
3. Edit `docker/.env` with your actual secrets and configuration values.
4. Re-run `../run_local.sh` to start the pipeline. 