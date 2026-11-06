# API permissions and money effects

## Authentication

All authenticated endpoints require an Authorization header in the form `Bearer <token>`.

- Admin: can create accounts, inspect all balances, perform deposits and withdrawals, and audit ledger integrity.
- Account holder: can access their own accounts, deposit and withdraw from them, and transfer out of them.
- Auditor: can read accounts and statements but cannot alter balances or ledger rows.

## Endpoints

### POST /login

- Allowed roles: everyone with a valid username/password.
- Effect on money: none. It issues a bearer token used for subsequent requests.

### GET /accounts

- Allowed roles: admin, auditor, and each account holder for their own accounts.
- Effect on money: none. Lists current balances and account metadata.

### POST /accounts

- Allowed roles: admin only.
- Effect on money: creates a new account with a zero starting balance and a ledger entry marking the account creation.

### GET /accounts/{id}

- Allowed roles: admin, auditor, and the owning account holder.
- Effect on money: none. Returns the balance and account settings.

### GET /accounts/{id}/statement

- Allowed roles: admin, auditor, and the owning account holder.
- Effect on money: none. Returns all ledger rows for the account, including credits, debits, and refused attempts, with the running balance and actor username.

### POST /deposits

- Allowed roles: admin and the owning account holder.
- Effect on money: adds the amount to the account balance; inserts a `credit` ledger row and updates the running balance.

### POST /withdrawals

- Allowed roles: admin and the owning account holder.
- Effect on money: subtracts the amount if the resulting balance is above the overdraft floor; otherwise the request is rejected and written as a `refused` ledger entry.

### POST /transfers

- Allowed roles: admin and the owning account holder on the source account.
- Effect on money: debits the source account and credits the destination account in one transaction; if funds are insufficient the transfer is rejected and a `refused` row is recorded.

### GET /ledger/verify

- Allowed roles: admin and auditor.
- Effect on money: none. Confirms the ledger hash chain remains intact and append-only.

## Money invariants enforced

- Every transfer is one database transaction, so debits and credits are written together or not at all.
- No balance can go below zero unless a configured overdraft limit allows it.
- Idempotency keys are stored per client key so replayed requests return the original result without moving money again.
- The ledger is append-only and hash-chained to protect against silent edits.
