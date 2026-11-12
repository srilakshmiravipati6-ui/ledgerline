# BalanceVault API Documentation (formerly LedgerLine)

All authenticated endpoints require an `Authorization` header formatted as `Bearer <token>`.

---

## 1. Authentication & Onboarding

### `POST /auth/register`
- **Description**: Registers a new account holder and automatically provisions their primary bank account.
- **Allowed Roles**: Public / Unauthenticated.
- **Rate Limit**: 10 requests / minute.
- **Request Body**:
  ```json
  {
    "username": "johndoe",
    "password": "SecurePassword123!",
    "email": "john@example.com",
    "initial_deposit": 500
  }
  ```
- **Responses**:
  - `200 OK`: User registered, primary account created, and bearer token returned.
  - `409 Conflict`: Username already registered.
  - `422 Unprocessable Entity`: Validation failure (username < 3 chars, password < 8 chars).

### `POST /auth/login` (and alias `POST /login`)
- **Description**: Authenticates existing credentials and issues a signed 1-hour Bearer token.
- **Allowed Roles**: Public / Unauthenticated.
- **Rate Limit**: 15 requests / minute.
- **Request Body**:
  ```json
  {
    "username": "johndoe",
    "password": "SecurePassword123!"
  }
  ```
- **Responses**:
  - `200 OK`: `{"token": "eyJ...", "user": {"id": 1, "username": "johndoe", "role": "account_holder", "permissions": [...]}}`
  - `401 Unauthorized`: Invalid credentials.

### `GET /auth/me` (and alias `GET /me`)
- **Description**: Returns authenticated user profile, assigned role, and permissions.
- **Allowed Roles**: Any authenticated user.
- **Responses**:
  - `200 OK`: User profile object.
  - `401 Unauthorized`: Missing or expired token.

---

## 2. Health & Observability

### `GET /health`
- **Description**: Liveness probe confirming API service availability.
- **Responses**:
  - `200 OK`: `{"status": "ok", "app": "BalanceVault", "version": "2.0.0", "timestamp": 1700000000}`

### `GET /ready`
- **Description**: Readiness probe testing PostgreSQL database and Redis connectivity.
- **Responses**:
  - `200 OK`: All critical infrastructure dependencies are operational.
  - `503 Service Unavailable`: Database unreachable (returns failure status without leaking credentials).

---

## 3. Account Management

### `GET /accounts`
- **Allowed Roles**: `super_admin`, `auditor`, and `account_holder` (account holders see only accounts they own).
- **Responses**:
  - `200 OK`: Array of accounts with current integer balances and overdraft limits.

### `POST /accounts`
- **Allowed Roles**: `super_admin` only.
- **Request Body**:
  ```json
  {
    "name": "Corporate Escrow",
    "owner_username": "johndoe",
    "overdraft_limit": 10000
  }
  ```
- **Responses**:
  - `200 OK`: Account created with zero balance and ledger creation event.
  - `403 Forbidden`: Caller lacks `accounts:create` permission.
  - `409 Conflict`: Account name already taken.

### `GET /accounts/{id}`
- **Allowed Roles**: `super_admin`, `auditor`, or the owning `account_holder`.
- **Responses**:
  - `200 OK`: Account details.
  - `403 Forbidden`: Attempting to inspect another user's account.
  - `404 Not Found`: Account does not exist.

### `GET /accounts/{id}/statement`
- **Allowed Roles**: `super_admin`, `auditor`, or the owning `account_holder`.
- **Responses**:
  - `200 OK`: Full chronological list of ledger events (`credit`, `debit`, `refused`), running balances, actors, and ledger hash validation flag.

---

## 4. Money Operations (Idempotent & Atomic)

Every money endpoint accepts a unique `client_key`. Retrying with an identical key and payload safely returns the prior response. Reusing a key with altered parameters or a different user returns `409 Conflict`.

### `POST /deposits`
- **Allowed Roles**: `super_admin` or the owning `account_holder`.
- **Request Body**:
  ```json
  {
    "account_id": 1,
    "amount": 1000,
    "description": "Salary payroll",
    "client_key": "dep-uuid-12345"
  }
  ```
- **Responses**:
  - `200 OK`: Funds added; running balance updated atomically.
  - `403 Forbidden`: Unauthorized user.

### `POST /withdrawals`
- **Allowed Roles**: `super_admin` or the owning `account_holder`.
- **Request Body**:
  ```json
  {
    "account_id": 1,
    "amount": 250,
    "description": "ATM cash withdrawal",
    "client_key": "with-uuid-12345"
  }
  ```
- **Responses**:
  - `200 OK` (`"result": "posted"`): Funds debited.
  - `200 OK` (`"result": "rejected"`, `"reason": "insufficient_funds"`): Exceeds overdraft floor; refused event logged to audit ledger.

### `POST /transfers`
- **Allowed Roles**: `super_admin` or the owning `account_holder` of the source account.
- **Request Body**:
  ```json
  {
    "from_account_id": 1,
    "to_account_id": 2,
    "amount": 300,
    "description": "Vendor invoice payment",
    "client_key": "xfer-uuid-12345"
  }
  ```
- **Responses**:
  - `200 OK` (`"result": "posted"`): Source account debited, destination account credited atomically in one database transaction.
  - `200 OK` (`"result": "rejected"`, `"reason": "insufficient_funds"`): Insufficient funds.

---

## 5. Ledger Integrity

### `GET /ledger/verify`
- **Allowed Roles**: `super_admin` and `auditor`.
- **Responses**:
  - `200 OK`: `{"hash_valid": true}` confirming the entire ledger hash chain from genesis to the latest event is unbroken.
