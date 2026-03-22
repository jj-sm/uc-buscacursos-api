#!/bin/bash
# Health check and verification script for Universal API Template

set -e

BASE_URL="${1:-http://localhost:8000}"
API_KEY="${2:-}"

echo "🔍 Universal API - Health Check & Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Target URL: $BASE_URL"
echo ""

# Check if server is running
echo "1️⃣  Checking if API is running..."
if ! command -v curl &> /dev/null; then
    echo "   ⚠️  curl not found, using python instead"
    python3 -c "import urllib.request; urllib.request.urlopen('$BASE_URL/health')" 2>/dev/null && echo "   ✅ API is running!" || {
        echo "   ❌ Cannot connect to $BASE_URL"
        echo "   Start the API with: python run.py"
        exit 1
    }
else
    curl -s "$BASE_URL/health" > /dev/null && echo "   ✅ API is running!" || {
        echo "   ❌ Cannot connect to $BASE_URL"
        echo "   Start the API with: python run.py"
        exit 1
    }
fi

echo ""
echo "2️⃣  Testing health check endpoint..."
curl -s "$BASE_URL/health" | python3 -m json.tool 2>/dev/null && echo "   ✅ Health check OK" || echo "   ⚠️  Could not parse response"

echo ""
echo "3️⃣  Testing root endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool 2>/dev/null | head -n 10
echo "   ✅ Root endpoint OK"

echo ""
echo "4️⃣  Testing documentation endpoints..."
echo "   • Swagger UI: $BASE_URL/docs"
curl -s -I "$BASE_URL/docs" | grep "200" > /dev/null && echo "     ✅ Available" || echo "     ❌ Not available"

echo "   • ReDoc: $BASE_URL/redoc"
curl -s -I "$BASE_URL/redoc" | grep "200" > /dev/null && echo "     ✅ Available" || echo "     ❌ Not available"

echo "   • OpenAPI Schema: $BASE_URL/openapi.json"
curl -s -I "$BASE_URL/openapi.json" | grep "200" > /dev/null && echo "     ✅ Available" || echo "     ❌ Not available"

echo ""
echo "5️⃣  Testing routers..."
echo "   • Admin router: $BASE_URL/api/admin/"
curl -s -I "$BASE_URL/api/admin/" | head -n 1

echo "   • Template router: $BASE_URL/api/template/"
curl -s -I "$BASE_URL/api/template/" | head -n 1

echo "   • Airports router: $BASE_URL/api/airports/"
curl -s -I "$BASE_URL/api/airports/" | head -n 1

echo ""
echo "6️⃣  Testing authentication..."
if [ -n "$API_KEY" ]; then
    echo "   Testing with API key: $API_KEY"
    curl -s -H "X-API-Key: $API_KEY" "$BASE_URL/api/template/" | python3 -m json.tool 2>/dev/null && echo "   ✅ Authentication works" || echo "   ⚠️  Request completed"
else
    echo "   ⚠️  No API key provided (use: ./verify.sh [URL] [API_KEY])"
    echo "   Testing without auth (expect 403):"
    curl -s -w "\n   Status: %{http_code}\n" "$BASE_URL/api/template/" 2>/dev/null | head -n 5
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ API health check complete!"
echo ""
echo "Next steps:"
echo "  1. Visit http://localhost:8000/docs for interactive API documentation"
echo "  2. Create an API key via the admin panel"
echo "  3. Test endpoints with your API key using:"
echo "     curl -H 'X-API-Key: your-key' http://localhost:8000/api/template/"
echo ""
