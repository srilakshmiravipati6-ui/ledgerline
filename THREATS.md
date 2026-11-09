# Threat model and mitigations

## 1. Double-spend via race on a withdrawal

Threat: two withdrawal requests hit the same account at the same time and both read the same balance before either writes it.

Mitigation: each money-changing route starts a SQLite transaction with `BEGIN IMMEDIATE`, which obtains a write lock before the balance is checked and updated. The check and update are in the same transaction, so both requests cannot pass the same balance check.

## 2. Replay from a network retry or double-click

Threat: the same transfer or withdrawal is submitted twice with the same client key and the second attempt pays again.

Mitigation: the server stores a unique `client_key`, request fingerprint, actor, and prior response in the `idempotency_keys` table in the same transaction as the money move. An exact replay returns the first result; reuse with a different payload or actor returns `409`.

## 3. Overdrawn accounts

Threat: a valid request could drive an account negative by creating a balance below zero.

Mitigation: every withdrawal and transfer validates `new_balance >= -overdraft_limit` in the same transaction as the update. If not, the request is rejected and recorded as a `refused` ledger entry.

## 4. Unauthorized money movement

Threat: a user attempts to spend money from an account they do not own.

Mitigation: every money-changing request checks the live database role and source account owner before processing. Only administrators and the owning account holder can move funds; auditors are read-only. The service returns `403` for a forbidden operation.

## 5. Ledger tampering

Threat: a ledger row is altered or deleted to hide a payment.

Mitigation: database triggers reject ledger updates and deletes, and entries are hash-chained; each row stores the previous hash and its own hash. The `/ledger/verify` endpoint exposes the chain check.

## 6. Credential and token theft

Threat: a database reader obtains passwords, or a guessed signing key lets an attacker forge bearer tokens.

Mitigation: passwords are stored as salted PBKDF2 hashes. Production startup requires `LEDGERLINE_TOKEN_SECRET`; local development generates a random process secret. Demo credentials are published for local testing only and must be replaced before deployment.

## 7. Lost debit or credit

Threat: a transfer may debits one account while the credit to the destination is omitted due to a partial failure.

Mitigation: transfer logic is one database transaction that updates both balances and inserts both ledger rows together. A failure before commit rolls back the transaction, leaving both accounts unchanged.

## 8. Risks deliberately accepted

- The service uses a single SQLite database file rather than a distributed ledger or external transaction coordinator. This is intentionally small and is suitable for a single-process demo system, not a multi-region bank deployment.
- SQLite is suitable for this single-instance demonstration, not high-availability multi-instance production. External audit-log shipping, secret rotation, password reset, and account lifecycle workflows are not implemented.
- The user model is intentionally simple: ownership is tied to the account owner, and a single account has one owner. This keeps the authorization logic explicit and easy to audit.
