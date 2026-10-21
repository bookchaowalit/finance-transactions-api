"""Defaults and duplicates of a transaction."""

from datetime import UTC, datetime

from transactions_helpers import TRANSACTIONS, create


def test_new_transaction_defaults_to_personal_thb_manual(client, owner):
    response = create(client, owner)
    assert response.status_code == 201, response.text
    transaction = response.json()
    assert transaction["currency"] == "THB"
    assert transaction["owner_scope"] == "personal"
    assert transaction["source"] == "manual"
    assert transaction["version"] == 1
    assert transaction["account_id"] is None
    assert transaction["subscription_id"] is None


def test_defaults_can_be_overridden(client, owner):
    transaction = create(
        client, owner, currency="USD", owner_scope="venture", source="import"
    ).json()
    assert transaction["currency"] == "USD"
    assert transaction["owner_scope"] == "venture"
    assert transaction["source"] == "import"


def test_the_same_payment_can_be_recorded_twice(client, owner):
    first = create(client, owner, merchant="Cafe", amount=80)
    second = create(client, owner, merchant="Cafe", amount=80)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]


def test_account_and_subscription_ids_are_not_checked_against_other_services(
    client, owner
):
    response = create(client, owner, account_id=987654321, subscription_id=123456789)
    assert response.status_code == 201, response.text
    assert response.json()["account_id"] == 987654321
    assert response.json()["subscription_id"] == 123456789


def test_amount_keeps_its_decimal_value(client, owner):
    assert create(client, owner, amount=1234.56).json()["amount"] == 1234.56


def test_an_import_keeps_the_old_id(client, owner):
    imported = create(client, owner, legacy_id=4242, merchant="Old shop")
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 4242
    assert imported.json()["legacy_id"] == 4242
    found = client.get(f"{TRANSACTIONS}/legacy/4242", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["merchant"] == "Old shop"
    assert create(client, owner, legacy_id=4242).status_code == 409


def test_an_import_may_carry_its_original_timestamps(client, owner):
    imported = create(
        client,
        owner,
        legacy_id=4243,
        created_at="2020-01-02T03:04:05+00:00",
        updated_at="2020-02-03T04:05:06+00:00",
    )
    assert imported.status_code == 201, imported.text
    created = datetime.fromisoformat(imported.json()["created_at"])
    updated = datetime.fromisoformat(imported.json()["updated_at"])
    assert created == datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert updated == datetime(2020, 2, 3, 4, 5, 6, tzinfo=UTC)
