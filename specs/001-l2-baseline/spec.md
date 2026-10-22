# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/finance-transactions-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, and the only tests were the generic contract suite, so none of the transactions rules (non-negative amounts, known types, filters, ordering) were proven; no behaviour bug was found.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An amount cannot be negative

- **Given** an owner with write permission
- **When** they create a transaction with amount -0.01, then with amount 0
- **Then** the first is refused with 422 and the second is created
- **Test:** `tests/test_transaction_validation.py::test_amount_cannot_be_negative` · level: integration (API + throwaway PostgreSQL)

### AC-02 — A transaction needs a date, a type and an amount

- **Given** a create body missing one of the three
- **When** it is posted
- **Then** the API answers 422 for each missing field
- **Test:** `tests/test_transaction_validation.py::test_a_transaction_needs_its_date_type_and_amount` · level: integration (API + throwaway PostgreSQL)

### AC-03 — The type must be a known kind

- **Given** types income, expense, transfer, refund, fee and adjustment
- **When** a transaction is created with type gift
- **Then** it is refused with 422 and every listed type is accepted
- **Test:** `tests/test_transaction_validation.py::test_transaction_type_must_be_a_known_kind` · level: integration (API + throwaway PostgreSQL)

### AC-04 — New transactions default to personal, THB, manual

- **Given** a create request with only date, type and amount
- **When** the transaction is created
- **Then** owner_scope is personal, currency is THB, source is manual and version is 1
- **Test:** `tests/test_transaction_defaults.py::test_new_transaction_defaults_to_personal_thb_manual` · level: integration (API + throwaway PostgreSQL)

### AC-05 — Account and subscription ids are plain numbers

- **Given** ids that exist in no other service
- **When** a transaction is created with them
- **Then** it is created, because they are not foreign keys
- **Test:** `tests/test_transaction_defaults.py::test_account_and_subscription_ids_are_not_checked_against_other_services` · level: integration (API + throwaway PostgreSQL)

### AC-06 — An import keeps the old id

- **Given** a create request with legacy_id 4242
- **When** it is posted, then posted again
- **Then** the record has id 4242 and is found by legacy id; the repeat is 409
- **Test:** `tests/test_transaction_defaults.py::test_an_import_keeps_the_old_id` · level: integration (API + throwaway PostgreSQL)

### AC-07 — The list is ordered by transaction date

- **Given** transactions dated out of order, two on the same day
- **When** the owner lists them, ascending then descending
- **Then** they come back by date then id, and reversed with order=desc
- **Test:** `tests/test_transaction_queries.py::test_list_is_ordered_by_transaction_date_then_id` · level: integration (API + throwaway PostgreSQL)

### AC-08 — Stats group only by a declared filter

- **Given** income and expense transactions
- **When** the owner asks for stats grouped by transaction_type, then by amount
- **Then** counts per type are returned and grouping by a non-filter field is refused with 422
- **Test:** `tests/test_transaction_queries.py::test_stats_refuse_a_field_that_is_not_a_filter` · level: integration (API + throwaway PostgreSQL)

### AC-09 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `/v1/*` (all resources) | unchanged | same routes and payloads; see README |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "55"` (measured 57.48% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_transaction_validation.py::test_amount_cannot_be_negative` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-02 | `tests/test_transaction_validation.py::test_a_transaction_needs_its_date_type_and_amount` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-03 | `tests/test_transaction_validation.py::test_transaction_type_must_be_a_known_kind` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_transaction_defaults.py::test_new_transaction_defaults_to_personal_thb_manual` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_transaction_defaults.py::test_account_and_subscription_ids_are_not_checked_against_other_services` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_transaction_defaults.py::test_an_import_keeps_the_old_id` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_transaction_queries.py::test_list_is_ordered_by_transaction_date_then_id` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_transaction_queries.py::test_stats_refuse_a_field_that_is_not_a_filter` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-09 | `tests/test_contract.py::test_numbers_fit_their_columns` | 454ba2b · `.venv/bin/pytest -q -k numbers_fit` · `ValueError: Out of range float values are not JSON compliant: nan` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
