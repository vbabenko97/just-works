-- Run with psql variables, for example:
-- psql -d app -v db_name=app -v schema_name=analytics -v role_name=analytics_agent_readonly \
--   -v login_role=analytics_agent_login -v owner_role=app_migrator \
--   -f readonly_role.sql
-- psql performs variable substitution before sending SQL.  The identifier variables
-- below are quoted with :"name" and must be supplied by a trusted operator.
--
-- This creates a NOLOGIN group role and grants it to an existing dedicated login or
-- RDS IAM database role.  Do not give the login role direct table privileges.

\set ON_ERROR_STOP on

\if :{?db_name}
\else
SELECT 1 / 0;
\endif
\if :{?schema_name}
\else
SELECT 1 / 0;
\endif
\if :{?role_name}
\else
SELECT 1 / 0;
\endif
\if :{?login_role}
\else
SELECT 1 / 0;
\endif
\if :{?owner_role}
\else
SELECT 1 / 0;
\endif

SELECT current_database() = :'db_name' AS correct_database
\gset
\if :correct_database
\else
SELECT 1 / 0;
\endif

BEGIN;

SELECT
    NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role_name') AS role_missing,
    EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = :'role_name'
          AND (rolcanlogin OR rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
    ) AS role_unsafe,
    NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'login_role') AS login_missing,
    EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = :'login_role'
          AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
    ) AS login_unsafe
\gset
\if :role_unsafe
SELECT 1 / 0;
\endif
\if :login_missing
SELECT 1 / 0;
\endif
\if :login_unsafe
SELECT 1 / 0;
\endif

SELECT format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT NOBYPASSRLS', :'role_name')
WHERE :'role_missing' = 't'
\gexec

GRANT CONNECT ON DATABASE :"db_name" TO :"role_name";
GRANT USAGE ON SCHEMA :"schema_name" TO :"role_name";
GRANT SELECT ON ALL TABLES IN SCHEMA :"schema_name" TO :"role_name";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_role" IN SCHEMA :"schema_name" GRANT SELECT ON TABLES TO :"role_name";
GRANT :"role_name" TO :"login_role";

-- Settings belong to the actual login role: role settings on a NOLOGIN group do
-- not automatically apply to a member's session.
ALTER ROLE :"login_role" SET default_transaction_read_only = on;
ALTER ROLE :"login_role" SET statement_timeout = '15s';
ALTER ROLE :"login_role" SET lock_timeout = '2s';
ALTER ROLE :"login_role" SET idle_in_transaction_session_timeout = '30s';

COMMIT;

-- This script intentionally does not revoke PUBLIC privileges.  Such revokes change
-- shared database behaviour and must be reviewed for the target database separately.
