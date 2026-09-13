#!/bin/bash
# Comprehensive SentinelOps AI System Verification Script

set -e

echo "=========================================="
echo "SentinelOps AI System Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check_file() {
  local file=$1
  local search=$2
  local description=$3

  if grep -r "$search" "$file" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} FAIL: $description"
    echo "  Found: $(grep -r "$search" "$file" | head -1)"
    ((FAIL++))
  else
    echo -e "${GREEN}✓${NC} PASS: $description"
    ((PASS++))
  fi
}

check_exists() {
  local file=$1
  local description=$2

  if [ -f "$file" ]; then
    echo -e "${GREEN}✓${NC} PASS: $description"
    ((PASS++))
  else
    echo -e "${RED}✗${NC} FAIL: $description"
    echo "  File not found: $file"
    ((FAIL++))
  fi
}

check_contains() {
  local file=$1
  local search=$2
  local description=$3

  if grep -q "$search" "$file" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PASS: $description"
    ((PASS++))
  else
    echo -e "${RED}✗${NC} FAIL: $description"
    echo "  Expected pattern not found: $search"
    ((FAIL++))
  fi
}

echo "1. Checking for Cloud API Usage..."
echo "   Searching for banned API references..."
check_file "backend/src" "openai" "No OpenAI API usage"
check_file "backend/src" "claude" "No Claude API usage"
check_file "backend/src" "gemini" "No Gemini API usage"
check_file "backend/src" "anthropic" "No Anthropic API usage"
check_file "frontend/src" "openai\|claude\|gemini" "No cloud APIs in frontend"
echo ""

echo "2. Checking AI Agent Implementation..."
check_exists "backend/src/sentinelops/ai/agents.py" "AI agents module"
check_contains "backend/src/sentinelops/ai/agents.py" "class CPUAgent" "CPU Agent implemented"
check_contains "backend/src/sentinelops/ai/agents.py" "class MemoryAgent" "Memory Agent implemented"
check_contains "backend/src/sentinelops/ai/agents.py" "class NPLInfrastructureAssistant" "NLP Assistant implemented"
check_contains "backend/src/sentinelops/ai/agents.py" "class StorageAgent" "Storage Agent implemented"
check_contains "backend/src/sentinelops/ai/agents.py" "class NetworkAgent" "Network Agent implemented"
check_contains "backend/src/sentinelops/ai/agents.py" "class LogsAgent" "Logs Agent implemented"
echo ""

echo "3. Checking Orchestrator Implementation..."
check_exists "backend/src/sentinelops/ai/orchestrator.py" "AI Orchestrator"
check_contains "backend/src/sentinelops/ai/orchestrator.py" "PIPELINE" "Pipeline defined"
check_contains "backend/src/sentinelops/ai/orchestrator.py" "async def orchestrate" "orchestrate method"
echo ""

echo "4. Checking Safety & Validation..."
check_exists "backend/src/sentinelops/ai/registry.py" "Agent Registry"
check_contains "backend/src/sentinelops/ai/registry.py" "class AIAgentRegistry" "Registry implemented"
check_contains "backend/src/sentinelops/ai/registry.py" "class AISafetyValidator" "Safety validator"
echo ""

echo "5. Checking Ollama Client..."
check_exists "backend/src/sentinelops/ai/ollama_client.py" "Ollama Client"
check_contains "backend/src/sentinelops/ai/ollama_client.py" "class OllamaClient" "OllamaClient implemented"
check_contains "backend/src/sentinelops/ai/ollama_client.py" "async def generate" "generate method"
echo ""

echo "6. Checking Frontend Components..."
check_exists "frontend/src/components/dashboard/AIInsightsPanel.tsx" "AI Insights Panel"
check_exists "frontend/src/components/dashboard/AIAssistantPanel.tsx" "AI Assistant Panel"
check_exists "frontend/src/components/dashboard/ConfidenceVisualization.tsx" "Confidence Visualization"
check_exists "frontend/src/components/dashboard/RCAPanel.tsx" "RCA Panel"
echo ""

echo "7. Checking Database Schema..."
check_exists "backend/alembic/versions/004_ai_agents_schema.py" "AI Agent schema migration"
check_contains "backend/alembic/versions/004_ai_agents_schema.py" "ai_insights" "ai_insights table"
check_contains "backend/alembic/versions/004_ai_agents_schema.py" "ai_reasoning_logs" "ai_reasoning_logs table"
check_contains "backend/alembic/versions/004_ai_agents_schema.py" "ai_recommendations" "ai_recommendations table"
echo ""

echo "8. Checking Integration Points..."
check_exists "backend/src/sentinelops/workers/runner.py" "Worker runner"
check_contains "backend/src/sentinelops/workers/runner.py" "AIOrchestrator" "AIOrchestrator imported"
check_contains "backend/src/sentinelops/workers/runner.py" "orchestrate" "orchestrate called"
echo ""

echo "9. Checking Docker Configuration..."
check_exists "docker-compose.yml" "Docker Compose file"
check_contains "docker-compose.yml" "ollama" "Ollama service configured"
check_contains "docker-compose.yml" "model.*pull" "Model preloading configured"
echo ""

echo "10. Checking Documentation..."
check_exists "STARTUP_AND_VALIDATION.md" "Startup documentation"
echo ""

echo "=========================================="
echo "Verification Results:"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}✓ All checks passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some checks failed. Please review above.${NC}"
  exit 1
fi
