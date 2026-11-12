# Prompt Log

## 2026-11-06 — Prompt 1
- What I asked the tool: "Create a FastAPI ledger service with account balances, auth, and money transfers."
- What it produced: a basic CRUD skeleton and starter routes.
- What was wrong: it was missing idempotency, atomic concurrency around balance updates, and a proper ledger hash chain.
- What I did instead: I wrote the integrity tests first and implemented the transactions and idempotency keys directly in the service logic.
- Commit: [initial implementation](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/b5b3365)

## 2026-11-06 — Prompt 2
- What I asked the tool: "Add balance safety so two withdrawals cannot overdraw the same account."
- What it produced: a naive check-then-update pattern with separate reads and writes.
- What was wrong: it allowed a race condition where both requests could see the same balance.
- What I did instead: I replaced it with `BEGIN IMMEDIATE` and performed the balance check and update inside the same transaction.
- Commit: [transaction safety fix](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/b5b3365)

## 2026-11-06 — Prompt 3
- What I asked the tool: "Model money moves with idempotency keys and duplicate detection."
- What it produced: a simple duplicate guard that could be bypassed by concurrent requests.
- What was wrong: it did not protect against a second request arriving while the first was still in flight.
- What I did instead: I stored the idempotency record in the same transaction as the balance update and used a unique key constraint to serialize duplicates.
- Commit: [idempotency fix](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/b5b3365)

## 2026-11-06 — Prompt 4
- What I asked the tool: "Add an append-only ledger with proof that a row cannot be quietly changed."
- What it produced: a ledger table without verification.
- What was wrong: it could be edited without any integrity check.
- What I did instead: I added a hash chain using `prev_hash` and `hash_value` and exposed the `/ledger/verify` endpoint for audits.
- Commit: [hash chain fix](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/b5b3365)

## 2026-11-06 — Prompt 5
- What I asked the tool: "Build a concise API and docs that describe who can do what."
- What it produced: generic routes without a clear permission model.
- What was wrong: the access matrix was not explicit enough for admin, account-holder, and auditor roles.
- What I did instead: I documented the roles and enforced them in the server code and README.
- Commit: [permission documentation](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/3703cc3)

## 2026-11-07 — Prompt 6
- What I asked the tool: "Compare the project with the official LedgerLine requirements and close gaps without redesigning the existing webpage."
- What it found: auditors could perform money operations, idempotency keys were not bound to actors or request contents, passwords were stored in plaintext, and dashboard figures and transactions were hardcoded.
- What I changed: enforced read-only auditor permissions, bound replay keys to request fingerprints and actors, hashed and migrated passwords, protected ledger rows from updates/deletes, wired the existing dashboard to live API data and actions, and expanded automated coverage and setup/security documentation.
- Commit: [integrity and dashboard wiring](https://github.com/srilakshmiravipati6-ui/ledgerline/commit/3703cc3)

## 2026-11-12 — Prompt 7 (BalanceVault Rebranding & Mandatory Requirements Extension)
- What I asked the tool: "Extend LedgerLine to BalanceVault, implementing all new mandatory requirements: PostgreSQL support with Alembic migrations, Redis rate limiting, user onboarding, centralized RBAC, first-admin bootstrap script, PostgreSQL database roles with least-privilege, deployment health checks, frontend rebranding, and deployment configurations."
- What it produced: A comprehensive architectural extension preserving 100% of the original financial integrity engine.
- What was implemented:
  1. **PostgreSQL + Dual-Engine Architecture**: SQLAlchemy models, Alembic migrations (`alembic/versions/`), and row-level locking (`SELECT ... FOR UPDATE` with deterministic lock ordering to prevent transfer deadlocks).
  2. **Redis Rate Limiting**: Built-in sliding-window limiter with in-memory fallback, returning HTTP 429 on abuse.
  3. **User Onboarding**: `POST /auth/register` with input validation, duplicate checks, and automatic personal checking account creation.
  4. **Formal RBAC**: `app/rbac.py` defining fine-grained permissions for `super_admin`, `account_holder`, and `auditor`.
  5. **First-Admin Bootstrap**: `scripts/bootstrap_admin.py` with secure credential handling and duplicate admin prevention.
  6. **PostgreSQL Roles**: `scripts/setup_db_roles.sql` defining `migration_user`, `app_user` (no update/delete on ledger), and `auditor_user`.
  7. **Health Checks**: `GET /health` and `GET /ready` probes.
  8. **Deployment Configuration**: `render.yaml` (Backend + PostgreSQL + Redis blueprint), `Procfile`, `vercel.json`, and `.env.example`.
  9. **Frontend Rebranding**: Updated `app/static/index.html` to BalanceVault (formerly LedgerLine) and added self-service user registration.
  10. **Test Coverage**: Expanded test suite to 30 automated tests covering all original and new functionality.
