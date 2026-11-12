# BalanceVault (formerly LedgerLine)

BalanceVault is an enterprise-grade financial ledger and money-movement platform designed to guarantee mathematical conservation of funds, double-entry accounting integrity, idempotency, and strict concurrency safety under distributed retries and concurrent operations.

---

## Key Capabilities & Architecture

- **PostgreSQL Database & Migrations**: Fully compatible with PostgreSQL (via SQLAlchemy & psycopg2) and automated schema migrations via Alembic. Dual-mode support enables zero-friction local SQLite development while enforcing production PostgreSQL constraints.
- **Append-Only Hash-Chained Ledger**: Every deposit, withdrawal, and transfer appends an immutable, cryptographic SHA-256 hash-chained entry to `ledger_entries`. Database triggers and PostgreSQL least-privilege roles block any `UPDATE` or `DELETE`.
- **Concurrency Safety & Overdraft Prevention**: Row-level locking (`SELECT ... FOR UPDATE` in PostgreSQL; serialized immediate write-locking in SQLite) prevents double-spending and enforces non-negative balances / overdraft limits. Deterministic lock ordering prevents deadlocks on concurrent bidirectional transfers.
- **Strict Idempotency Protection**: Client-provided idempotency keys (`client_key`) are bound to the authenticated actor and request payload fingerprint. Retries safely return cached results; reusing keys with altered inputs or actors triggers `409 Conflict`.
- **Redis Rate Limiting**: Built-in sliding-window / counter rate limiting powered by Redis (with safe in-memory fallback), returning `429 Too Many Requests` on abuse.
- **User Onboarding & Profile Management**: Self-service user registration (`POST /auth/register`), automatic personal account provisioning, salted PBKDF2 password hashing, and signed JWT token issuance.
- **Formal Role-Based Access Control (RBAC)**: Centralized backend permission engine with explicit privilege mappings for `super_admin`, `account_holder`, and `auditor`.
- **First-Admin Bootstrap Script**: Secure CLI utility (`scripts/bootstrap_admin.py`) for initializing production credentials without hardcoding seeds or exposing privileged users.
- **Database Roles & Security**: PostgreSQL least-privilege separation (`migration_user`, `app_user`, `auditor_user`).
- **Health & Readiness Checks**: Liveness (`GET /health`) and readiness (`GET /ready`) monitoring database and cache connectivity.

---

## Roles and Permissions Matrix

| Permission | Super Admin (`super_admin` / `admin`) | Account Holder (`account_holder`) | Auditor (`auditor`) |
| :--- | :---: | :---: | :---: |
| **Manage Users & Roles** | ✅ Yes | ❌ No | ❌ No |
| **Create Bank Accounts** | ✅ Yes | ❌ No | ❌ No |
| **Read All Accounts** | ✅ Yes | ❌ No (Own accounts only) | ✅ Yes (Read-only) |
| **Deposit / Withdraw** | ✅ Any account | ✅ Own accounts only | ❌ No |
| **Transfer Money** | ✅ Any source | ✅ Own source account only | ❌ No |
| **Read Account Statements** | ✅ All accounts | ✅ Own accounts only | ✅ All accounts |
| **Verify Cryptographic Ledger** | ✅ Yes | ❌ No | ✅ Yes |

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+
- (Optional) PostgreSQL and Redis

### 2. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start the Application
```bash
uvicorn app.main:app --reload --port 8000
```
Open your browser to:
- **Web Dashboard**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

---

## First-Admin Bootstrap Utility

In production, automatic seed accounts are disabled. Use the bootstrap utility to provision the initial super administrator:

```bash
# Interactive mode (prompts for password securely):
python scripts/bootstrap_admin.py

# Or via environment variables:
export ADMIN_USERNAME="superadmin"
export ADMIN_PASSWORD="your-strong-password-at-least-12-chars"
python scripts/bootstrap_admin.py
```
*Note: Duplicate execution is prevented; once an administrator exists, duplicate bootstraps are safely rejected.*

---

## Database Least-Privilege Roles (PostgreSQL)

Run `scripts/setup_db_roles.sql` as a PostgreSQL administrator to provision least-privilege database users:
- `migration_user`: DDL privileges for running Alembic migrations.
- `app_user`: DML privileges for runtime queries (`SELECT, INSERT, UPDATE` on accounts/users; `SELECT, INSERT` on ledger; **`UPDATE/DELETE` explicitly revoked on `ledger_entries`**).
- `auditor_user`: Strict `SELECT` read-only access for compliance and inspection.

---

## API Summary

### Authentication & Onboarding
- `POST /auth/register` — Self-service registration; provisions primary checking account.
- `POST /auth/login` (or `/login`) — Authenticates and returns Bearer token.
- `GET /auth/me` (or `/me`) — Returns authenticated user profile, role, and permissions.

### Accounts & Statements
- `GET /accounts` — List accounts visible to caller (filtered by RBAC).
- `POST /accounts` — Create an account (Super Admin only).
- `GET /accounts/{id}` — Retrieve account balance and overdraft limit.
- `GET /accounts/{id}/statement` — Retrieve chronological ledger statement and verify integrity.

### Money Operations (Idempotent & Atomic)
- `POST /deposits` — Add funds to account.
- `POST /withdrawals` — Remove funds; rejected with `refused` audit log if overdraft exceeded.
- `POST /transfers` — Move funds between accounts atomically in a single transaction.

### Audit & Observability
- `GET /ledger/verify` — Verifies SHA-256 hash chain across all historical ledger rows.
- `GET /health` — Liveness probe (returns 200 OK).
- `GET /ready` — Readiness probe (checks PostgreSQL and Redis connectivity).

---

## Automated Test Suite

Run the full automated test suite (concurrency, double-spend, idempotency, RBAC, rate limiting, health checks):

```bash
pytest -v
```

All 30 automated test cases pass with zero errors.
