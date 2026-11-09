# LedgerLine

LedgerLine is a small money-movement service built to show that balances stay correct under retries and concurrent requests.

## Roles and permissions

- Administrator: create accounts, seed balances, view all accounts and statements, and inspect the append-only ledger integrity.
- Account holder: can view and modify only the accounts they own; they may deposit, withdraw, and transfer from those accounts.
- Auditor: read-only access to the whole ledger and account statements; may not move money.

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the service: `uvicorn app.main:app --reload`
4. Open the API docs at `http://localhost:8000/docs`

The dashboard signs in when you click the user panel and loads balances,
statements, and recent ledger entries from the API. The quick-action tiles submit
deposits, withdrawals, and transfers to the server; transaction details and
authorization are checked server-side.

## Database

LedgerLine uses SQLite, which is included with Python, so no database server or
additional package is required. On first startup, the app creates `ledger.db`
in the project root and seeds the example users, accounts, and opening ledger
entries. The database is local to this checkout and is excluded from Git.

Normal startup preserves account balances, ledger history, and idempotency
records. The app enables SQLite write-ahead logging and foreign-key checks.
Money is stored as integer amounts, and deposits, withdrawals, transfers, and
their ledger records are committed together. Tests use temporary database
files and do not modify the project database.

The schema has `users`, `accounts`, `ledger_entries`, and `idempotency_keys`
tables, with indexes for account ownership and statement lookup. Startup adds
the idempotency metadata columns to older databases and migrates legacy
plaintext passwords to salted PBKDF2 hashes without clearing account data.

See [DESIGN.md](./DESIGN.md) for the architecture, data model, transaction
flow, role matrix, integrity controls, validation, and operational limits.

## Seed users

These are demo-only credentials; change them before exposing the service:

- admin / adminpass
- alice / pass123
- bob / pass123
- auditor / pass123

For a deployment, set a persistent, high-entropy token secret and production
mode before starting the service:

```powershell
$env:LEDGERLINE_TOKEN_SECRET = "<generate-a-long-random-secret>"
$env:LEDGERLINE_ENV = "production"
$env:LEDGERLINE_ADMIN_PASSWORD = "<unique-password-at-least-12-characters>"
$env:LEDGERLINE_ALICE_PASSWORD = "<unique-password-at-least-12-characters>"
$env:LEDGERLINE_BOB_PASSWORD = "<unique-password-at-least-12-characters>"
$env:LEDGERLINE_AUDITOR_PASSWORD = "<unique-password-at-least-12-characters>"
uvicorn app.main:app
```

The application refuses to start in production mode without the token secret
and strong passwords for the demo users.
When running locally without one, a random development secret is generated;
tokens will be invalidated if the process restarts.

## Integrity model

- Every money event happens inside a database transaction and writes the account balance and ledger entry atomically.
- The balance check and the update happen in the same SQLite transaction with `BEGIN IMMEDIATE`, which serializes writes and prevents two withdrawals from overspending the same balance.
- Idempotency keys are stored with the original request fingerprint and actor so replaying the same request returns its result, while key reuse for a different request or user is rejected.
- Passwords use salted PBKDF2 hashes. Bearer tokens are signed and expire after one hour.
- The ledger is append-only (database triggers reject updates/deletes) and hash-chained; `/ledger/verify` and statement responses verify the chain.

## API summary

- POST /login - authenticate a user and return a bearer token.
- GET /me - return the authenticated user's username and role.
- GET /accounts - list accounts visible to the caller.
- POST /accounts - create an account (admin only).
- GET /accounts/{id} - view one account.
- GET /accounts/{id}/statement - view a ledger statement for one account.
- POST /deposits - add money to an account.
- POST /withdrawals - remove money from an account.
- POST /transfers - transfer money between two accounts.
- GET /ledger/verify - confirm the ledger hash chain remains valid.

## Security notes

This is a deliberately small system intended to demonstrate the integrity rules rather than a full banking platform. The server enforces account ownership on every move and the database transaction ensures the balance check and write happen together.
