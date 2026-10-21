"""What transactions refuses: missing fields, unknown kinds, negative amounts, wrong shapes."""

import pytest
from transactions_helpers import TRANSACTIONS, create


@pytest.mark.parametrize("missing", ["transaction_date", "transaction_type", "amount"])
def test_a_transaction_needs_its_date_type_and_amount(client, owner, missing):
    body = {
        "transaction_date": "2026-10-01",
        "transaction_type": "expense",
        "amount": 50.0,
    }
    del body[missing]
    response = client.post(TRANSACTIONS, headers=owner, json=body)
    assert response.status_code == 422, response.text


def test_transaction_type_must_be_a_known_kind(client, owner):
    assert create(client, owner, transaction_type="gift").status_code == 422
    for kind in ("income", "expense", "transfer", "refund", "fee", "adjustment"):
        response = create(client, owner, transaction_type=kind)
        assert response.status_code == 201, response.text


def test_amount_cannot_be_negative(client, owner):
    assert create(client, owner, amount=-0.01).status_code == 422
    assert create(client, owner, amount=0).status_code == 201


def test_amount_must_be_a_number(client, owner):
    assert create(client, owner, amount="a lot").status_code == 422


def test_transaction_date_must_be_a_real_date(client, owner):
    assert create(client, owner, transaction_date="2026-13-40").status_code == 422
    assert create(client, owner, transaction_date="yesterday").status_code == 422


def test_currency_code_is_at_most_12_characters(client, owner):
    assert create(client, owner, currency="C" * 13).status_code == 422
    assert create(client, owner, currency="USD").status_code == 201


def test_owner_scope_must_be_a_known_scope(client, owner):
    assert create(client, owner, owner_scope="nobody").status_code == 422
    for scope in ("personal", "solo_empire", "venture", "client", "shared"):
        assert create(client, owner, owner_scope=scope).status_code == 201


def test_metadata_must_be_an_object(client, owner):
    assert create(client, owner, metadata=["a", "list"]).status_code == 422
    assert create(client, owner, metadata="text").status_code == 422
    assert create(client, owner, metadata={"receipt": "r-1"}).status_code == 201


def test_account_id_must_be_a_whole_number(client, owner):
    assert create(client, owner, account_id="main-account").status_code == 422
    assert create(client, owner, account_id=1.5).status_code == 422


def test_a_transaction_cannot_carry_fields_the_cell_does_not_know(client, owner):
    assert create(client, owner, tip=3).status_code == 422


def test_a_new_record_cannot_set_its_own_timestamps(client, owner):
    response = create(client, owner, created_at="2020-01-01T00:00:00+00:00")
    assert response.status_code == 422, response.text


def test_update_refuses_the_same_bad_values(client, owner):
    transaction = create(client, owner).json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    assert client.patch(path, headers=owner, json={"amount": -5}).status_code == 422
    kind = client.patch(path, headers=owner, json={"transaction_type": "gift"})
    assert kind.status_code == 422
    assert client.patch(path, headers=owner, json={"metadata": [1]}).status_code == 422
    assert client.get(path, headers=owner).json()["version"] == 1


def test_a_required_field_cannot_be_cleared(client, owner):
    transaction = create(client, owner).json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    cleared = client.patch(path, headers=owner, json={"transaction_date": None})
    assert cleared.status_code == 422, cleared.text
    assert client.get(path, headers=owner).json()["transaction_date"] == "2026-10-01"
