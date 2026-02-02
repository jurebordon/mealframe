#!/bin/bash
# MealFrame Proxmox CT Setup Script
# Run this script on your new Ubuntu CT after creation

set -e

echo "=== MealFrame CT Setup ==="
echo ""

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install Docker
echo "Installing Docker..."
apt install -y curl ca-certificates gnupg lsb-release

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl enable docker
systemctl start docker

# Verify Docker installation
docker --version
docker compose version

# Install git (for pulling code)
echo "Installing git..."
apt install -y git

# Create mealframe directory
echo "Creating application directory..."
mkdir -p /opt/mealframe
cd /opt/mealframe

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Clone the repository: cd /opt/mealframe && git clone <your-repo-url> ."
echo "2. Create .env.production from template (see deploy/.env.production.template)"
echo "3. Make deploy script executable: chmod +x deploy/deploy.sh"
echo "4. Start containers: docker compose -f docker-compose.yml -f docker-compose.npm.yml up -d"
echo ""
echo "For auto-deploy via GitHub Actions:"
echo "- Set up SSH port forwarding on your router"
echo "- Add SSH key and secrets to GitHub repository"
echo "- See deploy/QUICK_START.md for details"
