#!/usr/bin/env python3
"""
BalanceVault First-Admin Bootstrap Script

Usage:
  # Via environment variables:
  export ADMIN_USERNAME="superadmin"
  export ADMIN_PASSWORD="your-strong-password-at-least-12-chars"
  python scripts/bootstrap_admin.py

  # Or interactively:
  python scripts/bootstrap_admin.py
"""

from __future__ import annotations

import getpass
import hashlib
import os
import secrets
import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db import DB_PATH, get_db_connection, init_database_schema
from app.rbac import UserRole


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 240_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def bootstrap_admin(username: str | None = None, password: str | None = None, db_path: Path | None = None) -> bool:
    username = username or os.environ.get("ADMIN_USERNAME")
    password = password or os.environ.get("ADMIN_PASSWORD")

    # If not in env, prompt interactively if attached to a terminal
    if not username:
        if sys.stdin.isatty():
            username = input("Enter Super Admin username [default: admin]: ").strip() or "admin"
        else:
            username = "admin"

    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass("Enter Super Admin password (min 12 chars): ").strip()
        else:
            print("ERROR: ADMIN_PASSWORD environment variable must be set in non-interactive environments.", file=sys.stderr)
            return False

    if len(password) < 12:
        print("ERROR: Administrator password must be at least 12 characters long.", file=sys.stderr)
        return False

    target_path = db_path or os.environ.get("DATABASE_PATH") or None
    with get_db_connection(target_path) as conn:
        init_database_schema(conn)

        # Check for existing super admin
        conn.execute("SELECT id, username, role FROM users WHERE role IN (?, ?)", (UserRole.SUPER_ADMIN.value, "admin"))
        existing_admins = conn.fetchall()

        if existing_admins:
            print(f"INFO: Super Administrator already exists (found {len(existing_admins)} admin user(s)). Duplicate creation prevented.")
            return False

        # Also check if the chosen username is already taken
        conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        if conn.fetchone():
            print(f"ERROR: Username '{username}' already exists.", file=sys.stderr)
            return False

        hashed = hash_password(password)
        now = int(time.time())

        # Insert super admin
        conn.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            (username, hashed, UserRole.SUPER_ADMIN.value, now),
        )

        # Create primary administration account
        account_name = f"{username.capitalize()} Treasury Operations"
        conn.execute(
            "INSERT INTO accounts (name, owner_username, balance, overdraft_limit, created_at) VALUES (?, ?, ?, ?, ?)",
            (account_name, username, 0, 0, now),
        )

        conn.commit()
        print(f"SUCCESS: Super Administrator '{username}' successfully created with role '{UserRole.SUPER_ADMIN.value}'.")
        print(f"SUCCESS: Treasury Operations account '{account_name}' initialized.")
        return True


if __name__ == "__main__":
    success = bootstrap_admin()
    sys.exit(0 if success else 1)
