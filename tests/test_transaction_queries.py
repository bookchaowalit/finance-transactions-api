"""Listing, grouping and the lifecycle of a transaction."""

from transactions_helpers import TRANSACTIONS, create


def ids(response):
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def test_list_filters_by_transaction_type(client, owner):
    income = create(client, owner, transaction_type="income").json()
    create(client, owner, transaction_type="expense")
    listed = client.get(
        TRANSACTIONS, headers=owner, params={"transaction_type": "income"}
    )
    assert ids(listed) == [income["id"]]


def test_list_filters_by_account_id(client, owner):
    mine = create(client, owner, account_id=11).json()
    create(client, owner, account_id=12)
    create(client, owner)
    assert ids(client.get(TRANSACTIONS, headers=owner, params={"account_id": 11})) == [
        mine["id"]
    ]


def test_list_filters_by_category_and_owner_scope(client, owner):
    food = create(client, owner, category="food", owner_scope="client").json()
    create(client, owner, category="food", owner_scope="personal")
    create(client, owner, category="rent", owner_scope="client")
    listed = client.get(
        TRANSACTIONS,
        headers=owner,
        params={"category": "food", "owner_scope": "client"},
    )
    assert ids(listed) == [food["id"]]


def test_a_filter_can_list_several_values(client, owner):
    income = create(client, owner, transaction_type="income").json()
    refund = create(client, owner, transaction_type="refund").json()
    create(client, owner, transaction_type="fee")
    listed = client.get(
        TRANSACTIONS,
        headers=owner,
        params=[("transaction_type", "income"), ("transaction_type", "refund")],
    )
    assert sorted(ids(listed)) == sorted([income["id"], refund["id"]])


def test_an_unknown_filter_is_refused(client, owner):
    listed = client.get(TRANSACTIONS, headers=owner, params={"merchant": "Cafe"})
    assert listed.status_code == 422


def test_list_is_ordered_by_transaction_date_then_id(client, owner):
    late = create(client, owner, transaction_date="2026-10-20").json()
    early = create(client, owner, transaction_date="2026-09-01").json()
    same_a = create(client, owner, transaction_date="2026-10-05").json()
    same_b = create(client, owner, transaction_date="2026-10-05").json()
    assert ids(client.get(TRANSACTIONS, headers=owner)) == [
        early["id"],
        same_a["id"],
        same_b["id"],
        late["id"],
    ]
    newest_first = client.get(TRANSACTIONS, headers=owner, params={"order": "desc"})
    assert ids(newest_first) == [late["id"], same_b["id"], same_a["id"], early["id"]]


def test_stats_count_transactions_per_type(client, owner):
    create(client, owner, transaction_type="income")
    create(client, owner, transaction_type="expense")
    create(client, owner, transaction_type="expense")
    stats = client.get(
        f"{TRANSACTIONS}/stats", headers=owner, params={"group_by": "transaction_type"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"] == {"income": 1, "expense": 2}


def test_stats_count_transactions_per_account(client, owner):
    create(client, owner, account_id=7)
    create(client, owner, account_id=7)
    create(client, owner, account_id=8)
    stats = client.get(
        f"{TRANSACTIONS}/stats", headers=owner, params={"group_by": "account_id"}
    )
    assert stats.json()["groups"] == {"7": 2, "8": 1}


def test_stats_can_be_narrowed_by_another_filter(client, owner):
    create(client, owner, transaction_type="income", owner_scope="venture")
    create(client, owner, transaction_type="expense", owner_scope="personal")
    stats = client.get(
        f"{TRANSACTIONS}/stats",
        headers=owner,
        params={"group_by": "transaction_type", "owner_scope": "venture"},
    )
    assert stats.json()["groups"] == {"income": 1}


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    for field in ("amount", "merchant", "transaction_date", "currency"):
        stats = client.get(
            f"{TRANSACTIONS}/stats", headers=owner, params={"group_by": field}
        )
        assert stats.status_code == 422, field


def test_patching_a_transaction_bumps_its_version(client, owner):
    transaction = create(client, owner, amount=10).json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    changed = client.patch(
        path, headers=owner, json={"amount": 12.5, "category": "food"}
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["amount"] == 12.5
    assert changed.json()["category"] == "food"
    assert changed.json()["version"] == 2


def test_a_patch_that_changes_nothing_keeps_the_version(client, owner):
    transaction = create(client, owner, amount=10, category="food").json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    same = client.patch(path, headers=owner, json={"amount": 10, "category": "food"})
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1


def test_a_stale_expected_version_is_refused(client, owner):
    transaction = create(client, owner).json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    client.patch(path, headers=owner, json={"amount": 1})
    stale = client.patch(path, headers=owner, json={"amount": 2, "expected_version": 1})
    assert stale.status_code == 409, stale.text
    assert client.get(path, headers=owner).json()["amount"] == 1


def test_deleting_a_transaction_removes_it(client, owner):
    transaction = create(client, owner).json()
    path = f"{TRANSACTIONS}/{transaction['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
    assert ids(client.get(TRANSACTIONS, headers=owner)) == []


def test_a_transaction_that_does_not_exist_is_404(client, owner):
    assert client.get(f"{TRANSACTIONS}/999999999", headers=owner).status_code == 404
    patched = client.patch(
        f"{TRANSACTIONS}/999999999", headers=owner, json={"amount": 1}
    )
    assert patched.status_code == 404
    assert client.delete(f"{TRANSACTIONS}/999999999", headers=owner).status_code == 404
