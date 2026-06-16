# A1 — Multi-Worktree Parallel Plan

**Project:** Fraud-score-system  
**Feature:** Polyglot fraud-score pipeline (A3)  
**Date:** 2026-06-16

---

## Task Decomposition

| Lane | Directory | Deliverable |
|------|-----------|-------------|
| **scorer** | `scorer/` | Rust CLI: JSON stdin → score JSON stdout |
| **api** | `api/` | FastAPI ingestion, status lifecycle, score endpoints |
| **worker** | `worker/` | Node poller, spawn scorer via stdio pipe |

Lanes touch **disjoint directories** only during parallel work.

---

## Worktree / Branch Names

| Lane | Branch | Worktree path |
|------|--------|---------------|
| scorer | `lane/scorer` | `../Fraud-score-system-scorer` |
| api | `lane/api` | `../Fraud-score-system-api` |
| worker | `lane/worker` | merged on `integration/a3` |
| integration | `integration/a3` | main repo |

---

## Agent Prompts (one per lane)

**lane/scorer:**
> Build only `scorer/`. Read transaction JSON from **stdin** (`scorer score`), write score JSON to stdout. Validate `contract_version == "1.0"`. Match `shared/contract.json`. Run `cargo test`. Do not edit `api/` or `worker/`.

**lane/api:**
> Build only `api/`. FastAPI on port 8002. Implement contract from `shared/contract.json`. Status: pending → processing → scored | failed. Endpoints: POST /transactions, GET /transactions/{id}, GET /transactions/pending, PATCH claim, POST score, POST fail, GET /health. Do not edit `scorer/` or `worker/`.

**lane/worker:**
> Build only `worker/`. Poll API pending list. Claim as processing. Spawn `scorer score` with **stdio pipe** (never shell-exec JSON). Submit score or fail. Validate contract_version. Do not edit `api/` or `scorer/` source.

---

## Shared Constraints

- `shared/contract.json` is **read-only** during parallel lanes; `contract_version` must stay `"1.0"`
- All components validate `contract_version` on read/write
- API port **8002** only
- Secrets in `.env` only (gitignored); template in `.env.example`
- Lanes do not edit root `Makefile` or `scripts/e2e.sh` until `integration/a3`

### Avoiding contract drift

Every payload includes `"contract_version": "1.0"`. If one lane changes fields, it must bump version and notify all lanes — otherwise merge is blocked.

---

## Merge Order

```text
lane/scorer → lane/api → lane/worker → integration/a3 → main
```

```bash
git checkout -b integration/a3
git merge lane/scorer
git merge lane/api
git merge lane/worker
make test && make e2e
git checkout main && git merge integration/a3
```

---

## Conflict / Risk Plan

| Risk | Mitigation |
|------|------------|
| README / Makefile conflict | Only edit on `integration/a3` |
| Contract drift | Frozen v1.0 + validation in each lane |
| Worker before API ready | Merge api before worker |
| Scorer binary path | Document in `.env.example` as `SCORER_BIN` |

---

## Verification Plan

```bash
make test-scorer   # cargo test
make test-api      # pytest
make test-worker   # npm test
make test          # all three
make e2e           # full pipeline (A3)
```

Agent suggested vs manually verified: all commands run with captured output in A2/A3 docs.
