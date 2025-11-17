#!/bin/bash
# TweekIT Web Converter Launcher

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

if [ ! -d "examples/web-converter" ]; then
    echo "Error: Must run from tweekit-mcp root"
    exit 1
fi

print_header "TweekIT Web Converter Launcher"

if [ -f .env ]; then
    echo -e "${YELLOW}→ Loading API credentials${NC}"
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Credentials loaded${NC}"
fi

echo ""
echo "Starting standalone HTML version..."
cd examples/web-converter

PORT=8080
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; do
    PORT=$((PORT+1))
done

echo -e "${GREEN}✓ Server starting on port $PORT${NC}"
echo ""
echo "Web Converter: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

if command -v open >/dev/null 2>&1; then
    sleep 1 && open "http://localhost:$PORT" &
fi

python3 -m http.server $PORT
