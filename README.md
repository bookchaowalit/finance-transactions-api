# finance-transactions-api
The Transactions cell: its own API (Railway, serverless) and its own Neon
database, first generated from `cell.yaml` (one of the ten finance
services split on 2026-10-12). It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `finance-transactions-api`, service `transactions-api` (Serverless) |
| Data | Neon project `finance-transactions-api`, database `transactions` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`transactions`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `transactions.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/transactions` | transaction | `account_id`, `category`, `transaction_type`, `owner_scope` |

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/transactions-db provision
npm install && railway config apply && railway up --ci --service transactions-api
railway scale --service transactions-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see `src/cellkit/_sentry.py`),
`TRANSACTIONS_DB_MODE=hosted`, `TRANSACTIONS_DB_URL_API`,
`TRANSACTIONS_JWT_PUBLIC_KEY_PEM`, `TRANSACTIONS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
