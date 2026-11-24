# Verify recipe (finance-transactions-api)

The `verify` skill follows this file. The checks are the ones CI runs (Python 3.12).

## Checks

```bash
# libpq reads these even when the fixtures pass a Unix socket: a set PGHOSTADDR can send the
# throwaway-cluster bootstrap and migrate to a real server. Clear them first.
unset PGHOST PGHOSTADDR PGPORT PGUSER PGPASSWORD PGDATABASE PGSERVICE PGSERVICEFILE PGPASSFILE \
      PGOPTIONS PGSSLMODE DATABASE_URL SENTRY_DSN
uv sync --frozen --all-extras --python 3.12
.venv/bin/mypy .
uvx ruff@0.17.1 check . && uvx ruff@0.17.1 format --check .
.venv/bin/pytest -q --cov --cov-report=
.venv/bin/coverage report --precision=2 --fail-under=68   # CI's gate: 67.75% fails
```

Tests use an embedded `pgserver` (Python 3.12 only) and a fake platform; never the hosted database.

## End to end

Exercise the change in process, not with a real server: a throwaway test under `tests/` (deleted
afterwards, never committed) that uses the kit fixtures `client` and `owner` (`cellkit.testing`). They
give a fresh migrated `pgserver`, a test-key JWT, a `FakePlatform` and drop the shell's
`TRANSACTIONS_KAFKA_*` / `_REFS_DATABASE_URL` / `_RELAY_DATABASE_URL`. Show `/health`, one authorized
read, and for money changes a 4-decimal amount accepted and a 5-decimal one refused (422). For a new
migration, say it must be applied with the migrator URI before the merge.

Do not start `transactions-api` from a shell: it takes `EMPIRE_PLATFORM_URL`, the JWT settings,
`TRANSACTIONS_DB_MODE`/`_DB_URL_*` and the Kafka/refs variables from that shell, and on a production
platform an authorized write creates a real execution. If a real server is unavoidable, first `unset
TRANSACTIONS_DB_MODE TRANSACTIONS_JWT_JWKS_URL TRANSACTIONS_JWT_IDENTITY_ISSUER
TRANSACTIONS_JWT_IDENTITY_JWKS_URL TRANSACTIONS_PUBLISHER_TOKEN TRANSACTIONS_REFS_DATABASE_URL
TRANSACTIONS_RELAY_DATABASE_URL SENTRY_DSN` and every `TRANSACTIONS_KAFKA_*` / `TRANSACTIONS_DB_URL_*`;
point `EMPIRE_PLATFORM_URL` at a loopback stub and the JWT at a throwaway key and test issuer; start,
bootstrap and migrate the local cluster yourself (the server does not); run it in the background, wait
for `127.0.0.1:3700/health`, and stop it afterwards.

## Never

- `transactions-db migrate` or `provision` with hosted settings from a working tree.
- `transactions-relay` with real secrets.
- `transactions-mcp` against a real API: `EMPIRE_MCP_READONLY=1` limits tools to list/get but still
  reads real data. Set `EMPIRE_TRANSACTIONS_API` to a test server, `EMPIRE_TOKEN` to a test token, and
  `EMPIRE_CLIENT_CONFIG` to an empty file so `client.env` and the `owner-mcp` token are not used.
- `railway up` / `railway config apply` from a working tree.
