#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${ECR_REGISTRY:?ECR_REGISTRY is required}"
: "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

install -d -m 0755 /opt/cloudops-ai-bookstore
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

docker compose \
  --env-file /opt/cloudops-ai-bookstore/deploy.env \
  -f /opt/cloudops-ai-bookstore/docker-compose.aws.yml \
  pull

docker compose \
  --env-file /opt/cloudops-ai-bookstore/deploy.env \
  -f /opt/cloudops-ai-bookstore/docker-compose.aws.yml \
  up -d --remove-orphans

curl --fail --retry 12 --retry-delay 5 http://127.0.0.1/health

