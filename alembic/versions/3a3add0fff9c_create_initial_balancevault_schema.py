"""create_initial_balancevault_schema

Revision ID: 3a3add0fff9c
Revises: 
Create Date: 2026-11-12 16:49:35.896503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a3add0fff9c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('owner_username', sa.String(length=80), nullable=False),
        sa.Column('balance', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('overdraft_limit', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.BigInteger(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['owner_username'], ['users.username']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_accounts_owner_username'), 'accounts', ['owner_username'], unique=False)

    # 3. ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('running_balance', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('actor_user_id', sa.Integer(), nullable=False),
        sa.Column('request_key', sa.String(length=128), nullable=False),
        sa.Column('operation_id', sa.String(length=128), nullable=False),
        sa.Column('actor_username', sa.String(length=80), nullable=False),
        sa.Column('prev_hash', sa.String(length=64), nullable=False),
        sa.Column('hash_value', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ledger_entries_account_id'), 'ledger_entries', ['account_id'], unique=False)
    op.create_index(op.f('ix_ledger_entries_hash_value'), 'ledger_entries', ['hash_value'], unique=False)

    # 4. idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('client_key', sa.String(length=128), nullable=False),
        sa.Column('response_json', sa.Text(), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('client_key'),
    )

    # 5. PostgreSQL Triggers for Append-Only Ledger
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_ledger_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'ledger_entries is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_prevent_ledger_update
            BEFORE UPDATE ON ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_prevent_ledger_delete
            BEFORE DELETE ON ledger_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_ledger_mutation();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS trg_prevent_ledger_delete ON ledger_entries;")
        op.execute("DROP TRIGGER IF EXISTS trg_prevent_ledger_update ON ledger_entries;")
        op.execute("DROP FUNCTION IF EXISTS prevent_ledger_mutation();")

    op.drop_table('idempotency_keys')
    op.drop_table('ledger_entries')
    op.drop_table('accounts')
    op.drop_table('users')
