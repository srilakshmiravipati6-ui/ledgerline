-- ============================================================================
-- BalanceVault PostgreSQL Least-Privilege Database Roles Setup
-- ============================================================================
-- Execute this script as a PostgreSQL Superuser (e.g. 'postgres') when
-- provisioning the production database.
--
-- Roles Defined:
--   1. migration_user: Schema administrator for running Alembic migrations.
--   2. app_user: Runtime application connection (DML only, NO DELETE on ledger).
--   3. auditor_user: Read-only access for compliance, auditors, and reporting.
-- ============================================================================

-- Step 1: Create Database (if not exists)
-- CREATE DATABASE balancevault;
-- \c balancevault;

-- Step 2: Create Roles with Secure Passwords
-- (Replace passwords before running in production!)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'migration_user') THEN
        CREATE ROLE migration_user WITH LOGIN PASSWORD 'change_this_migration_password_123!';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'change_this_app_password_123!';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'auditor_user') THEN
        CREATE ROLE auditor_user WITH LOGIN PASSWORD 'change_this_auditor_password_123!';
    END IF;
END
$$;

-- Step 3: Grant Schema Permissions
GRANT USAGE, CREATE ON SCHEMA public TO migration_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT USAGE ON SCHEMA public TO auditor_user;

-- Step 4: Configure Permissions for 'migration_user' (DDL + Full Control)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO migration_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO migration_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO migration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO migration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO migration_user;

-- Step 5: Configure Permissions for 'app_user' (Least Privilege Runtime)
-- Table Grants:
GRANT SELECT, INSERT, UPDATE ON TABLE users TO app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE accounts TO app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE idempotency_keys TO app_user;

-- CRITICAL AUDIT RULE:
-- app_user may SELECT and INSERT into ledger_entries, but MUST NOT UPDATE or DELETE!
GRANT SELECT, INSERT ON TABLE ledger_entries TO app_user;
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE ledger_entries FROM app_user;

-- Sequence Grants (needed for serial primary keys):
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Default privileges for future tables created by migration_user:
ALTER DEFAULT PRIVILEGES FOR ROLE migration_user IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE migration_user IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;

-- Step 6: Configure Permissions for 'auditor_user' (Strictly Read-Only)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO auditor_user;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM auditor_user;

-- Default privileges for future tables:
ALTER DEFAULT PRIVILEGES FOR ROLE migration_user IN SCHEMA public
    GRANT SELECT ON TABLES TO auditor_user;

-- ============================================================================
-- Verification Queries (Run to confirm):
-- ============================================================================
-- SELECT grantee, table_name, privilege_type 
-- FROM information_schema.role_table_grants 
-- WHERE grantee IN ('migration_user', 'app_user', 'auditor_user')
-- ORDER BY grantee, table_name;

