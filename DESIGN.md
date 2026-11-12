# BalanceVault Technical Design (formerly LedgerLine)

## 1. System Scope & Technology Stack

BalanceVault is a secure, high-integrity financial transaction platform designed to guarantee mathematical conservation of money, idempotency, append-only ledger transparency, and concurrency safety.

- **Backend**: Python 3.10+, FastAPI, Starlette.
- **Database Layer**: SQLAlchemy, Alembic for schema migrations, psycopg2 for PostgreSQL, with dual-engine fallback to SQLite for lightweight local testing.
- **Caching & Throttling**: Redis with atomic counters and sliding-window rate limiting; in-memory fallback if Redis is unavailable.
- **Frontend Dashboard**: Single-page interactive HTML5 / CSS3 / JavaScript application served directly by FastAPI or deployable independently to static hosting (Vercel).
- **Authentication**: HMAC-SHA256 signed Bearer tokens (1-hour expiry); salted PBKDF2-HMAC-SHA256 password hashing.

---

## 2. Relational Data Model

### `users`
- `id`: Integer primary key (Auto-increment / Serial).
- `username`: String(80), unique, indexed.
- `password`: String(256), salted PBKDF2 hash.
- `role`: String(32) — `super_admin`, `account_holder`, or `auditor`.
- `email`: String(255), optional contact.
- `created_at`: BigInteger timestamp.

### `accounts`
- `id`: Integer primary key (Auto-increment / Serial).
- `name`: String(120), unique account title.
- `owner_username`: Foreign key referencing `users.username`, indexed.
- `balance`: BigInteger, whole-rupee units (64-bit integer prevents floating-point inaccuracy).
- `overdraft_limit`: BigInteger, non-negative credit cushion (default 0).
- `created_at`: BigInteger timestamp.

### `ledger_entries` (Append-Only Audit Log)
- `id`: Integer primary key.
- `account_id`: Foreign key referencing `accounts.id`, indexed.
- `kind`: `credit`, `debit`, or `refused`.
- `amount`: BigInteger transaction amount.
- `running_balance`: BigInteger balance after event posted.
- `description`: Text transaction narrative.
- `actor_user_id`: Integer ID of the initiating user.
- `request_key`: String(128) client-supplied idempotency key.
- `operation_id`: String(128) unique operation tracker.
- `actor_username`: String(80) username of initiator.
- `prev_hash`: String(64) SHA-256 of the prior ledger row.
- `hash_value`: String(64) SHA-256 of the current canonical row payload.
- `created_at`: BigInteger timestamp.

### `idempotency_keys`
- `client_key`: String(128) primary key.
- `response_json`: Text representation of original response.
- `actor_user_id`: Integer ID of the user who submitted the request.
- `request_hash`: String(64) SHA-256 fingerprint of the request payload.
- `created_at`: BigInteger timestamp.

---

## 3. Concurrency Safety & Row-Level Locking

Financial transactions require absolute isolation to prevent the double-spending problem (e.g., two concurrent withdrawals depleting the same initial balance).

- **PostgreSQL Row-Level Locking**: In PostgreSQL, `SELECT ... WHERE id = :id FOR UPDATE` acquires an exclusive lock on the target account row until transaction commit/rollback.
- **Deadlock Avoidance in Transfers**: Transfers between two accounts sort the account IDs deterministically (`ORDER BY id FOR UPDATE`) prior to acquiring locks. This guarantees that concurrent transfers in opposite directions (Account A -> B and Account B -> A) never cause database deadlocks.
- **SQLite Concurrency**: In SQLite test environments, `BEGIN IMMEDIATE` acquires a database-level write lock before checking balances.
- **Atomic Balance Updates**: Balances and their corresponding ledger entries are committed or rolled back in a single ACID transaction.

---

## 4. Cryptographic Hash-Chained Ledger

To prove that transaction records have not been altered or deleted:
1. Each row computes a canonical SHA-256 hash incorporating the previous row's hash (`prev_hash`), account ID, event kind, amount, running balance, actor, and request keys.
2. The `/ledger/verify` and `/accounts/{id}/statement` endpoints verify the integrity of this unbroken chain back to the `genesis` state.
3. Database triggers (`prevent_ledger_update` and `prevent_ledger_delete`) abort any SQL `UPDATE` or `DELETE` attempt.
4. Database role security revokes `UPDATE` and `DELETE` privileges on `ledger_entries` from the application user (`app_user`).

---

## 5. Rate Limiting & Denial-of-Service Protection

- Integrated Redis rate limiter with sliding window counters.
- Public/Authentication endpoints (`/auth/login`, `/auth/register`) are throttled to 10-15 requests per minute per IP.
- Financial transactions (`/deposits`, `/withdrawals`, `/transfers`) are throttled to 60 requests per minute.
- Returns `429 Too Many Requests` with a standard `Retry-After` header when thresholds are exceeded.
- Configurable fail-safe mode (`RATE_LIMIT_FAIL_SAFE=true`) ensures that transient Redis network interruptions do not disrupt legitimate banking operations.

---

## 6. Role-Based Access Control (RBAC)

A centralized authorization layer (`app/rbac.py`) evaluates incoming requests against role permissions:
- **`super_admin`**: Full administrative access (`users:create`, `accounts:create`, `accounts:read_all`, `ledger:verify`).
- **`account_holder`**: Access restricted strictly to owned accounts and authorized financial moves.
- **`auditor`**: Strict read-only inspection access across all accounts, statements, and ledger chains; forbidden from executing deposits, withdrawals, or transfers.
