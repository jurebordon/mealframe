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

**Option A: Via Proxmox host (most reliable)**

```bash
# On your Mac - copy to Proxmox host
scp deploy/ct-setup.sh root@proxmox-host-ip:/tmp/

# SSH to Proxmox host
ssh root@proxmox-host-ip

# Push to CT (replace 100 with your CT ID)
pct push 100 /tmp/ct-setup.sh /root/ct-setup.sh

# Enter CT console and run setup
pct enter 100
chmod +x /root/ct-setup.sh
/root/ct-setup.sh
```

**Option B: Direct SSH (if SSH is enabled)**

```bash
# Copy setup script to CT
scp deploy/ct-setup.sh root@192.168.1.100:/root/

# SSH to CT and run
ssh root@192.168.1.100
chmod +x /root/ct-setup.sh
/root/ct-setup.sh
```

**If SSH fails:** Use Option A, or enable SSH in CT:
```bash
# From Proxmox host
pct enter 100
apt update && apt install -y openssh-server
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd
exit
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

# Generate SSH key for GitHub
ssh-keygen -t ed25519 -C "mealframe-ct"
# Press Enter for all prompts (default location, no passphrase)

# Display public key
cat ~/.ssh/id_ed25519.pub
# Copy this entire output
```

**Add SSH key to GitHub:**
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Title: "MealFrame CT"
4. Paste the public key from above
5. Click "Add SSH key"

**Back on the CT:**
```bash
# Clone repo using SSH
cd /opt/mealframe
git clone git@github.com:jurebordon/mealframe.git .

# Create production environment
cp deploy/.env.production.template .env.production

# Generate secure password
openssl rand -base64 32
# Copy this password

# Edit .env.production
nano .env.production
# Replace CHANGE_ME_TO_SECURE_PASSWORD with your password (2 places)
# Save (Ctrl+O, Enter, Ctrl+X)

# Make deploy script executable
chmod +x deploy/deploy.sh
```

### ☐ Step 5: Configure GitHub Actions Secrets (5 min)

**Create SSH key for deployment:**

```bash
# On your Mac, generate a deployment key
ssh-keygen -t ed25519 -f ~/.ssh/mealframe-deploy -C "mealframe-deploy" -N ""

# Copy public key to the CT
ssh-copy-id -i ~/.ssh/mealframe-deploy.pub root@192.168.1.100

# Test SSH connection
ssh -i ~/.ssh/mealframe-deploy root@192.168.1.100 "echo 'SSH works!'"

# Base64 encode the private key for GitHub
cat ~/.ssh/mealframe-deploy | base64 | tr -d '\n'
# Copy this entire output
```

**Add secrets to GitHub repository:**

Go to your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value |
|-------------|-------|
| `HOMELAB_SSH_KEY_BASE64` | The base64-encoded private key from above |
| `HOMELAB_WAN_IP` | Your public IP (or use a DDNS hostname) |
| `HOMELAB_SSH_PORT` | Your SSH port (forwarded through router) |
| `HOMELAB_USERNAME` | `root` (or your deploy user) |

**Set up SSH port forwarding on your router:**

Forward an external port (e.g., 2222) to your CT's SSH port (22) at 192.168.1.100.

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

### ☐ Step 9: Test Auto-Deploy (2 min)

Auto-deploy is already configured! The GitHub Actions workflow uses SSH to connect directly to your homelab and run the deployment script.

**Verify it works:**

1. Check GitHub Actions tab in your repo - the deploy workflow should run on every push to main
2. View workflow logs to confirm SSH connection succeeds
3. Check deployment logs on CT: `cat /var/log/mealframe-deploy.log`

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

**Backend connectivity issues?** See [TROUBLESHOOTING_BACKEND.md](TROUBLESHOOTING_BACKEND.md) for step-by-step diagnosis.

**Run diagnostic script on VM:**
```bash
ssh root@192.168.1.100
cd /opt/mealframe
bash deploy/diagnose.sh
```

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

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for more common issues.
