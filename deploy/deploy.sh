#!/bin/bash
# MealFrame Deployment Script
# Triggered by GitHub Actions via SSH or manually

set -e

DEPLOY_DIR="${DEPLOY_DIR:-/opt/mealframe}"
LOG_FILE="/var/log/mealframe-deploy.log"

echo "=== MealFrame Deployment Started at $(date) ===" | tee -a "$LOG_FILE"

cd "$DEPLOY_DIR"

# Pull latest code
echo "Pulling latest code..." | tee -a "$LOG_FILE"
git pull origin main

# Build and restart containers with bundled nginx reverse proxy
echo "Building and restarting containers..." | tee -a "$LOG_FILE"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans

# Clean up old images
echo "Cleaning up old images..." | tee -a "$LOG_FILE"
docker image prune -f

# Show container status
echo "Container status:" | tee -a "$LOG_FILE"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps | tee -a "$LOG_FILE"

echo "=== Deployment Complete at $(date) ===" | tee -a "$LOG_FILE"
