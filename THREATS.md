# BalanceVault Threat Model & Security Mitigations (formerly LedgerLine)

## 1. Double-Spend via Race Condition on Concurrent Withdrawals
- **Threat**: Two simultaneous requests against the same account read the balance concurrently and both debit the account, causing funds to be spent twice.
- **Mitigation**: In PostgreSQL, every balance-changing route executes `SELECT ... FOR UPDATE`, obtaining an exclusive row-level lock before checking the balance. In SQLite, `BEGIN IMMEDIATE` acquires an immediate write lock. Check and update occur within the exact same ACID transaction.

## 2. Deadlock on Concurrent Bidirectional Transfers
- **Threat**: User A transfers to User B while User B simultaneously transfers to User A. Two concurrent transactions lock opposite accounts first, causing an unresolvable database deadlock.
- **Mitigation**: BalanceVault sorts all account IDs deterministically (`ORDER BY id FOR UPDATE`) prior to acquiring locks. Both transactions attempt to lock accounts in the exact same order, preventing cyclic wait conditions and deadlocks.

## 3. Network Retry & Replay Attacks
- **Threat**: A client or network proxy retries a withdrawal or transfer, causing money to be moved multiple times.
- **Mitigation**: Idempotency keys (`client_key`) are stored in `idempotency_keys` in the same transaction as the balance move, bound to the actor's user ID and a SHA-256 fingerprint of the request payload. Replays return the cached response; key reuse with modified inputs returns `409 Conflict`.

## 4. Unauthorized Account Access & Privilege Escalation
- **Threat**: A malicious user attempts to debit or transfer money from another user's account, or access administrative endpoints.
- **Mitigation**: Centralized RBAC (`app/rbac.py`) enforces strict permission checks on all backend endpoints. Financial operations verify that the authenticated user owns the source account or holds `super_admin` privilege. Auditors have read-only access.

## 5. Brute-Force & Denial-of-Service on Authentication & Transactions
- **Threat**: Credential stuffing attacks against `/auth/login` or transaction flooding against `/transfers`.
- **Mitigation**: Redis-backed rate limiting throttles authentication endpoints to 10-15 requests per minute per IP, and money endpoints to 60 requests per minute. Returns `429 Too Many Requests` with a `Retry-After` header.

## 6. Ledger Tampering & Audit Row Deletion
- **Threat**: A compromised account or rogue insider attempts to delete or alter historical ledger rows to conceal fraudulent activity.
- **Mitigation**:
  1. Each ledger entry contains a cryptographic SHA-256 hash chained to the prior entry's hash (`prev_hash`).
  2. Database triggers (`prevent_ledger_update` and `prevent_ledger_delete`) abort any update or deletion.
  3. PostgreSQL database roles enforce least privilege: `app_user` is granted only `SELECT` and `INSERT` on `ledger_entries`; `UPDATE` and `DELETE` are revoked at the database role level.

## 7. Credential Theft & Production Seeding Risks
- **Threat**: Passwords stolen via SQL injection or exposure of hardcoded administrative credentials.
- **Mitigation**:
  1. Passwords are saved exclusively as salted PBKDF2-HMAC-SHA256 hashes (240,000 iterations). Plaintext passwords are never stored.
  2. First administrator is provisioned via a dedicated bootstrap script (`scripts/bootstrap_admin.py`). Automatic production seeding of default credentials is disabled.
  3. Production environment requires `LEDGERLINE_TOKEN_SECRET` with high entropy.
