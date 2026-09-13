#!/bin/bash
# SentinelOps One-Click Deployment Script
# Run this to start everything and open in Chrome

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="8000"
FRONTEND_PORT="5173"

echo "🚀 SentinelOps Enterprise Platform - Starting Deployment"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Ensure required services are running locally.${NC}"
fi

# Check if PostgreSQL is accessible
echo -e "${BLUE}[1/5]${NC} Checking PostgreSQL connection..."
if psql -U sentinelops sentinelops -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL connected${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL connection check skipped or service unreachable.${NC}"
fi

# Run migrations
echo -e "${BLUE}[2/5]${NC} Running database migrations..."
cd "$PROJECT_ROOT/backend"
if alembic upgrade head > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database migrations complete${NC}"
else
    echo -e "${YELLOW}⚠️  Migration warning (may already be up to date)${NC}"
fi

# Start backend
echo -e "${BLUE}[3/5]${NC} Starting FastAPI backend on port ${BACKEND_PORT}..."
cd "$PROJECT_ROOT/backend"
nohup uvicorn sentinelops.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > /tmp/sentinelops-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend
echo -e "${BLUE}[4/5]${NC} Starting React frontend on port ${FRONTEND_PORT}..."
cd "$PROJECT_ROOT/frontend"
nohup npm run dev -- --port $FRONTEND_PORT > /tmp/sentinelops-frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for services to be ready
echo -e "${BLUE}[5/5]${NC} Waiting for services to be ready..."
sleep 3

# Check if services are responding
if curl -s http://localhost:$BACKEND_PORT/api/v1/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not responding yet, it may take a moment${NC}"
fi

if curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
    echo -e "${GREEN}✅ Frontend is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend not responding yet, it may take a moment${NC}"
fi

# Open Chrome
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 SentinelOps is ready!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "📍 Frontend: ${BLUE}http://localhost:${FRONTEND_PORT}${NC}"
echo -e "📍 Backend:  ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
echo ""
echo -e "Opening Chrome in 2 seconds..."
sleep 2

# Open in Chrome (cross-platform)
if command -v chrome &> /dev/null; then
    chrome "http://localhost:$FRONTEND_PORT"
elif command -v google-chrome &> /dev/null; then
    google-chrome "http://localhost:$FRONTEND_PORT"
elif command -v chromium &> /dev/null; then
    chromium "http://localhost:$FRONTEND_PORT"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    cmd /c "start chrome http://localhost:$FRONTEND_PORT"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open -a "Google Chrome" "http://localhost:$FRONTEND_PORT"
else
    echo -e "${YELLOW}⚠️  Couldn't auto-open Chrome. Please navigate to: http://localhost:$FRONTEND_PORT${NC}"
fi

echo ""
echo -e "📋 Logs:"
echo -e "  Backend:  tail -f /tmp/sentinelops-backend.log"
echo -e "  Frontend: tail -f /tmp/sentinelops-frontend.log"
echo ""
echo -e "🛑 To stop all services:"
echo -e "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
