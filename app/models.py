from __future__ import annotations

import time
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="account_holder")
    email = Column(String(255), nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))

    accounts = relationship("Account", back_populates="owner")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), unique=True, nullable=False)
    owner_username = Column(String(80), ForeignKey("users.username"), nullable=False, index=True)
    balance = Column(BigInteger, nullable=False, default=0)
    overdraft_limit = Column(BigInteger, nullable=False, default=0)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))

    owner = relationship("User", back_populates="accounts")
    ledger_entries = relationship("LedgerEntry", back_populates="account")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    kind = Column(String(32), nullable=False)  # 'credit', 'debit', 'refused'
    amount = Column(BigInteger, nullable=False)
    running_balance = Column(BigInteger, nullable=False)
    description = Column(Text, nullable=False, default="")
    actor_user_id = Column(Integer, nullable=False)
    request_key = Column(String(128), nullable=False)
    operation_id = Column(String(128), nullable=False)
    actor_username = Column(String(80), nullable=False)
    prev_hash = Column(String(64), nullable=False)
    hash_value = Column(String(64), nullable=False, index=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))

    account = relationship("Account", back_populates="ledger_entries")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    client_key = Column(String(128), primary_key=True)
    response_json = Column(Text, nullable=False)
    actor_user_id = Column(Integer, nullable=False)
    request_hash = Column(String(64), nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time()))

