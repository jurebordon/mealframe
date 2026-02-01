#!/bin/bash
# Backend Connectivity Diagnostic Script
# Run this on the VM: ssh root@192.168.1.100 'bash -s' < deploy/diagnose.sh

set -e

echo "=== MealFrame Backend Diagnostic ==="
echo ""

echo "1. Checking Docker containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2. Testing local frontend (localhost:3000)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo "✅ Frontend is accessible on localhost:3000"
else
    echo "❌ Frontend is NOT accessible on localhost:3000"
fi
echo ""

echo "3. Testing API via frontend (localhost:3000/api/v1/meal-types)..."
API_RESPONSE=$(curl -s http://localhost:3000/api/v1/meal-types)
if echo "$API_RESPONSE" | grep -q "id"; then
    echo "✅ API is accessible via frontend"
    echo "Sample response: ${API_RESPONSE:0:100}..."
else
    echo "❌ API is NOT accessible via frontend"
    echo "Response: $API_RESPONSE"
fi
echo ""

echo "4. Checking environment variables..."
if [ -f .env ]; then
    echo "✅ .env file exists"
    echo "CORS_ORIGINS: $(grep CORS_ORIGINS .env | cut -d= -f2)"
    echo "NEXT_PUBLIC_API_URL: $(grep NEXT_PUBLIC_API_URL .env | cut -d= -f2)"
else
    echo "❌ .env file NOT found"
fi
echo ""

echo "5. Checking Docker network..."
WEB_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mealframe-web)
API_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mealframe-api)
echo "Web container IP: $WEB_IP"
echo "API container IP: $API_IP"
echo ""

echo "6. Testing web → api connectivity (internal network)..."
if docker exec mealframe-web wget -q -O- http://api:8003/api/v1/meal-types > /dev/null 2>&1; then
    echo "✅ Web container can reach API container"
else
    echo "❌ Web container CANNOT reach API container"
fi
echo ""

echo "7. Checking recent logs for errors..."
echo "--- API Logs (last 10 lines) ---"
docker compose logs api --tail=10 2>&1 | grep -v "INFO:     192.168" | tail -10
echo ""
echo "--- Web Logs (last 10 lines) ---"
docker compose logs web --tail=10 2>&1 | grep -v "compiled successfully" | tail -10
echo ""

echo "8. Network connectivity test..."
echo "Testing if port 3000 is listening:"
if netstat -tuln | grep -q ":3000 "; then
    echo "✅ Port 3000 is listening"
    netstat -tuln | grep ":3000 "
else
    echo "❌ Port 3000 is NOT listening"
fi
echo ""

echo "=== Diagnostic Complete ==="
echo ""
echo "Next steps:"
echo "1. If localhost:3000 API works: Check NPM proxy configuration"
echo "2. If localhost:3000 API fails: Check container logs and environment"
echo "3. See TROUBLESHOOTING_BACKEND.md for detailed solutions"
