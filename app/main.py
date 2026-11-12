from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import (
    DB_PATH as DEFAULT_DB_PATH,
    check_database_health,
    get_db_connection,
    init_database_schema,
    is_postgres,
)
from app.ratelimit import check_redis_health, rate_limit
from app.rbac import (
    Permission,
    UserRole,
    get_role_permissions,
    has_permission,
    normalize_role,
)

logger = logging.getLogger("balancevault")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = DEFAULT_DB_PATH

TOKEN_SECRET = os.environ.get("LEDGERLINE_TOKEN_SECRET")
if not TOKEN_SECRET and os.environ.get("LEDGERLINE_ENV") == "production":
    raise RuntimeError("LEDGERLINE_TOKEN_SECRET must be set in production")
if not TOKEN_SECRET:
    TOKEN_SECRET = secrets.token_urlsafe(32)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database schema and triggers are initialized
    init_db()
    yield


app = FastAPI(
    title="BalanceVault",
    version="2.0.0",
    description="Enterprise Financial Transaction Ledger with PostgreSQL, Redis Rate Limiting, and Hash-Chained Double-Entry Accounting.",
    lifespan=lifespan,
)

# CORS configuration
origins_env = os.environ.get("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
security = HTTPBearer(auto_error=False)


# ============================================================================
# Request / Response Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=256)
    email: Optional[str] = Field(default=None, max_length=255)
    initial_deposit: Optional[int] = Field(default=0, ge=0)


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


# ============================================================================
# Database & Crypto Helpers
# ============================================================================

def get_db():
    return get_db_connection(DB_PATH)


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
    user_dict = dict(row)
    user_dict["permissions"] = get_role_permissions(user_dict["role"])
    return user_dict


def require_admin(user: dict[str, Any]) -> None:
    if user["role"] not in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, "admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Administrator only")


def require_permission(permission: Permission | str):
    def dependency(user: dict[str, Any] = Depends(current_user)):
        if not has_permission(user["role"], permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: requires {permission}")
        return user
    return dependency


def account_for_user(user: dict[str, Any], account_id: int, *, require_owner: bool = False) -> dict[str, Any]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if user["role"] in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, "admin", "super_admin", UserRole.AUDITOR.value):
        return row
    if require_owner and row["owner_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not permitted to modify this account")
    if row["owner_username"] != user["username"]:
        raise HTTPException(status_code=403, detail="Not permitted to access this account")
    return row


def get_last_hash(conn: Any) -> str:
    row = conn.execute("SELECT hash_value FROM ledger_entries ORDER BY id DESC LIMIT 1").fetchone()
    return row["hash_value"] if row else "genesis"


def append_ledger_event(
    conn: Any,
    *,
    account_id: int,
    kind: str,
    amount: int,
    running_balance: int,
    description: str,
    actor_user: dict[str, Any],
    request_key: str,
    operation_id: str,
) -> str:
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
    conn: Any, client_key: str, actor_user_id: int, request_hash: str
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


def store_idempotency(
    conn: Any,
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
            ("admin", required_passwords["admin"], UserRole.ADMIN.value),
            ("alice", required_passwords["alice"], UserRole.ACCOUNT_HOLDER.value),
            ("bob", required_passwords["bob"], UserRole.ACCOUNT_HOLDER.value),
            ("auditor", required_passwords["auditor"], UserRole.AUDITOR.value),
        ]
    else:
        initial_users = [
            ("admin", "adminpass", UserRole.ADMIN.value),
            ("alice", "pass123", UserRole.ACCOUNT_HOLDER.value),
            ("bob", "pass123", UserRole.ACCOUNT_HOLDER.value),
            ("auditor", "pass123", UserRole.AUDITOR.value),
        ]

    with get_db() as conn:
        init_database_schema(conn)

        if not is_postgres():
            # Check legacy sqlite migrations
            idempotency_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(idempotency_keys)").fetchall()
            }
            if "actor_user_id" not in idempotency_columns:
                conn.execute("ALTER TABLE idempotency_keys ADD COLUMN actor_user_id INTEGER")
            if "request_hash" not in idempotency_columns:
                conn.execute("ALTER TABLE idempotency_keys ADD COLUMN request_hash TEXT")

        if reset:
            if not is_postgres():
                conn.execute("DROP TRIGGER IF EXISTS ledger_entries_no_update")
                conn.execute("DROP TRIGGER IF EXISTS ledger_entries_no_delete")
                conn.execute("DROP TRIGGER IF EXISTS prevent_ledger_update")
                conn.execute("DROP TRIGGER IF EXISTS prevent_ledger_delete")
            conn.execute("DELETE FROM idempotency_keys")
            conn.execute("DELETE FROM ledger_entries")
            conn.execute("DELETE FROM accounts")
            conn.execute("DELETE FROM users")
            conn.commit()

        user_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        } if not is_postgres() else {"id", "username", "password", "role", "email", "created_at"}

        for username, password, role in initial_users:
            existing = conn.execute(
                "SELECT id, password FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing is None:
                if "created_at" in user_cols:
                    conn.execute(
                        "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                        (username, hash_password(password), role, int(time.time())),
                    )
                else:
                    conn.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (username, hash_password(password), role),
                    )
            elif production_mode and not verify_password(password, existing["password"]):
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
        conn.commit()

        acc_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        } if not is_postgres() else {"id", "name", "owner_username", "balance", "overdraft_limit", "created_at"}

        initial_accounts = [
            ("Alice Checking", "alice", 1000, 0),
            ("Bob Checking", "bob", 250, 0),
            ("Treasury", "admin", 0, 0),
        ]
        for name, owner, balance, overdraft in initial_accounts:
            existing_acc = conn.execute("SELECT id FROM accounts WHERE name = ?", (name,)).fetchone()
            if not existing_acc:
                if "created_at" in acc_cols:
                    conn.execute(
                        "INSERT INTO accounts (name, owner_username, balance, overdraft_limit, created_at) VALUES (?, ?, ?, ?, ?)",
                        (name, owner, balance, overdraft, int(time.time())),
                    )
                else:
                    conn.execute(
                        "INSERT INTO accounts (name, owner_username, balance, overdraft_limit) VALUES (?, ?, ?, ?)",
                        (name, owner, balance, overdraft),
                    )
        conn.commit()

        seed_ledger = reset or conn.execute("SELECT 1 FROM ledger_entries LIMIT 1").fetchone() is None
        if seed_ledger:
            admin = conn.execute("SELECT id, username FROM users WHERE username = 'admin'").fetchone()
            if admin:
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
                conn.commit()

        # Re-verify triggers for SQLite
        if not is_postgres():
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
                BEFORE UPDATE ON ledger_entries
                BEGIN
                    SELECT RAISE(FAIL, 'ledger_entries is append-only');
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
                BEFORE DELETE ON ledger_entries
                BEGIN
                    SELECT RAISE(FAIL, 'ledger_entries is append-only');
                END;
                """
            )
            conn.commit()


def require_money_permission(user: dict[str, Any], account: dict[str, Any]) -> None:
    if user["role"] in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, "admin", "super_admin"):
        return
    if (
        user["role"] != UserRole.ACCOUNT_HOLDER.value
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
    return hash_payload({"operation": operation, "payload": payload_data})


# ============================================================================
# Health & Readiness Endpoints
# ============================================================================

@app.get("/health")
def health_check():
    """Liveness probe: verifies service availability."""
    return {
        "status": "ok",
        "app": "BalanceVault",
        "version": "2.0.0",
        "timestamp": int(time.time()),
    }


@app.get("/ready")
def readiness_check(response: Response):
    """Readiness probe: verifies database and redis connectivity."""
    db_ok, db_status = check_database_health()
    redis_ok, redis_status = check_redis_health()

    is_ready = db_ok
    if not is_ready:
        response.status_code = 503
        return {
            "status": "not_ready",
            "app": "BalanceVault",
            "database": db_status,
            "redis": redis_status,
            "timestamp": int(time.time()),
        }

    return {
        "status": "ready",
        "app": "BalanceVault",
        "database": db_status,
        "redis": redis_status,
        "timestamp": int(time.time()),
    }


# ============================================================================
# User Onboarding & Authentication Endpoints
# ============================================================================

@app.post("/auth/register")
def register(
    payload: RegisterRequest,
    _rate_limit: bool = Depends(rate_limit(limit=10, window_seconds=60, key_prefix="auth_register")),
):
    """Register a new user, create an account, and issue authentication token."""
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (payload.username,)).fetchone()
            if existing:
                raise HTTPException(status_code=409, detail="Username already registered")

            now = int(time.time())
            hashed = hash_password(payload.password)
            role = UserRole.ACCOUNT_HOLDER.value

            conn.execute(
                "INSERT INTO users (username, password, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
                (payload.username, hashed, role, payload.email, now),
            )
            user_row = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
            user_id = user_row["id"]

            # Automatically provision default account
            account_name = f"{payload.username.capitalize()} Primary Account"
            initial_balance = payload.initial_deposit or 0

            conn.execute(
                "INSERT INTO accounts (name, owner_username, balance, overdraft_limit, created_at) VALUES (?, ?, ?, ?, ?)",
                (account_name, payload.username, initial_balance, 0, now),
            )
            acc_row = conn.execute("SELECT id FROM accounts WHERE name = ?", (account_name,)).fetchone()
            account_id = acc_row["id"]

            # Ledger record for opening balance
            append_ledger_event(
                conn,
                account_id=account_id,
                kind="credit",
                amount=initial_balance,
                running_balance=initial_balance,
                description="Opening account provisioned",
                actor_user={"id": user_id, "username": payload.username},
                request_key=f"onboard-{account_id}",
                operation_id=f"onboard-op-{account_id}",
            )
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise

    token = tokenise(payload.username, role)
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "username": payload.username,
            "role": role,
            "email": payload.email,
            "permissions": get_role_permissions(role),
        },
        "account": {
            "id": account_id,
            "name": account_name,
            "balance": initial_balance,
        },
    }


@app.post("/auth/login")
@app.post("/login")
def login(
    payload: LoginRequest,
    _rate_limit: bool = Depends(rate_limit(limit=15, window_seconds=60, key_prefix="auth_login")),
):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
        if row is None or not verify_password(payload.password, row["password"]):
            raise HTTPException(status_code=401, detail="Invalid username/password")
        if not row["password"].startswith("pbkdf2_sha256$"):
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(payload.password), row["id"]),
            )
            conn.commit()
    token = tokenise(row["username"], row["role"])
    return {
        "token": token,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "permissions": get_role_permissions(row["role"]),
        },
    }


@app.get("/auth/me")
@app.get("/me")
def get_current_user_profile(user: dict[str, Any] = Depends(current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "email": user.get("email"),
        "permissions": get_role_permissions(user["role"]),
    }


@app.post("/auth/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: dict[str, Any] = Depends(current_user),
):
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT id, password FROM users WHERE username = ?",
                (user["username"],)
            ).fetchone()
            if not row or not verify_password(payload.old_password, row["password"]):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            new_hash = hash_password(payload.new_password)
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (new_hash, row["id"])
            )
            conn.commit()
            return {"status": "ok", "message": "Password updated successfully"}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
# ============================================================================
# Account & Ledger Endpoints
# ============================================================================

@app.get("/accounts")
def list_accounts(user: dict[str, Any] = Depends(current_user)):
    with get_db() as conn:
        if has_permission(user["role"], Permission.ACCOUNTS_READ_ALL):
            rows = conn.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM accounts WHERE owner_username = ? ORDER BY id ASC", (user["username"],)).fetchall()
    return [dict(r) for r in rows]


@app.post("/accounts")
def create_account(
    payload: AccountCreateRequest,
    user: dict[str, Any] = Depends(require_permission(Permission.ACCOUNTS_CREATE)),
):
    require_admin(user)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            owner = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (payload.owner_username,)
            ).fetchone()
            if owner is None:
                raise HTTPException(status_code=404, detail="Account owner not found")

            # Check duplicate name
            existing = conn.execute("SELECT id FROM accounts WHERE name = ?", (payload.name,)).fetchone()
            if existing:
                raise HTTPException(status_code=409, detail="Account name already exists")

            now = int(time.time())
            conn.execute(
                "INSERT INTO accounts (name, owner_username, balance, overdraft_limit, created_at) VALUES (?, ?, 0, ?, ?)",
                (payload.name, payload.owner_username, payload.overdraft_limit, now),
            )
            account_row = conn.execute("SELECT id FROM accounts WHERE name = ?", (payload.name,)).fetchone()
            account_id = account_row["id"]

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
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except (sqlite3.IntegrityError, Exception) as exc:
            conn.rollback()
            if "UNIQUE" in str(exc).upper() or "ALREADY EXISTS" in str(exc).upper():
                raise HTTPException(status_code=409, detail="Account name already exists") from exc
            raise
    return {
        "id": account_id,
        "name": payload.name,
        "owner_username": payload.owner_username,
        "balance": 0,
        "overdraft_limit": payload.overdraft_limit,
    }


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


@app.get("/accounts/{account_id}/statement/csv")
def get_statement_csv(account_id: int, user: dict[str, Any] = Depends(current_user)):
    acc = account_for_user(user, account_id)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ledger_entries WHERE account_id = ? ORDER BY id ASC", (account_id,)
        ).fetchall()

    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Entry ID",
        "Timestamp",
        "Date (UTC)",
        "Account ID",
        "Account Name",
        "Type",
        "Amount (INR)",
        "Balance After (INR)",
        "Description",
        "Previous Hash",
        "Current Hash",
    ])
    for r in rows:
        ts = r["created_at"]
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))
        writer.writerow([
            r["id"],
            ts,
            dt,
            account_id,
            acc["name"],
            r["kind"],
            r["amount"],
            r["running_balance"],
            r["description"],
            r["prev_hash"],
            r["hash_value"],
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=balancevault_statement_acc_{account_id}.csv"},
    )


@app.get("/ledger/verify")
def verify_ledger(user: dict[str, Any] = Depends(require_permission(Permission.LEDGER_VERIFY))):
    return {"hash_valid": verify_ledger_chain()}


@app.get("/ledger/entries")
def get_ledger_entries(
    limit: int = 100,
    user: dict[str, Any] = Depends(require_permission(Permission.LEDGER_READ_ALL)),
):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ledger_entries ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return {
        "entries": [dict(r) for r in rows],
        "hash_valid": verify_ledger_chain(),
        "total": len(rows),
    }
# ============================================================================
# Financial Transaction Endpoints (With Concurrency Row-Locking & Rate Limiting)
# ============================================================================

@app.post("/deposits")
def create_deposit(
    payload: MoneyRequest,
    user: dict[str, Any] = Depends(current_user),
    _rate_limit: bool = Depends(rate_limit(limit=60, window_seconds=60, key_prefix="tx_deposit")),
):
    account = account_for_user(user, payload.account_id, require_owner=True)
    require_money_permission(user, account)
    fingerprint = request_fingerprint("deposit", payload)

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Row-level lock on PostgreSQL
            if is_postgres():
                conn.execute("SELECT * FROM accounts WHERE id = ? FOR UPDATE", (payload.account_id,))

            existing = read_idempotency(conn, payload.client_key, user["id"], fingerprint)
            if existing is not None:
                conn.commit()
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
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise


@app.post("/withdrawals")
def create_withdrawal(
    payload: MoneyRequest,
    user: dict[str, Any] = Depends(current_user),
    _rate_limit: bool = Depends(rate_limit(limit=60, window_seconds=60, key_prefix="tx_withdraw")),
):
    account = account_for_user(user, payload.account_id, require_owner=True)
    require_money_permission(user, account)
    fingerprint = request_fingerprint("withdrawal", payload)

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Row-level lock on PostgreSQL
            if is_postgres():
                conn.execute("SELECT * FROM accounts WHERE id = ? FOR UPDATE", (payload.account_id,))

            existing = read_idempotency(conn, payload.client_key, user["id"], fingerprint)
            if existing is not None:
                conn.commit()
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
                conn.commit()
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
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise


@app.post("/transfers")
def create_transfer(
    payload: TransferRequest,
    user: dict[str, Any] = Depends(current_user),
    _rate_limit: bool = Depends(rate_limit(limit=60, window_seconds=60, key_prefix="tx_transfer")),
):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    fingerprint = request_fingerprint("transfer", payload)
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Deterministic Row-Level Lock Order in PostgreSQL to prevent deadlocks
            if is_postgres():
                first_id, second_id = sorted([payload.from_account_id, payload.to_account_id])
                conn.execute(
                    "SELECT * FROM accounts WHERE id IN (?, ?) ORDER BY id FOR UPDATE",
                    (first_id, second_id),
                )

            from_account = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.from_account_id,)).fetchone()
            to_account = conn.execute("SELECT * FROM accounts WHERE id = ?", (payload.to_account_id,)).fetchone()
            if from_account is None or to_account is None:
                raise HTTPException(status_code=404, detail="Account not found")
            require_money_permission(user, from_account)

            existing = read_idempotency(conn, payload.client_key, user["id"], fingerprint)
            if existing is not None:
                conn.commit()
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
                conn.commit()
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
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise


@app.get("/")
def root():
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")
