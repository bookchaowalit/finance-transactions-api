# Review guide (finance-transactions-api)

The Codex Stop-hook review reads this file from the default branch, never from the change under
review. Owner-written; keep it under 16 KiB.

## What failure looks like here

Treat these as `[P0]`/`[P1]`:

- **Money**: `numeric(19,4)` returned as JSON strings; more than 4 decimals, NaN or Infinity -> 422;
  ISO 4217 currency enforced by a DB CHECK (`specs/003-saas-money-currency-scope/spec.md`).
- **Lost money edits**: a PATCH with a money field and no `expected_version` must get 428
  (`specs/009-money-patch-version/spec.md`).
- **Workspace isolation** through RLS (`migrations/0001_transactions.sql`); erase touches only the
  caller's workspace (`specs/008-workspace-erase/spec.md`).
- **References**: cross-cell references fail closed with 503 `references_unavailable`; a referenced
  record cannot be deleted (409 `has_dependents`) (`specs/006-cross-service-references/spec.md`).
- **Outbox**: written in the same transaction as the record; events carry no amounts or free text
  (`specs/005-finance-events-kafka/spec.md`).
- **Double recording**: only `Idempotency-Key` on create and the unique `legacy_id` (409) prevent
  duplicates; weakening either is `[P1]`.
- **Migrations**: append-only; an edited applied file, or code that needs a migration not yet applied
  in production (merges ship code only).

Merging to `main` deploys production; apply new migrations BEFORE the merge.

## Severity

- `[P0]` money wrong or stored inexactly, another workspace's rows reachable or erased, an edited applied migration.
- `[P1]` a create, patch or delete that ends in the wrong state or status code.
- `[P2]` edge case, or changed behaviour without a test.
- `[P3]` nit. **At most 3 nits.**

## Skip

- `uv.lock`, `package-lock.json`, `src/transactions.egg-info`, stale `src/cellkit/__pycache__`.
- Kit changes belong in platform-cellkit, never in `src/`: a kit file edited here is a finding.

## Evidence

Every finding gives `file:line` and input -> wrong result. No finding without evidence from the diff
or the code it calls. Start the summary with the count, e.g. `2 findings (1 P1, 1 P3)`.
