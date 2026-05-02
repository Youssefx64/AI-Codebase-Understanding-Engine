#!/bin/bash
# Example API usage for the AI Codebase Understanding Engine
# Assumes the server is running at localhost:8000

BASE_URL="${API_URL:-http://localhost:8000}"

echo "=== AI Codebase Understanding Engine - Example Usage ==="
echo

# 1. Health check
echo "1. Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo

# 2. Submit a repository for analysis
echo "2. Submit Repository for Analysis"
RESPONSE=$(curl -s -X POST "$BASE_URL/analyze-repo" \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/tiangolo/fastapi",
    "branch": "master"
  }')
echo "$RESPONSE" | python3 -m json.tool
REPO_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['repo_id'])")
echo "Repo ID: $REPO_ID"
echo

# 3. Poll for completion
echo "3. Checking analysis status..."
for i in {1..5}; do
  sleep 5
  STATUS=$(curl -s "$BASE_URL/repo-summary/$REPO_ID" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Status: $STATUS"
  if [ "$STATUS" = "complete" ]; then break; fi
done
echo

# 4. Get full summary
echo "4. Repository Summary"
curl -s "$BASE_URL/repo-summary/$REPO_ID" | python3 -m json.tool
echo

# 5. Get dependency graph
echo "5. Dependency Graph (file nodes only)"
curl -s "$BASE_URL/dependency-graph/$REPO_ID?node_type=file&max_nodes=20" | python3 -m json.tool
echo

# 6. Ask a question
echo "6. Developer Q&A"
curl -s -X POST "$BASE_URL/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"repo_id\": \"$REPO_ID\",
    \"question\": \"How does dependency injection work in this codebase?\",
    \"max_chunks\": 5
  }" | python3 -m json.tool
echo

# 7. Get issues
echo "7. Detected Issues (high severity)"
curl -s "$BASE_URL/issues/$REPO_ID?severity=high" | python3 -m json.tool
echo

# 8. Get refactoring suggestions
echo "8. Refactoring Suggestions (low effort)"
curl -s "$BASE_URL/refactor/$REPO_ID?effort=low" | python3 -m json.tool
echo

echo "=== Done ==="
