# Threat model and mitigations

## 1. Double-spend via race on a withdrawal

Threat: two withdrawal requests hit the same account at the same time and both read the same balance before either writes it.

Mitigation: each money-changing route starts a SQLite transaction with `BEGIN IMMEDIATE`, which obtains a write lock before the balance is checked and updated. The check and update are in the same transaction, so both requests cannot pass the same balance check.

## 2. Replay from a network retry or double-click

Threat: the same transfer or withdrawal is submitted twice with the same client key and the second attempt pays again.

Mitigation: the server stores a unique `client_key` and the prior response in the `idempotency_keys` table. If the same key is seen again, the API returns the first result without writing a second ledger posting.

## 3. Overdrawn accounts

Threat: a valid request could drive an account negative by creating a balance below zero.

Mitigation: every withdrawal and transfer validates `new_balance >= -overdraft_limit` in the same transaction as the update. If not, the request is rejected and recorded as a `refused` ledger entry.

## 4. Unauthorized money movement

Threat: a user attempts to spend money from an account they do not own.

Mitigation: every request validates the caller against the source account's `owner_username` before processing. The service returns `403` if the account is not permitted to the caller.

## 5. Ledger tampering

Threat: a ledger row is altered or deleted to hide a payment.

Mitigation: the ledger entries are append-only and hash-chained; each row stores the previous hash and its own hash. If someone changes an older row, the hash verification fails. The `/ledger/verify` endpoint exposes this check.

## 6. Lost debit or credit

Threat: a transfer may debits one account while the credit to the destination is omitted due to a partial failure.

Mitigation: transfer logic is one database transaction that updates both balances and inserts both ledger rows together. A failure before commit rolls back the transaction, leaving both accounts unchanged.

## 7. Risks deliberately accepted

- The service uses a single SQLite database file rather than a distributed ledger or external transaction coordinator. This is intentionally small and is suitable for a single-process demo system, not a multi-region bank deployment.
- There are no real bank-grade audit logs for external systems or secrets rotation. The app is intentionally focused on integrity and concurrency for a demonstrator.
- The user model is intentionally simple: ownership is tied to the account owner, and a single account has one owner. This keeps the authorization logic explicit and easy to audit.
