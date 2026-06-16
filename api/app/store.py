from fastapi import HTTPException

from app.models import (
    CONTRACT_VERSION,
    ScoreResult,
    Transaction,
    TransactionIngest,
    TransactionStatus,
)


class TransactionStore:
    def __init__(self) -> None:
        self._transactions: dict[str, Transaction] = {}

    def add(self, payload: TransactionIngest) -> Transaction:
        if payload.contract_version != CONTRACT_VERSION:
            raise HTTPException(status_code=400, detail="unsupported contract_version")

        if payload.transaction_id in self._transactions:
            raise HTTPException(status_code=409, detail="transaction_id already exists")

        txn = Transaction(
            contract_version=payload.contract_version,
            transaction_id=payload.transaction_id,
            user_id=payload.user_id,
            amount=payload.amount,
            type=payload.type,
            merchant=payload.merchant,
            status=TransactionStatus.PENDING,
        )
        self._transactions[payload.transaction_id] = txn
        return txn

    def get(self, transaction_id: str) -> Transaction:
        txn = self._transactions.get(transaction_id)
        if txn is None:
            raise HTTPException(status_code=404, detail="transaction not found")
        return txn

    def list_pending(self) -> list[Transaction]:
        return [
            txn
            for txn in self._transactions.values()
            if txn.status == TransactionStatus.PENDING
        ]

    def claim(self, transaction_id: str) -> Transaction:
        txn = self.get(transaction_id)
        if txn.status != TransactionStatus.PENDING:
            raise HTTPException(status_code=409, detail=f"cannot claim status {txn.status}")
        txn.status = TransactionStatus.PROCESSING
        return txn

    def submit_score(self, transaction_id: str, score: ScoreResult) -> Transaction:
        if score.contract_version != CONTRACT_VERSION:
            raise HTTPException(status_code=400, detail="unsupported contract_version")

        txn = self.get(transaction_id)
        if txn.status != TransactionStatus.PROCESSING:
            raise HTTPException(status_code=409, detail=f"cannot score status {txn.status}")

        txn.score = score
        txn.status = TransactionStatus.SCORED
        return txn

    def mark_failed(self, transaction_id: str) -> Transaction:
        txn = self.get(transaction_id)
        if txn.status not in (TransactionStatus.PENDING, TransactionStatus.PROCESSING):
            raise HTTPException(status_code=409, detail=f"cannot fail status {txn.status}")
        txn.status = TransactionStatus.FAILED
        return txn

    def reset(self) -> None:
        self._transactions.clear()


store = TransactionStore()
