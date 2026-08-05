#!/usr/bin/env bash
set -euo pipefail

# deploy/deploy.sh
# Simple helper to pull new images and restart docker-compose on a remote host.
# Usage: ./deploy.sh <remote-host> <remote-user> <compose-path> <image-tag>

REMOTE_HOST=${1:-}
REMOTE_USER=${2:-}
COMPOSE_PATH=${3:-/opt/sentineliq/docker-compose.yml}
IMAGE_TAG=${4:-latest}

if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
  echo "Usage: $0 <remote-host> <remote-user> [compose-path] [image-tag]"
  exit 2
fi

echo "Deploying images with tag=$IMAGE_TAG to $REMOTE_USER@$REMOTE_HOST"

ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} <<EOF
  set -euo pipefail
  echo "Pulling images"
  docker pull ghcr.io/${USER}/sentineliq-api:${IMAGE_TAG} || true
  docker pull ghcr.io/${USER}/sentineliq-frontend:${IMAGE_TAG} || true
  echo "Updating compose and restarting"
  docker-compose -f ${COMPOSE_PATH} pull || true
  docker-compose -f ${COMPOSE_PATH} up -d --remove-orphans
  echo "Deployed"
EOF

echo "Done"
