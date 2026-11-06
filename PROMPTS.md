# Prompt log

## 2026-11-06 — Prompt 1

- What I asked the tool: "Create a FastAPI ledger service with account balances, auth, and money transfers."
- What it produced: a basic CRUD skeleton and starter routes.
- What was wrong: it was missing idempotency, atomic concurrency around balance updates, and a proper ledger hash chain.
- What I did instead: I wrote the integrity tests first and implemented the transactions and idempotency keys directly in the service logic.
- Commit: [initial implementation](https://example.invalid/commit/1)

## 2026-11-06 — Prompt 2

- What I asked the tool: "Add balance safety so two withdrawals cannot overdraw the same account."
- What it produced: a naive check-then-update pattern with separate reads and writes.
- What was wrong: it allowed a race condition where both requests could see the same balance.
- What I did instead: I replaced it with `BEGIN IMMEDIATE` and performed the balance check and update inside the same transaction.
- Commit: [transaction safety fix](https://example.invalid/commit/2)

## 2026-11-06 — Prompt 3

- What I asked the tool: "Model money moves with idempotency keys and duplicate detection."
- What it produced: a simple duplicate guard that could be bypassed by concurrent requests.
- What was wrong: it did not protect against a second request arriving while the first was still in flight.
- What I did instead: I stored the idempotency record in the same transaction as the balance update and used a unique key constraint to serialize duplicates.
- Commit: [idempotency fix](https://example.invalid/commit/3)

## 2026-11-06 — Prompt 4

- What I asked the tool: "Add an append-only ledger with proof that a row cannot be quietly changed."
- What it produced: a ledger table without verification.
- What was wrong: it could be edited without any integrity check.
- What I did instead: I added a hash chain using `prev_hash` and `hash_value` and exposed the `/ledger/verify` endpoint for audits.
- Commit: [hash chain fix](https://example.invalid/commit/4)

## 2026-11-06 — Prompt 5

- What I asked the tool: "Build a concise API and docs that describe who can do what."
- What it produced: generic routes without a clear permission model.
- What was wrong: the access matrix was not explicit enough for admin, account-holder, and auditor roles.
- What I did instead: I documented the roles and enforced them in the server code and README.
- Commit: [permission documentation](https://example.invalid/commit/5)

> The example commit links are placeholders because this workspace is being initialized in-place; they are replaced with actual git commit hashes after the repository is created and committed.
