"""Shared helpers for the transactions domain tests."""

from typing import Any

TRANSACTIONS = "/v1/transactions"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "transaction_date": "2026-10-01",
        "transaction_type": "expense",
        "amount": 100.0,
        **fields,
    }
    return client.post(TRANSACTIONS, headers=owner, json=body)
