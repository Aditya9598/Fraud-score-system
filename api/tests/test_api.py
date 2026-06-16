import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    store.reset()
    yield
    store.reset()


def test_ingest_and_get_transaction():
    response = client.post(
        "/transactions",
        json={
            "contract_version": "1.0",
            "transaction_id": "tx-1",
            "user_id": 1,
            "amount": 500.0,
            "type": "debit",
            "merchant": "acme",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"

    get_resp = client.get("/transactions/tx-1")
    assert get_resp.status_code == 200


def test_status_lifecycle_to_scored():
    client.post(
        "/transactions",
        json={
            "contract_version": "1.0",
            "transaction_id": "tx-2",
            "user_id": 1,
            "amount": 1000.0,
            "type": "debit",
            "merchant": "acme",
        },
    )
    assert client.patch("/transactions/tx-2/claim").json()["status"] == "processing"
    score_resp = client.post(
        "/transactions/tx-2/score",
        json={
            "contract_version": "1.0",
            "transaction_id": "tx-2",
            "risk_score": 65,
            "risk_level": "medium",
            "reasons": ["high_amount"],
        },
    )
    assert score_resp.status_code == 200
    assert score_resp.json()["status"] == "scored"


def test_rejects_wrong_contract_version():
    response = client.post(
        "/transactions",
        json={
            "contract_version": "2.0",
            "transaction_id": "tx-3",
            "user_id": 1,
            "amount": 100.0,
            "type": "credit",
            "merchant": "acme",
        },
    )
    assert response.status_code == 400


def test_list_pending_only():
    client.post(
        "/transactions",
        json={
            "contract_version": "1.0",
            "transaction_id": "tx-a",
            "user_id": 1,
            "amount": 100.0,
            "type": "credit",
            "merchant": "a",
        },
    )
    client.post(
        "/transactions",
        json={
            "contract_version": "1.0",
            "transaction_id": "tx-b",
            "user_id": 1,
            "amount": 200.0,
            "type": "credit",
            "merchant": "b",
        },
    )
    client.patch("/transactions/tx-a/claim")
    pending = client.get("/transactions/pending").json()
    assert len(pending) == 1
    assert pending[0]["transaction_id"] == "tx-b"
