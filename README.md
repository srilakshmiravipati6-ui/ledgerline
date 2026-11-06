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

## Seed users

- admin / adminpass
- alice / pass123
- bob / pass123
- auditor / pass123

## Integrity model

- Every money event happens inside a database transaction and writes the account balance and ledger entry atomically.
- The balance check and the update happen in the same SQLite transaction with `BEGIN IMMEDIATE`, which serializes writes and prevents two withdrawals from overspending the same balance.
- Idempotency keys are stored with a unique database key so a replayed client request returns the original result instead of moving money again.
- The ledger is append-only and hash-chained; a row cannot be edited without invalidating the chain. The `/ledger/verify` endpoint confirms the chain integrity.

## API summary

- POST /login - authenticate a user and return a bearer token.
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
