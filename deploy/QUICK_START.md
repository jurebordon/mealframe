# MealFrame Homelab Deployment - Quick Start

## TL;DR Checklist

Follow these steps in order. Full details in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

### ☐ Step 1: Create Proxmox CT (10 min)

**In Proxmox web UI:**
- Create CT: Ubuntu 22.04, 2GB RAM, 2 cores, 20GB disk
- Static IP: 192.168.1.100 (or your preferred IP)
- Note the Container ID (e.g., `100`)

**On Proxmox HOST (not the CT):**

```bash
# SSH to Proxmox host
ssh root@proxmox-host-ip

# Enable nesting (replace 100 with your Container ID)
pct set 100 -features nesting=1,keyctl=1

# Start the container
pct start 100
```

### ☐ Step 2: Setup CT (5 min)

```bash
# Copy setup script to CT
scp deploy/ct-setup.sh root@192.168.1.100:/root/

# SSH to CT and run
ssh root@192.168.1.100
chmod +x /root/ct-setup.sh
/root/ct-setup.sh
```

### ☐ Step 3: Push Code to GitHub (2 min)

```bash
# On your Mac
cd /Users/jure/Dev/meal-planner

# Create GitHub repo first at github.com/new
# Then:
git remote add origin git@github.com:YOUR_USERNAME/mealframe.git
git push -u origin main
```

### ☐ Step 4: Clone & Configure on CT (10 min)

```bash
# SSH to CT
ssh root@192.168.1.100

# Clone repo
cd /opt/mealframe
git clone https://github.com/YOUR_USERNAME/mealframe.git .

# Create production environment
cp deploy/.env.production.template .env.production

# Generate secure password
openssl rand -base64 32
# Copy this password

# Edit .env.production
nano .env.production
# Replace CHANGE_ME_TO_SECURE_PASSWORD with your password (2 places)
# Save (Ctrl+O, Enter, Ctrl+X)

# Generate webhook secret
openssl rand -hex 32
# Copy this secret - you'll need it for GitHub

# Setup webhook
cp deploy/hooks.json.template hooks.json
nano hooks.json
# Replace CHANGE_ME_TO_SECURE_SECRET with your webhook secret
# Save

# Make deploy script executable
chmod +x deploy/deploy.sh

# Enable webhook service
systemctl enable mealframe-webhook --now
systemctl status mealframe-webhook  # Should show "active (running)"
```

### ☐ Step 5: Configure GitHub Actions (2 min)

```bash
# In your GitHub repo:
# 1. Go to Settings → Secrets and variables → Actions
# 2. Click "New repository secret"
# 3. Name: WEBHOOK_SECRET
# 4. Value: (paste the webhook secret from Step 4)
# 5. Click "Add secret"
```

### ☐ Step 6: Configure NPM (5 min)

In Nginx Proxy Manager:

**Proxy Host:**
- Domain: `meals.bordon.family`
- Forward to: `192.168.1.100:3000`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

**SSL:**
- ✅ Request new SSL certificate (Let's Encrypt)
- ✅ Force SSL
- ✅ HTTP/2 Support

**Advanced:**
```nginx
location /api/ {
    proxy_pass http://192.168.1.100:3000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

### ☐ Step 7: Initial Deploy (5 min)

```bash
# SSH to CT
ssh root@192.168.1.100

# Start containers
cd /opt/mealframe
docker compose -f docker-compose.yml -f docker-compose.npm.yml up -d

# Check logs (Ctrl+C to exit)
docker compose -f docker-compose.yml -f docker-compose.npm.yml logs -f

# Verify it's working
curl http://localhost:3000
```

### ☐ Step 8: Test Access (2 min)

1. Local: http://192.168.1.100:3000
2. Domain: https://meals.bordon.family (after DNS propagates)
3. Mobile: https://meals.bordon.family

### ☐ Step 9: Enable Auto-Deploy (2 min)

```bash
# Edit the GitHub Actions workflow on your Mac
cd /Users/jure/Dev/meal-planner
nano .github/workflows/deploy.yml

# Uncomment these lines (around line 23-27):
# curl -X POST https://meals.bordon.family:9000/hooks/deploy-mealframe \
#   -H "Content-Type: application/json" \
#   -H "X-Hub-Signature-256: sha256=$signature" \
#   -d "$payload" \
#   --max-time 10 || echo "Webhook trigger sent"

# Commit and push
git add .github/workflows/deploy.yml
git commit -m "feat: enable webhook auto-deployment"
git push
```

**Note:** For webhook to work from internet, either:
- Option A: Forward port 9000 on router to 192.168.1.100:9000
- Option B: Create NPM proxy for `webhook.bordon.family` → `192.168.1.100:9000`

### ☐ Step 10: Test CI/CD (2 min)

```bash
# Make a test change
echo "# Deployed!" >> README.md
git add README.md
git commit -m "test: verify auto-deployment"
git push

# Watch it deploy:
# 1. Check GitHub Actions tab - workflow should run
# 2. On CT: tail -f /var/log/mealframe-deploy.log
```

---

## Done! 🎉

Your app is now:
- ✅ Running at https://meals.bordon.family
- ✅ Auto-deploys on git push
- ✅ SSL secured
- ✅ Accessible from anywhere

## Daily Usage

- **Access**: https://meals.bordon.family
- **Deploy**: Just `git push` - automatic!
- **Logs**: `ssh root@192.168.1.100 "cd /opt/mealframe && docker compose logs -f"`
- **Restart**: `docker compose -f docker-compose.yml -f docker-compose.npm.yml restart`

## Troubleshooting

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for common issues.

**Quick fixes:**
```bash
# Restart containers
docker compose -f docker-compose.yml -f docker-compose.npm.yml restart

# Rebuild from scratch
docker compose -f docker-compose.yml -f docker-compose.npm.yml down
docker compose -f docker-compose.yml -f docker-compose.npm.yml up -d --build

# Check webhook
systemctl status mealframe-webhook
journalctl -u mealframe-webhook -f
```
