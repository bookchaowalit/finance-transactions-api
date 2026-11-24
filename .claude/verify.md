# Verify recipe (finance-transactions-api)

The `verify` skill follows this file. The checks are the ones CI runs.

## Checks

```bash
uv sync --frozen --all-extras
.venv/bin/mypy .
uvx ruff@0.17.1 check . && uvx ruff@0.17.1 format --check .
.venv/bin/pytest -q --cov --cov-fail-under=68
```

Tests use an embedded `pgserver` (Python 3.12) and a fake platform; never the hosted database.

## End to end

`transactions-api` runs on a local cluster unless `TRANSACTIONS_DB_MODE=hosted` (leave it unset),
then `curl -fsS localhost:3700/health` and one authorized read. For money changes, show a 4-decimal
amount accepted and a 5-decimal one refused (422). For a new migration, say it must be applied with
the migrator URI before the merge.

## Never

- `transactions-db migrate` or `provision` with hosted settings from a working tree.
- `transactions-relay` with real secrets; `transactions-mcp` with a real `EMPIRE_TOKEN`
  (use `EMPIRE_MCP_READONLY=1`).
- `railway up` / `railway config apply` from a working tree.
