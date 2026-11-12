from __future__ import annotations

from enum import Enum
from typing import Set


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"  # Backward-compatible alias for super_admin
    ACCOUNT_HOLDER = "account_holder"
    AUDITOR = "auditor"


class Permission(str, Enum):
    USERS_CREATE = "users:create"
    USERS_READ = "users:read"
    USERS_MANAGE = "users:manage"
    ACCOUNTS_CREATE = "accounts:create"
    ACCOUNTS_READ_ALL = "accounts:read_all"
    ACCOUNTS_READ_OWN = "accounts:read_own"
    TRANSACTIONS_DEPOSIT = "transactions:deposit"
    TRANSACTIONS_WITHDRAW = "transactions:withdraw"
    TRANSACTIONS_TRANSFER = "transactions:transfer"
    LEDGER_READ_ALL = "ledger:read_all"
    LEDGER_VERIFY = "ledger:verify"


# Canonical permission mappings per role
ROLE_PERMISSIONS: dict[str, Set[str]] = {
    UserRole.SUPER_ADMIN: {
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.ACCOUNTS_CREATE,
        Permission.ACCOUNTS_READ_ALL,
        Permission.ACCOUNTS_READ_OWN,
        Permission.TRANSACTIONS_DEPOSIT,
        Permission.TRANSACTIONS_WITHDRAW,
        Permission.TRANSACTIONS_TRANSFER,
        Permission.LEDGER_READ_ALL,
        Permission.LEDGER_VERIFY,
    },
    UserRole.ADMIN: {  # Same as SUPER_ADMIN
        Permission.USERS_CREATE,
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.ACCOUNTS_CREATE,
        Permission.ACCOUNTS_READ_ALL,
        Permission.ACCOUNTS_READ_OWN,
        Permission.TRANSACTIONS_DEPOSIT,
        Permission.TRANSACTIONS_WITHDRAW,
        Permission.TRANSACTIONS_TRANSFER,
        Permission.LEDGER_READ_ALL,
        Permission.LEDGER_VERIFY,
    },
    UserRole.ACCOUNT_HOLDER: {
        Permission.ACCOUNTS_READ_OWN,
        Permission.TRANSACTIONS_DEPOSIT,
        Permission.TRANSACTIONS_WITHDRAW,
        Permission.TRANSACTIONS_TRANSFER,
    },
    UserRole.AUDITOR: {
        Permission.ACCOUNTS_READ_ALL,
        Permission.LEDGER_READ_ALL,
        Permission.LEDGER_VERIFY,
    },
}


def normalize_role(role: str) -> str:
    """Normalize legacy role strings to canonical roles."""
    if role == "admin":
        return UserRole.SUPER_ADMIN.value
    return role


def has_permission(role: str, permission: Permission | str) -> bool:
    """Check if a given role has a specific permission."""
    canonical_role = normalize_role(role)
    perm_value = permission.value if isinstance(permission, Permission) else permission
    permissions = ROLE_PERMISSIONS.get(canonical_role, set())
    return perm_value in permissions or perm_value in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: str) -> list[str]:
    """Retrieve all permission strings assigned to a role."""
    canonical_role = normalize_role(role)
    perms = ROLE_PERMISSIONS.get(canonical_role, set()) | ROLE_PERMISSIONS.get(role, set())
    return sorted(list(perms))

