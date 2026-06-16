# A5 — Agent Code Review (Adversarial Verification)

**Project:** Fraud-score-system  
**Branch reviewed:** `review/agent-pr-seeded`  
**Date:** 2026-06-16

---

## Issue List

| # | Issue | Severity | Blocking |
|---|-------|----------|----------|
| 1 | Command injection via shell exec with JSON in args | **Critical** | **Yes** |
| 2 | Hardcoded `API_KEY` in worker source | **High** | **Yes** |
| 3 | No timeout on scorer subprocess | Medium | No |
| 4 | Skips `contract_version` validation | Medium | No |
| 5 | Missing test for `failed` status path | Low | No |

---

## Issue 1 — Command injection (Blocking)

**Seeded code (`review/agent-pr-seeded`):**
```javascript
exec(`"${scorerBin}" score --input '${JSON.stringify(transaction)}'`, ...)
```

**Risk:** Malicious merchant field with `'` breaks out of shell string.

**Safe fix on `main`:**
```javascript
spawn(scorerBin, ["score"], { stdio: ["pipe", "pipe", "pipe"] });
child.stdin.write(JSON.stringify(transaction));
```

**Verify:** `npm test` — `runScorer uses stdin pipe not shell`

---

## Issue 2 — Hardcoded secret (Blocking)

**Seeded:** `const API_KEY = "super-secret-key-12345";` in worker

**Fix:** Load from `.env` via `process.env.API_KEY`; never commit secrets.

**Verify:** `grep -r super-secret main` returns nothing

---

## Issue 3 — No scorer timeout (Non-blocking)

**Seeded:** subprocess hangs indefinitely on bad input.

**Fix on `main`:** `WORKER_SCORER_TIMEOUT_MS` with `setTimeout` kill — see [`worker/worker.js`](../../../worker/worker.js).

---

## Issue 4 — Missing contract_version check (Non-blocking)

**Seeded:** worker processes any payload.

**Fix on `main`:** reject and call `/fail` when `contract_version !== "1.0"`.

---

## Issue 5 — Missing failed-status test (Non-blocking)

**Fix:** add worker integration test simulating scorer exit code != 0.

---

## Agent vs Manual Verification

| Finding | Agent identified | Manually verified |
|---------|------------------|-------------------|
| Shell injection | Yes | Reviewed diff on seeded branch |
| Safe stdin spawn on main | Suggested | `npm test` pass |
| Hardcoded secret | Yes | grep on seeded branch |
