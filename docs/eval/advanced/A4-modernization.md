# A4 — Repository Modernization

**Project:** Fraud-score-system  
**Date:** 2026-06-16

---

## Findings (with evidence)

| Finding | Evidence | Priority |
|---------|----------|----------|
| Unpinned Python dependencies | [`api/requirements.txt`](../../../api/requirements.txt) used `>=` ranges | **P1 — fixed** |
| In-memory store only | [`api/app/store.py`](../../../api/app/store.py) — dict, no DB | P3 — documented |
| Worker URL from env with default | [`worker/worker.js`](../../../worker/worker.js) L26 | P2 — acceptable for demo |
| No structured logging | API uses FastAPI defaults | P3 — future |

---

## Prioritised Plan

1. **Pin Python deps** (implemented) — reproducible installs, zero behavior change
2. Add `pyproject.toml` / lockfile — future
3. PostgreSQL persistence — future
4. Structured logging — future

---

## First Step Implemented

**Change:** Pin exact versions in `api/requirements.txt`.

**Before:**
```text
fastapi>=0.110.0
...
```

**After (Python 3.14 compatible pins):**
```text
fastapi==0.137.1
uvicorn==0.49.0
pydantic==2.13.4
pydantic-settings==2.14.1
python-dotenv==1.2.2
pytest==9.1.0
httpx==0.28.1
```

---

## Verification

```bash
cd api && pip install -r requirements.txt && pytest -v
make test
```

```
4 passed (api), 3 passed (scorer), 1 passed (worker)
```

---

## Rollback

```bash
git revert <commit-sha>
pip install -r requirements.txt
pytest -v
```

Restores unpinned `>=` ranges.
