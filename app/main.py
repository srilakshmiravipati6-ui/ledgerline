from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "ledger.db"
TOKEN_SECRET = os.environ.get("LEDGERLINE_TOKEN_SECRET")
if not TOKEN_SECRET and os.environ.get("LEDGERLINE_ENV") == "production":
    raise RuntimeError("LEDGERLINE_TOKEN_SECRET must be set in production")
if not TOKEN_SECRET:
    TOKEN_SECRET = secrets.token_urlsafe(32)

app = FastAPI(title="LedgerLine", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
security = HTTPBearer(auto_error=False)


class UserRole:
    ADMIN = "admin"
    ACCOUNT_HOLDER = "account_holder"
    AUDITOR = "auditor"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AccountCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    owner_username: str = Field(min_length=1, max_length=80)
    overdraft_limit: int = Field(default=0, ge=0, strict=True)


class MoneyRequest(BaseModel):
    account_id: int = Field(gt=0, strict=True)
    amount: int = Field(gt=0, strict=True)
    description: str = Field(default="", max_length=500)
    client_key: str = Field(default_factory=lambda: f"auto-{uuid.uuid4().hex}", min_length=1, max_length=128)


class TransferRequest(BaseModel):
    from_account_id: int = Field(gt=0, strict=True)
    to_account_id: int = Field(gt=0, strict=True)
    amount: int = Field(gt=0, strict=True)
    description: str = Field(default="", max_length=500)
    client_key: str = Field(default_factory=lambda: f"auto-{uuid.uuid4().hex}", min_length=1, max_length=128)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 240_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password, stored_password)
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def tokenise(username: str, role: str) -> str:
    payload = {"sub": username, "role": role, "exp": int(time.time()) + 3600}
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).decode("utf-8").rstrip("=")
    digest = hmac.new(TOKEN_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return f"{body}.{sig}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        body, sig = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Malformed token") from exc
    expected_sig = base64.urlsafe_b64encode(hmac.new(TOKEN_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()).decode("utf-8").rstrip("=")
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid token signature")
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token payload") from exc
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("sub"), str)
        or not isinstance(payload.get("exp"), int)
        or payload["exp"] < time.time()
    ):
        raise HTTPException(status_code=401, detail="Token is expired")
    return payload


def current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    payload = decode_token(credentials.credentials)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (payload["sub"],)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="User not recognised")
    return dict(row)


def require_admin(user: dict[str, Any]) -> None:
    if user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Administrator only")


def account_for_user(user: dict[str, Any], account_id: int, *, require_owner: bool = False) -> sqlite3.Row:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if user["role"] in (UserRole.ADMIN, UserRole.AUDITOR):
        return row
    if require_owner and row["owner_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not permitted to modify this account")
    if row["owner_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not permitted to access this account")
    return row


def get_last_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT hash_value FROM ledger_entries ORDER BY id DESC LIMIT 1").fetchone()
    return row["hash_value"] if row else "genesis"


def append_ledger_event(conn: sqlite3.Connection, *, account_id: int, kind: str, amount: int, running_balance: int, description: str, actor_user: dict[str, Any], request_key: str, operation_id: str) -> str:
    prev_hash = get_last_hash(conn)
    payload = {
        "account_id": account_id,
        "kind": kind,
        "amount": amount,
        "running_balance": running_balance,
        "description": description,
        "actor_user_id": actor_user["id"],
        "request_key": request_key,
        "operation_id": operation_id,
        "actor_username": actor_user["username"],
        "prev_hash": prev_hash,
    }
    row_hash = hash_payload(payload)
    conn.execute(
        "INSERT INTO ledger_entries (account_id, kind, amount, running_balance, description, actor_user_id, request_key, operation_id, actor_username, prev_hash, hash_value, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            account_id,
            kind,
            amount,
            running_balance,
            description,
            actor_user["id"],
            request_key,
            operation_id,
            actor_user["username"],
            prev_hash,
            row_hash,
            int(time.time()),
        ),
    )
    return row_hash


def read_idempotency(
    conn: sqlite3.Connection, client_key: str, actor_user_id: int, request_hash: str
) -> Optional[dict[str, Any]]:
    row = conn.execute(
        "SELECT response_json, actor_user_id, request_hash FROM idempotency_keys WHERE client_key = ?",
        (client_key,),
    ).fetchone()
    if row is None:
        return None
    if row["actor_user_id"] != actor_user_id or row["request_hash"] != request_hash:
        raise HTTPException(status_code=409, detail="Idempotency key cannot be reused")
    data = json.loads(row["response_json"])
    data["idempotent"] = True
    return data


def verify_ledger_chain() -> bool:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM ledger_entries ORDER BY id ASC").fetchall()
    prev_hash = "genesis"
    for row in rows:
        payload = {
            "account_id": row["account_id"],
            "kind": row["kind"],
            "amount": row["amount"],
            "running_balance": row["running_balance"],
            "description": row["description"],
            "actor_user_id": row["actor_user_id"],
            "request_key": row["request_key"],
            "operation_id": row["operation_id"],
            "actor_username": row["actor_username"],
            "prev_hash": row["prev_hash"],
        }
        if row["prev_hash"] != prev_hash:
            return False
        if row["hash_value"] != hash_payload(payload):
            return False
        prev_hash = row["hash_value"]
    return True


def init_db(reset: bool = False) -> None:
    production_mode = os.environ.get("LEDGERLINE_ENV") == "production"
    if production_mode:
        if not os.environ.get("LEDGERLINE_TOKEN_SECRET"):
            raise RuntimeError("LEDGERLINE_TOKEN_SECRET must be set in production")
        required_passwords = {
            "admin": os.environ.get("LEDGERLINE_ADMIN_PASSWORD"),
            "alice": os.environ.get("LEDGERLINE_ALICE_PASSWORD"),
            "bob": os.environ.get("LEDGERLINE_BOB_PASSWORD"),
            "auditor": os.environ.get("LEDGERLINE_AUDITOR_PASSWORD"),
        }
        if (
            any(not password or len(password) < 12 for password in required_passwords.values())
            or len(set(required_passwords.values())) != len(required_passwords)
        ):
            raise RuntimeError(
                "Production requires a unique password of at least 12 characters for each seeded user"
            )
        initial_users = [
            ("admin", required_passwords["admin"], UserRole.ADMIN),
            ("alice", required_passwords["alice"], UserRole.ACCOUNT_HOLDER),
            ("bob", required_passwords["bob"], UserRole.ACCOUNT_HOLDER),
            ("auditor", required_passwords["auditor"], UserRole.AUDITOR),
        ]
    else:
        initial_users = [
            ("admin", "adminpass", UserRole.ADMIN),
            ("alice", "pass123", UserRole.ACCOUNT_HOLDER),
            ("bob", "pass123", UserRole.ACCOUNT_HOLDER),
            ("auditor", "pass123", UserRole.AUDITOR),
        ]

    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'account_holder', 'auditor'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                owner_username TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0,
                overdraft_limit INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(owner_username) REFERENCES users(username)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('credit', 'debit', 'refused')),
                amount INTEGER NOT NULL,
                running_balance INTEGER NOT NULL,
                description TEXT,
                actor_user_id INTEGER,
                request_key TEXT,
                operation_id TEXT NOT NULL,
                actor_username TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                hash_value TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                client_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                actor_user_id INTEGER,
                request_hash TEXT
            )
            """
        )

        idempotency_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(idempotency_keys)")
        }
        if "actor_user_id" not in idempotency_columns:
            conn.execute("ALTER TABLE idempotency_keys ADD COLUMN actor_user_id INTEGER")
        if "request_hash" not in idempotency_columns:
            conn.execute("ALTER TABLE idempotency_keys ADD COLUMN request_hash TEXT")

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_accounts_owner ON accounts(owner_username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ledger_account_id ON ledger_entries(account_id, id)"
        )

        if reset:
            conn.execute("DROP TRIGGER IF EXISTS ledger_entries_no_update")
            conn.execute("DROP TRIGGER IF EXISTS ledger_entries_no_delete")
            conn.execute("DELETE FROM idempotency_keys")
            conn.execute("DELETE FROM ledger_entries")
            conn.execute("DELETE FROM accounts")
            conn.execute("DELETE FROM users")

        for username, password, role in initial_users:
            existing = conn.execute(
                "SELECT id, password FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hash_password(password), role),
                )
            elif production_mode and not verify_password(
                password, existing["password"]
            ):
                conn.execute(
                    "UPDATE users SET password = ?, role = ? WHERE id = ?",
                    (hash_password(password), role, existing["id"]),
                )

        for row in conn.execute("SELECT id, password FROM users").fetchall():
            if not row["password"].startswith("pbkdf2_sha256$"):
                conn.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (hash_password(row["password"]), row["id"]),
                )

        initial_accounts = [
            ("Alice Checking", "alice", 1000, 0),
            ("Bob Checking", "bob", 250, 0),
            ("Treasury", "admin", 0, 0),
        ]
        for name, owner, balance, overdraft in initial_accounts:
            conn.execute("INSERT OR IGNORE INTO accounts (name, owner_username, balance, overdraft_limit) VALUES (?, ?, ?, ?)", (name, owner, balance, overdraft))

        seed_ledger = reset or conn.execute("SELECT 1 FROM ledger_entries LIMIT 1").fetchone() is None
        if seed_ledger:
            admin = conn.execute("SELECT id, username FROM users WHERE username = 'admin'").fetchone()
            account_rows = conn.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
            for row in account_rows:
                append_ledger_event(
                    conn,
                    account_id=row["id"],
                    kind="credit",
                    amount=row["balance"],
                    running_balance=row["balance"],
                    description="opening balance",
                    actor_user={"id": admin["id"], "username": admin["username"]},
                    request_key=f"seed-{row['id']}",
                    operation_id=f"seed-op-{row['id']}",
                )

        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS ledger_entries_no_update
            BEFORE UPDATE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'ledger entries are append-only');
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS ledger_entries_no_delete
            BEFORE DELETE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'ledger entries are append-only');
            END
            """
        )


def require_money_permission(user: dict[str, Any], account: sqlite3.Row) -> None:
    if user["role"] == UserRole.ADMIN:
        return
    if (
        user["role"] != UserRole.ACCOUNT_HOLDER
        or account["owner_username"] != user["username"]
    ):
        raise HTTPException(status_code=403, detail="Not permitted to move this account's money")


def request_fingerprint(operation: str, payload: Any) -> str:
    if isinstance(payload, BaseModel):
        model_dump = getattr(payload, "model_dump", None)
        payload_data = (
            model_dump(exclude={"client_key"})
            if model_dump is not None
            else payload.dict(exclude={"client_key"})
        )
    else:
        payload_data = {
            key: value
            for key, value in vars(payload).items()
            if key != "client_key"
        }
    return hash_payload(
        {"operation": operation, "payload": payload_data}
    )


def store_idempotency(
    conn: sqlite3.Connection,
    *,
    client_key: str,
    response: dict[str, Any],
    actor_user_id: int,
    request_hash: str,
) -> None:
    conn.execute(
        "INSERT INTO idempotency_keys (client_key, response_json, created_at, actor_user_id, request_hash) VALUES (?, ?, ?, ?, ?)",
        (
            client_key,
            json.dumps(response),
            int(time.time()),
            actor_user_id,
            request_hash,
        ),
    )


@app.post("/login")
def login(payload: LoginRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
        if row is None or not verify_password(payload.password, row["password"]):
            raise HTTPException(status_code=401, detail="Invalid username/password")
        if not row["password"].startswith("pbkdf2_sha256$"):
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(payload.password), row["id"]),
            )
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid username/password")
    token = tokenise(row["username"], row["role"])
    return {"token": token, "user": {"username": row["username"], "role": row["role"]}}


@app.get("/me")
def get_current_user(user: dict[str, Any] = Depends(current_user)):
    return {"username": user["username"], "role": user["role"]}


@app.get("/accounts")
def list_accounts(user: dict[str, Any] = Depends(current_user)):
    with get_db() as conn:
        if user["role"] in (UserRole.ADMIN, UserRole.AUDITOR):
            rows = conn.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM accounts WHERE owner_username = ? ORDER BY id ASC", (user["username"],)).fetchall()
    return [dict(r) for r in rows]


@app.post("/accounts")
def create_account(payload: AccountCreateRequest, user: dict[str, Any] = Depends(current_user)):
    require_admin(user)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            owner = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (payload.owner_username,)
            ).fetchone()
            if owner is None:
                raise HTTPException(status_code=404, detail="Account owner not found")
            cursor = conn.execute(
                "INSERT INTO accounts (name, owner_username, balance, overdraft_limit) VALUES (?, ?, 0, ?)",
                (payload.name, payload.owner_username, payload.overdraft_limit),
            )
            account_id = cursor.lastrowid
            append_ledger_event(
                conn,
                account_id=account_id,
                kind="credit",
                amount=0,
                running_balance=0,
                description="account created",
                actor_user=user,
                request_key=f"account-create-{account_id}",
                operation_id=f"account-create-{account_id}",
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            conn.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Account name already exists") from exc
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"id": account_id, "name": payload.name, "owner_username": payload.owner_username, "balance": 0, "overdraft_limit": payload.overdraft_limit}


@app.get("/accounts/{account_id}")
def get_account(account_id: int, user: dict[str, Any] = Depends(current_user)):
    row = account_for_user(user, account_id)
    return dict(row)


@app.get("/accounts/{account_id}/statement")
def get_statement(account_id: int, user: dict[str, Any] = Depends(current_user)):
    account_for_user(user, account_id)
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM ledger_entries WHERE account_id = ? ORDER BY id ASC", (account_id,)).fetchall()
    return {"account_id": account_id, "entries": [dict(r) for r in rows], "hash_valid": verify_ledger_chain()}


@app.get("/ledger/verify")
def verify_ledger(user: dict[str, Any] = Depends(current_user)):
    if user["role"] not in (UserRole.ADMIN, UserRole.AUDITOR):
        raise HTTPException(status_code=403, detail="Administrators and auditors only")
    return {"hash_valid": verify_ledger_chain()}


@app.post("/deposits")
def create_deposit(payload: MoneyRequest, user: dict[str, Any] = Depends(current_user)):
    account = account_for_user(user, payload.account_id, require_owner=True)
    require_money_permission(user, account)
    fingerprint = request_fingerprint("deposit", payload)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            existing = read_idempotency(
                conn, payload.client_key, user["id"], fingerprint
            )
            if existing is not None:
                conn.execute("COMMIT")
                return existing

            current = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.account_id,)).fetchone()
            new_balance = current["balance"] + payload.amount
            conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, payload.account_id))
            operation_id = f"deposit:{payload.client_key}"
            append_ledger_event(
                conn,
                account_id=payload.account_id,
                kind="credit",
                amount=payload.amount,
                running_balance=new_balance,
                description=payload.description,
                actor_user=user,
                request_key=payload.client_key,
                operation_id=operation_id,
            )
            response = {
                "id": operation_id,
                "result": "posted",
                "amount": payload.amount,
                "account_id": payload.account_id,
                "balance": new_balance,
                "idempotent": False,
            }
            store_idempotency(
                conn,
                client_key=payload.client_key,
                response=response,
                actor_user_id=user["id"],
                request_hash=fingerprint,
            )
            conn.execute("COMMIT")
            return response
        except Exception:
            conn.execute("ROLLBACK")
            raise


@app.post("/withdrawals")
def create_withdrawal(payload: MoneyRequest, user: dict[str, Any] = Depends(current_user)):
    account = account_for_user(user, payload.account_id, require_owner=True)
    require_money_permission(user, account)
    fingerprint = request_fingerprint("withdrawal", payload)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            existing = read_idempotency(
                conn, payload.client_key, user["id"], fingerprint
            )
            if existing is not None:
                conn.execute("COMMIT")
                return existing

            current = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.account_id,)).fetchone()
            new_balance = current["balance"] - payload.amount
            operation_id = f"withdraw:{payload.client_key}"
            if new_balance < -account["overdraft_limit"]:
                response = {
                    "id": operation_id,
                    "result": "rejected",
                    "amount": payload.amount,
                    "account_id": payload.account_id,
                    "balance": current["balance"],
                    "reason": "insufficient_funds",
                    "idempotent": False,
                }
                append_ledger_event(
                    conn,
                    account_id=payload.account_id,
                    kind="refused",
                    amount=payload.amount,
                    running_balance=current["balance"],
                    description=payload.description,
                    actor_user=user,
                    request_key=payload.client_key,
                    operation_id=operation_id,
                )
                store_idempotency(
                    conn,
                    client_key=payload.client_key,
                    response=response,
                    actor_user_id=user["id"],
                    request_hash=fingerprint,
                )
                conn.execute("COMMIT")
                return response

            conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, payload.account_id))
            append_ledger_event(
                conn,
                account_id=payload.account_id,
                kind="debit",
                amount=payload.amount,
                running_balance=new_balance,
                description=payload.description,
                actor_user=user,
                request_key=payload.client_key,
                operation_id=operation_id,
            )
            response = {
                "id": operation_id,
                "result": "posted",
                "amount": payload.amount,
                "account_id": payload.account_id,
                "balance": new_balance,
                "idempotent": False,
            }
            store_idempotency(
                conn,
                client_key=payload.client_key,
                response=response,
                actor_user_id=user["id"],
                request_hash=fingerprint,
            )
            conn.execute("COMMIT")
            return response
        except Exception:
            conn.execute("ROLLBACK")
            raise


@app.post("/transfers")
def create_transfer(payload: TransferRequest, user: dict[str, Any] = Depends(current_user)):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    fingerprint = request_fingerprint("transfer", payload)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            from_account = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.from_account_id,)).fetchone()
            to_account = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.to_account_id,)).fetchone()
            if from_account is None or to_account is None:
                raise HTTPException(status_code=404, detail="Account not found")
            require_money_permission(user, from_account)

            existing = read_idempotency(
                conn, payload.client_key, user["id"], fingerprint
            )
            if existing is not None:
                conn.execute("COMMIT")
                return existing

            new_from = from_account["balance"] - payload.amount
            if new_from < -from_account["overdraft_limit"]:
                response = {
                    "id": f"transfer:{payload.client_key}",
                    "result": "rejected",
                    "amount": payload.amount,
                    "from_account_id": payload.from_account_id,
                    "to_account_id": payload.to_account_id,
                    "reason": "insufficient_funds",
                    "idempotent": False,
                }
                append_ledger_event(
                    conn,
                    account_id=payload.from_account_id,
                    kind="refused",
                    amount=payload.amount,
                    running_balance=from_account["balance"],
                    description=payload.description,
                    actor_user=user,
                    request_key=payload.client_key,
                    operation_id=f"transfer:{payload.client_key}",
                )
                store_idempotency(
                    conn,
                    client_key=payload.client_key,
                    response=response,
                    actor_user_id=user["id"],
                    request_hash=fingerprint,
                )
                conn.execute("COMMIT")
                return response

            new_to = to_account["balance"] + payload.amount
            conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_from, payload.from_account_id))
            conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_to, payload.to_account_id))

            operation_id = f"transfer:{payload.client_key}"
            append_ledger_event(
                conn,
                account_id=payload.from_account_id,
                kind="debit",
                amount=payload.amount,
                running_balance=new_from,
                description=payload.description,
                actor_user=user,
                request_key=payload.client_key,
                operation_id=operation_id,
            )
            append_ledger_event(
                conn,
                account_id=payload.to_account_id,
                kind="credit",
                amount=payload.amount,
                running_balance=new_to,
                description=payload.description,
                actor_user=user,
                request_key=payload.client_key,
                operation_id=operation_id,
            )
            response = {
                "id": operation_id,
                "result": "posted",
                "amount": payload.amount,
                "from_account_id": payload.from_account_id,
                "to_account_id": payload.to_account_id,
                "from_balance": new_from,
                "to_balance": new_to,
                "idempotent": False,
            }
            store_idempotency(
                conn,
                client_key=payload.client_key,
                response=response,
                actor_user_id=user["id"],
                request_hash=fingerprint,
            )
            conn.execute("COMMIT")
            return response
        except Exception:
            conn.execute("ROLLBACK")
            raise


@app.get("/")
def root():
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")


@app.on_event("startup")
def startup_event():
    init_db()
