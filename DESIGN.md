# LedgerLine technical design

## Scope and stack

LedgerLine is a single-instance financial transaction demonstration built with
FastAPI, Python, SQLite, and a static HTML/CSS/JavaScript dashboard. SQLite is
the existing project database and is included with Python; no database server
or additional package is required. The dashboard keeps its current visual
design and calls the API for account data, statements, authentication, and
money operations.

The database file is `ledger.db` in the project root. Startup creates missing
tables and indexes, adds the actor and request-fingerprint columns to older
idempotency tables, migrates plaintext passwords to PBKDF2 hashes, and seeds
example data only where it is missing. Normal startup does not reset balances
or ledger history.

## Data model

- `users`: unique username, salted PBKDF2 password hash, and one of the
  `admin`, `account_holder`, or `auditor` roles.
- `accounts`: unique name, owner username, integer-rupee balance, and
  non-negative overdraft limit.
- `ledger_entries`: account, event kind (`credit`, `debit`, or `refused`),
  amount, running balance, description, actor, operation/request identifiers,
  timestamp, and previous/current SHA-256 chain hashes.
- `idempotency_keys`: unique client key, original response, actor, canonical
  request fingerprint, and creation time.

Indexes support owner-scoped account listing and account statement lookup.
SQLite foreign-key checks are enabled on database connections.

## Authentication and authorization

`POST /login` verifies PBKDF2 hashes and returns a one-hour HMAC-signed bearer
token. The current role and user identity are reloaded from the database for
each authenticated request; a role embedded in a token is not used as the
authorization source. `/me` returns the authenticated identity.

| Role | Read accounts/statements | Create accounts | Deposit/withdraw | Transfer | Verify ledger |
|---|---|---|---|---|---|
| Admin | All | Yes | Any account | Any source account | Yes |
| Account holder | Owned accounts | No | Owned accounts | Owned source account | No |
| Auditor | All | No | No | No | Yes |

Production mode requires `LEDGERLINE_TOKEN_SECRET` and unique configured
passwords of at least 12 characters for the seeded demo users. Local mode uses
documented demo credentials and a random, process-local token secret.

## Money operation flow

Deposits, withdrawals, and transfers validate positive whole-rupee amounts and
are processed inside `BEGIN IMMEDIATE` transactions. The balance check, balance
update, ledger append, and idempotency record commit or roll back together.
SQLite serializes writers, preventing concurrent withdrawals from spending the
same balance. Withdrawals and transfers below the account's overdraft floor
are refused without changing balances, and the refusal is appended to the
ledger.

Clients should send and reuse a `client_key` when retrying an operation. The
server binds each key to the authenticated user and operation fingerprint:
identical retries return the saved response, while reuse for another user or
different request returns `409 Conflict`. If a client omits the key, the API
generates one for that request; callers that need retry protection must supply
their own stable key.

## Audit integrity

Every event is serialized into a canonical payload and chained to the previous
ledger hash. `/ledger/verify` and account statements report whether the chain
verifies. Database triggers reject ledger updates and deletions. The ledger
records refused attempts as well as successful postings and includes the
initiating username and running balance.

## Validation

Run the automated suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover money conservation, duplicate retries and key conflicts, concurrent
withdrawals, account authorization, auditor read-only access, deposit/
withdrawal/transfer behavior, refused attempts, ledger integrity, password
hashing, and migration from the prior SQLite schema. Test cases use temporary
database files rather than the project database.

## Operational limits

This design targets a single application instance and a local SQLite database.
It is not a multi-instance/high-availability banking deployment. The repository
does not currently provide a deployed application URL, password-reset or
general user-provisioning flows, external audit-log shipping, or production
secret rotation. Demo credentials must not be used for a public deployment.
