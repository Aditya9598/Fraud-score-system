from fastapi import FastAPI

from app.config import settings
from app.models import ScoreResult, Transaction, TransactionIngest
from app.store import store

app = FastAPI(title="Fraud Score API", version="1.0.0", debug=settings.debug)


@app.post("/transactions", response_model=Transaction, status_code=201)
def create_transaction(payload: TransactionIngest) -> Transaction:
    return store.add(payload)


@app.get("/transactions/pending", response_model=list[Transaction])
def list_pending() -> list[Transaction]:
    return store.list_pending()


@app.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str) -> Transaction:
    return store.get(transaction_id)


@app.patch("/transactions/{transaction_id}/claim", response_model=Transaction)
def claim_transaction(transaction_id: str) -> Transaction:
    return store.claim(transaction_id)


@app.post("/transactions/{transaction_id}/score", response_model=Transaction)
def submit_score(transaction_id: str, score: ScoreResult) -> Transaction:
    return store.submit_score(transaction_id, score)


@app.post("/transactions/{transaction_id}/fail", response_model=Transaction)
def fail_transaction(transaction_id: str) -> Transaction:
    return store.mark_failed(transaction_id)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
