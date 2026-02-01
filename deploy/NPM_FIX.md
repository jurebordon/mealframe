# NPM Configuration Fix for Backend API

## Problem
Frontend loads but API requests return 404. This is because NPM is only proxying to the Next.js web container, which doesn't handle `/api/` requests.

## Solution
Configure NPM to proxy `/api/` requests directly to the FastAPI backend on port 8003.

---

## Step 1: Deploy Updated Docker Compose

On the VM (ssh root@192.168.1.100):

```bash
cd /opt/mealframe

# Pull latest code (includes updated docker-compose.npm.yml)
git pull origin main

# Rebuild and restart containers
docker compose -f docker-compose.yml -f docker-compose.npm.yml down
docker compose -f docker-compose.yml -f docker-compose.npm.yml up -d --build

# Verify all containers are running
docker ps

# Test locally that API is accessible
curl http://localhost:8003/api/v1/meal-types
curl http://localhost:3000  # Frontend should also work
```

**Expected:**
- Port 8003 is now exposed and accessible
- API returns JSON response with meal types
- Frontend loads normally

---

## Step 2: Update NPM Configuration

In your Nginx Proxy Manager web interface:

### Edit the Proxy Host

1. Go to **Hosts** → **Proxy Hosts**
2. Find `meals.bordon.family`
3. Click the **3 dots** → **Edit**

### Details Tab

Keep these settings as-is:
- Domain: `meals.bordon.family`
- Scheme: `http`
- Forward Hostname/IP: `192.168.1.100`
- Forward Port: `3000`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

### Advanced Tab

**REPLACE the entire content** with this:

```nginx
# Proxy API requests to FastAPI backend
location /api/ {
    proxy_pass http://192.168.1.100:8003/api/;
    proxy_http_version 1.1;

    # WebSocket support (if needed later)
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';

    # Standard proxy headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Disable caching for API requests
    proxy_cache_bypass $http_upgrade;
    proxy_no_cache 1;
    proxy_cache_bypass 1;
}
```

### SSL Tab

Keep as-is:
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

### Custom Locations Tab

**REMOVE any custom locations for /api/** if you added them earlier. We're using the Advanced tab instead.

### Save

Click **Save** and wait 30 seconds for NPM to reload.

---

## Step 3: Test the Fix

### From Your Mac (on mobile internet):

```bash
# Test API endpoint
curl -k https://meals.bordon.family/api/v1/meal-types

# Should return JSON like:
# [{"id":1,"name":"Breakfast","description":"Morning meal"}, ...]
```

### In Browser:

1. Open https://meals.bordon.family
2. Open Developer Tools (F12 / Cmd+Option+I)
3. Go to **Network** tab
4. Reload the page
5. Look for requests to `/api/v1/...`
6. They should return **200 OK** with JSON data

### Expected Results:

- ✅ Frontend loads
- ✅ API calls return 200 OK
- ✅ Your meal plan data appears
- ✅ No CORS errors in console

---

## Troubleshooting

### Still getting 404 on /api/ requests?

**Check NPM logs:**
```bash
# On NPM server (wherever NPM is running)
docker logs nginx-proxy-manager | tail -50
```

**Look for:**
- Errors about upstream not found
- Connection refused to 192.168.1.100:8003

**Verify API is reachable from NPM:**
```bash
# SSH to wherever NPM is running
curl http://192.168.1.100:8003/api/v1/meal-types
```

If this fails, it's a network routing issue between NPM and the MealFrame VM.

### Getting Connection Refused?

**On the VM, check if port 8003 is listening:**
```bash
netstat -tuln | grep 8003
```

Should show:
```
tcp        0      0 0.0.0.0:8003            0.0.0.0:*               LISTEN
```

If not listening:
```bash
# Check API container logs
docker compose logs api

# Restart containers
docker compose -f docker-compose.yml -f docker-compose.npm.yml restart
```

### Still Not Working?

Run the diagnostic script:
```bash
ssh root@192.168.1.100
cd /opt/mealframe
bash deploy/diagnose.sh
```

Check [TROUBLESHOOTING_BACKEND.md](TROUBLESHOOTING_BACKEND.md) for more detailed diagnosis.

---

## Why This Works

**Before:**
```
Browser → NPM → Web:3000 → 404 (Next.js doesn't handle /api/)
```

**After:**
```
Browser → NPM → Web:3000 (for / homepage, assets)
                └→ API:8003 (for /api/* requests)
```

NPM now intelligently routes:
- `/` , `/meals`, `/week`, etc. → **Web container** (Next.js) on port 3000
- `/api/*` → **API container** (FastAPI) on port 8003

This matches how you have it configured locally, but adapted for production with NPM as the reverse proxy.

---

## What Changed

1. **docker-compose.npm.yml**: Now exposes API container on port 8003
2. **NPM Advanced config**: Added `/api/` location block to proxy to port 8003
3. **Architecture**: NPM acts as the central reverse proxy instead of Next.js

This is the correct production architecture for a Next.js + FastAPI stack behind a reverse proxy.
