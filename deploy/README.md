# MealFrame Deployment Files

This directory contains everything needed to deploy MealFrame to a Proxmox homelab with automated CI/CD.

## 📁 Files Overview

| File | Purpose |
|------|---------|
| **[QUICK_START.md](QUICK_START.md)** | ⚡ Start here! 10-step checklist (45 min total) |
| **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** | 📖 Complete deployment documentation |
| **ct-setup.sh** | 🔧 Automated Proxmox CT setup script |
| **deploy.sh** | 🚀 Deployment script (triggered by webhook) |
| **.env.production.template** | 🔐 Production environment template |
| **hooks.json.template** | 🪝 Webhook configuration template |

## 🚀 Quick Start

**First time deploying?**

1. Read [QUICK_START.md](QUICK_START.md) - follow the checklist
2. Reference [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details

**Already deployed?**

Just `git push` - your changes auto-deploy! 🎉

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└─────────────────────┬───────────────────────────────────┘
                      │ meals.bordon.family
                      ↓
┌─────────────────────────────────────────────────────────┐
│              Nginx Proxy Manager                         │
│              (SSL, reverse proxy)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ :3000
                      ↓
┌─────────────────────────────────────────────────────────┐
│           Proxmox CT (192.168.1.100)                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Docker Compose Stack                              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │ │
│  │  │ Next.js  │  │ FastAPI  │  │ PostgreSQL   │    │ │
│  │  │  :3000   │◄─┤  :8003   │◄─┤  (internal)  │    │ │
│  │  └──────────┘  └──────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Webhook Listener :9000                            │ │
│  │  (listens for GitHub push events)                 │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                      ↑
                      │ webhook trigger
                      │
┌─────────────────────────────────────────────────────────┐
│              GitHub Actions                              │
│              (on push to main)                           │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Deployment Flow

1. **Developer pushes code** → GitHub (main branch)
2. **GitHub Actions** → Generates webhook signature
3. **Webhook sent** → Homelab CT (authenticated with HMAC)
4. **Webhook listener** → Triggers deploy.sh
5. **deploy.sh** → Pulls latest code, rebuilds containers
6. **Containers restart** → App updated at meals.bordon.family

Total time: ~30 seconds from push to live.

## 🛠️ Maintenance Commands

SSH to CT: `ssh root@192.168.1.100`

### View Logs

```bash
# Application logs
cd /opt/mealframe
docker compose -f docker-compose.yml -f docker-compose.npm.yml logs -f

# Specific service
docker compose logs -f web
docker compose logs -f api
docker compose logs -f db

# Webhook logs
journalctl -u mealframe-webhook -f

# Deployment history
cat /var/log/mealframe-deploy.log
```

### Restart Services

```bash
# Restart all containers
docker compose -f docker-compose.yml -f docker-compose.npm.yml restart

# Restart specific service
docker compose restart web

# Full rebuild
docker compose -f docker-compose.yml -f docker-compose.npm.yml down
docker compose -f docker-compose.yml -f docker-compose.npm.yml up -d --build
```

### Database Backup

```bash
# Backup
docker exec mealframe-db pg_dump -U mealframe mealframe > backup-$(date +%Y%m%d).sql

# Restore
docker exec -i mealframe-db psql -U mealframe mealframe < backup-20260130.sql
```

## 🔐 Security

- ✅ HMAC-SHA256 webhook authentication
- ✅ Secrets stored in GitHub Actions (not in code)
- ✅ SSL via Let's Encrypt (NPM)
- ✅ Database password in `.env.production` (not committed)
- ✅ CORS restricted to domain only
- ✅ Production containers run as non-root

## 📊 Monitoring

**Health Checks:**

```bash
# Check all containers
docker ps

# Test API
curl http://localhost:3000/api/v1/meal-types

# Test from outside
curl https://meals.bordon.family/api/v1/meal-types
```

**Resource Usage:**

```bash
# Container stats
docker stats

# Disk usage
docker system df

# CT resources
pct status <CTID>
```

## 🆘 Troubleshooting

**Backend connectivity issues?**

Frontend loads but can't reach API? See [TROUBLESHOOTING_BACKEND.md](TROUBLESHOOTING_BACKEND.md)

Run diagnostic script:
```bash
ssh root@192.168.1.100
cd /opt/mealframe
bash deploy/diagnose.sh
```

**App not loading?**

```bash
# Check containers
docker ps  # All should show "Up"

# Check logs for errors
docker compose logs --tail=100

# Restart
docker compose restart
```

**Webhook not triggering?**

```bash
# Check webhook service
systemctl status mealframe-webhook

# Test manually
curl -X POST http://localhost:9000/hooks/deploy-mealframe \
  -H "Content-Type: application/json" \
  -d '{"ref":"refs/heads/main"}'

# Check webhook logs
journalctl -u mealframe-webhook -n 50
```

**SSL issues?**

- Ensure ports 80 and 443 forwarded to NPM on router
- Check DNS points to your public IP: `dig meals.bordon.family`
- Wait for DNS propagation (up to 48 hours)
- Verify NPM proxy host configuration

**Database issues?**

```bash
# Check database is running
docker exec mealframe-db pg_isready -U mealframe

# Check connection
docker exec mealframe-api env | grep DATABASE_URL

# Access database
docker exec -it mealframe-db psql -U mealframe
```

## 📚 Additional Resources

- **Project Documentation**: [../docs/](../docs/)
- **Docker Compose Configs**: [../docker-compose.yml](../docker-compose.yml), [../docker-compose.npm.yml](../docker-compose.npm.yml)
- **GitHub Actions**: [../.github/workflows/deploy.yml](../.github/workflows/deploy.yml)

## 🤝 Contributing

After making changes:

1. Test locally: `docker compose up`
2. Commit: `git commit -m "feat: your change"`
3. Push: `git push`
4. Auto-deploys to homelab! 🎉

---

**Questions?** Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive documentation.
