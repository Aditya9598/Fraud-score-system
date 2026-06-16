# Fraud-score-system

Polyglot mini fraud-score pipeline: **FastAPI** ingestion → **Node.js** worker → **Rust** scorer.

Separate project — not related to `transaction-ledger` or `currency-converter`.

## Structure

```
Fraud-score-system/
├── shared/contract.json   # contract v1.0
├── api/                   # FastAPI (port 8002)
├── worker/                # Node.js poller
├── scorer/                # Rust CLI (stdin JSON)
├── scripts/e2e.sh
├── Makefile
└── docs/eval/advanced/    # A1–A6 eval artifacts
```

## Contract

All payloads include `"contract_version": "1.0"`. Transaction status: `pending` → `processing` → `scored` | `failed`.

## Setup

```bash
# Rust scorer
source "$HOME/.cargo/env"
cd scorer && cargo build

# Python API
cd api && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # optional
```

## Run order (three terminals)

**Terminal 1 — API:**
```bash
cd api && source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

**Terminal 2 — Worker:**
```bash
cd worker && node worker.js
```

**Terminal 3 — Ingest:**
```bash
curl -X POST http://127.0.0.1:8002/transactions \
  -H "Content-Type: application/json" \
  -d '{"contract_version":"1.0","transaction_id":"tx-1","user_id":1,"amount":1000,"type":"debit","merchant":"acme"}'
```

**Scorer manually:**
```bash
echo '{"contract_version":"1.0","transaction_id":"tx-1","user_id":1,"amount":1000,"type":"debit","merchant":"acme"}' \
  | ./scorer/target/debug/scorer score
```

## Test

```bash
make test      # api + worker + scorer unit tests
make e2e       # full pipeline integration
```

## Eval docs

See [`docs/eval/advanced/`](docs/eval/advanced/) for A1–A6 deliverables.
