# Backend Connectivity Troubleshooting

## Issue
Frontend loads at https://meals.bordon.family but cannot reach backend API. App works perfectly on localhost:3000.

## Diagnosis Checklist

Run these commands on the VM (ssh root@192.168.1.100) to diagnose the issue:

### 1. Verify Containers Are Running

```bash
docker ps
```

**Expected output:** All three containers should show "Up":
- `mealframe-web` on port 3000
- `mealframe-api` (internal, no exposed port)
- `mealframe-db` (internal, no exposed port)

**If any container is missing or restarting:** Check logs with `docker compose logs <service>`

### 2. Test Local Connectivity

```bash
# Test frontend
curl -I http://localhost:3000

# Test API directly
curl http://localhost:3000/api/v1/meal-types

# Test backend API container directly (if port 8003 is exposed)
curl http://localhost:8003/api/v1/meal-types
```

**Expected:**
- Frontend: HTTP 200 OK
- API via frontend: JSON response with meal types
- Backend direct: JSON response (if port exposed)

**If API calls fail on localhost:** Backend is not running properly
**If API calls work on localhost:** Issue is with NPM proxy configuration

### 3. Check Docker Network

```bash
# Inspect the network
docker network ls
docker network inspect mealframe_default

# Check if web can reach api
docker exec mealframe-web wget -O- http://api:8003/api/v1/meal-types
```

**Expected:** Web container should be able to reach API container via internal network

### 4. Check Container Logs

```bash
# Check web container logs
docker compose logs web --tail=50

# Check API container logs
docker compose logs api --tail=50

# Follow logs in real-time while accessing from domain
docker compose logs -f
```

**Look for:**
- CORS errors
- Connection refused errors
- 404 or routing errors
- Database connection issues

### 5. Test from NPM Server

If NPM is on a different machine, SSH to it and test:

```bash
# From NPM server, test if it can reach the VM
curl http://192.168.1.100:3000
curl http://192.168.1.100:3000/api/v1/meal-types
```

**Expected:** Both should return successful responses

**If this fails:** Network routing issue between NPM and VM

### 6. Check NPM Configuration

In NPM UI, verify the Proxy Host settings:

**Details Tab:**
- Domain: `meals.bordon.family`
- Scheme: `http`
- Forward Hostname/IP: `192.168.1.100`
- Forward Port: `3000`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

**Advanced Tab - Option A (Recommended):**

Add this in the Advanced section:

```nginx
location /api/ {
    proxy_pass http://192.168.1.100:3000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Advanced Tab - Option B (Alternative):**

If using Custom Locations instead, ensure:
- Path: `/api/`
- Forward Scheme: `http`
- Forward Hostname/IP: `192.168.1.100`
- Forward Port: `3000`

**After changing NPM config:** Save and wait 30 seconds for reload

### 7. Check Browser Network Tab

Open https://meals.bordon.family in browser:
1. Open Developer Tools (F12)
2. Go to Network tab
3. Reload page
4. Look for failed API requests

**Common issues:**
- Requests to `/api/v1/...` returning 502 Bad Gateway
- Requests to `/api/v1/...` returning 404 Not Found
- CORS errors in console

### 8. Test API from External

From your Mac (not the VM):

```bash
# Test if domain resolves
dig meals.bordon.family

# Test frontend
curl -I https://meals.bordon.family

# Test API endpoint
curl https://meals.bordon.family/api/v1/meal-types
```

**Expected:**
- Frontend: HTTP 200
- API: JSON response with meal types

## Common Issues & Solutions

### Issue: 502 Bad Gateway on /api/ requests

**Cause:** NPM cannot reach the backend

**Solution:**
1. Verify containers are running: `docker ps`
2. Test local API: `curl http://localhost:3000/api/v1/meal-types`
3. Restart containers: `docker compose restart`

### Issue: 404 Not Found on /api/ requests

**Cause:** NPM is not configured to proxy /api/ path

**Solution:**
1. Add the nginx location block in NPM Advanced tab (see Section 6)
2. Save and wait for NPM to reload

### Issue: CORS errors in browser

**Cause:** API not allowing requests from domain

**Solution:**
1. Check `.env` file has correct CORS_ORIGINS
2. Should be: `CORS_ORIGINS=https://meals.bordon.family`
3. Restart API: `docker compose restart api`

### Issue: Frontend loads but shows "No plan" or empty data

**Cause:** API calls are failing silently

**Solution:**
1. Open browser DevTools → Network tab
2. Look for failed requests to /api/
3. Check the error (502, 404, CORS, etc.)
4. Follow relevant troubleshooting above

### Issue: API works on localhost:3000 but not through domain

**Cause:** NPM proxy configuration incomplete

**Solution:**
1. Ensure Advanced nginx config is in place (Section 6, Option A)
2. OR ensure Custom Locations are configured (Section 6, Option B)
3. Do NOT use both - pick one method
4. Verify NEXT_PUBLIC_API_URL in `.env`:
   - Should be: `NEXT_PUBLIC_API_URL=https://meals.bordon.family/api/v1`
5. Rebuild web container: `docker compose up -d --build web`

## Environment Variables Check

On the VM, verify environment variables are correct:

```bash
cat .env
```

Should contain:

```
DB_PASSWORD=<your-secure-password>
CORS_ORIGINS=https://meals.bordon.family
NEXT_PUBLIC_API_URL=https://meals.bordon.family/api/v1
```

**If different:** Edit `.env`, then `docker compose up -d --build`

## Quick Fixes

### Restart Everything

```bash
docker compose down
docker compose up -d
```

### Rebuild from Scratch

```bash
docker compose down -v
docker compose up -d --build
```

### Check NPM Logs

If NPM is running in Docker:

```bash
docker logs nginx-proxy-manager
```

Look for errors related to `meals.bordon.family`

## Next Steps Based on Results

**If localhost:3000 API works but domain doesn't:**
→ NPM configuration issue (Section 6)

**If localhost:3000 API doesn't work:**
→ Container/backend issue (Section 1-4)

**If NPM can't reach 192.168.1.100:3000:**
→ Network/firewall issue (Section 5)

**If API returns CORS errors:**
→ Environment variable issue (CORS_ORIGINS)

---

**Current Status:** Diagnosing why API works on localhost:3000 but not through https://meals.bordon.family
