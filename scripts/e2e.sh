#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

source "$HOME/.cargo/env" 2>/dev/null || true

# Build scorer if needed
if [[ ! -x "$ROOT/scorer/target/debug/scorer" ]]; then
  echo "Building scorer..."
  (cd scorer && cargo build)
fi

# Setup API venv
if [[ ! -d api/.venv ]]; then
  python3 -m venv api/.venv
  source api/.venv/bin/activate
  pip install -r api/requirements.txt -q
else
  source api/.venv/bin/activate
fi

export SCORER_BIN="$ROOT/scorer/target/debug/scorer"
export API_BASE_URL="http://127.0.0.1:8002"

# Start API
(cd api && uvicorn app.main:app --host 127.0.0.1 --port 8002) &
API_PID=$!
cleanup() { kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT

sleep 2

# Ingest transaction
TX_ID="e2e-$(date +%s)"
curl -sf -X POST "$API_BASE_URL/transactions" \
  -H "Content-Type: application/json" \
  -d "{\"contract_version\":\"1.0\",\"transaction_id\":\"$TX_ID\",\"user_id\":1,\"amount\":1000,\"type\":\"debit\",\"merchant\":\"e2e\"}"

# Run worker once
cd worker && node worker.js --once
cd "$ROOT"

# Verify scored
RESULT=$(curl -sf "$API_BASE_URL/transactions/$TX_ID")
echo "$RESULT" | grep -q '"status":"scored"'
echo "$RESULT" | grep -q '"risk_score"'

echo "e2e: PASSED for $TX_ID"
