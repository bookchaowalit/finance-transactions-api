# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through `life-dashboard-web` (finance pages, which reach the cell through
  `EMPIRE_TRANSACTIONS_API`), `finance-portfolio-web` (reads `/api/finance/v1/transactions`), the
  cell's own MCP server (`transactions-mcp`) and the hosted tool hub (`platform-mcp-remote-worker`).
- Automations with an `empire-platform` token, within the permissions
  `transactions.transaction:read|write|delete`.
- The cell points at other services by plain ids: `account_id` (`finance-accounts-api`) and
  `subscription_id` (`finance-subscriptions-api`). Other consumers beyond these [ต้องยืนยัน].

## Product Purpose

The ledger of money in and out: one record per income, expense, transfer, refund, fee or
adjustment, with its date, amount, currency, owner scope, category and merchant, and the account
and subscription it belongs to.

Success: every movement of money is recorded once with a non-negative amount and a known type,
and it can be listed by account, category, type or owner scope.

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://transactions-api-production-4078.up.railway.app` (`/health`), deployed by
  merging to `main` after CI.
- Data starts empty (created 2026-10-12 from the retired `finance_*` tables' fields); imports keep
  old ids in `legacy_id`.
- Monitored by `platform-uptime-worker`; errors go to Sentry when `SENTRY_DSN` is set.

## Capabilities and Constraints

- `/v1/transactions`: list (filters `account_id`, `category`, `transaction_type`, `owner_scope`;
  ordered by `transaction_date`, then id; `order=desc` reverses), stats (`group_by` one of those
  filters), get, get-by-legacy-id, create (with `Idempotency-Key`), patch (with
  `expected_version`), delete.
- Rules: `transaction_date`, `transaction_type` and `amount` are required; `transaction_type` is
  one of income, expense, transfer, refund, fee, adjustment; `amount` cannot be negative (zero is
  allowed, the direction comes from the type); `currency` defaults to THB and is at most 12
  characters; `owner_scope` is personal, solo_empire, venture, client or shared (default
  personal); `source` defaults to `manual`; `metadata` is a JSON object; unknown fields are
  refused.
- No uniqueness rule: the same payment can be recorded twice. `account_id` and `subscription_id`
  are not foreign keys and are not checked against the other services.
- An import (`legacy_id`) keeps the old id and may carry the original `created_at`/`updated_at`;
  a repeated `legacy_id` is a 409.
- Out of scope: balances (computed by readers from these records), bank connections, currency
  conversion and payments.

## Measures

Proposed (nothing collects them yet):

- Transactions created per week, by `source`.
- Transactions with an `account_id` that `finance-accounts-api` no longer resolves (target: 0).
- 5xx rate and p95 latency on `/v1/transactions` (uptime worker and Sentry).
