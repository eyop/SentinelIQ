#!/usr/bin/env bash
set -euo pipefail

# deploy/deploy.sh
# Simple helper to pull new images and restart docker-compose on a remote host.
# Usage: ./deploy.sh <remote-host> <remote-user> [compose-path] [image-tag] [image-owner]

REMOTE_HOST=${1:-}
REMOTE_USER=${2:-}
COMPOSE_PATH=${3:-/opt/sentineliq/docker-compose.yml}
IMAGE_TAG=${4:-latest}
IMAGE_OWNER=${5:-${GITHUB_REPOSITORY_OWNER:-${USER:-github}}}

if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
  echo "Usage: $0 <remote-host> <remote-user> [compose-path] [image-tag] [image-owner]"
  exit 2
fi

echo "Deploying images with tag=$IMAGE_TAG from ghcr.io/$IMAGE_OWNER to $REMOTE_USER@$REMOTE_HOST"

ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" "IMAGE_TAG='${IMAGE_TAG}' IMAGE_OWNER='${IMAGE_OWNER}' COMPOSE_PATH='${COMPOSE_PATH}' bash -s" <<'EOF'
  set -euo pipefail
  echo "Pulling images"
  docker pull "ghcr.io/${IMAGE_OWNER}/sentineliq-api:${IMAGE_TAG}" || true
  docker pull "ghcr.io/${IMAGE_OWNER}/sentineliq-frontend:${IMAGE_TAG}" || true
  echo "Updating compose and restarting"
  docker-compose -f "${COMPOSE_PATH}" pull || true
  docker-compose -f "${COMPOSE_PATH}" up -d --remove-orphans
  echo "Deployed"
EOF

echo "Done"
