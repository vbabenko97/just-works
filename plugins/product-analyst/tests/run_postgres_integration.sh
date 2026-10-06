#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
plugin_dir="$(cd "$script_dir/.." && pwd)"
cd "$plugin_dir"
uv_bin="${UV_BIN:-uv}"
if [[ "$uv_bin" == */* && ! -x "$uv_bin" ]]; then
  echo "UV_BIN is not executable: $uv_bin" >&2
  exit 2
fi
if [[ "$uv_bin" != */* ]] && ! command -v "$uv_bin" >/dev/null; then
  echo "uv was not found; set UV_BIN to its absolute path" >&2
  exit 2
fi

container="product-analyst-pg-test-$$"
service_file="$(mktemp)"
cleanup() {
  docker stop "$container" >/dev/null 2>&1 || true
  rm -f "$service_file"
}
trap cleanup EXIT

docker run --rm -d --name "$container" -e POSTGRES_PASSWORD=postgres -p 127.0.0.1::5432 postgres:16-alpine >/dev/null
for _ in $(seq 1 60); do
  if docker exec "$container" pg_isready -U postgres -d postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$container" pg_isready -U postgres -d postgres >/dev/null
port="$(docker port "$container" 5432/tcp | sed -E 's/.*:([0-9]+)$/\1/')"

docker exec -i "$container" psql -v ON_ERROR_STOP=1 -U postgres -d postgres <<'SQL'
CREATE SCHEMA analytics;
CREATE TABLE analytics.events (id integer PRIMARY KEY, name text NOT NULL);
INSERT INTO analytics.events VALUES (1, 'one'), (2, 'two'), (3, 'three');
CREATE SCHEMA private_data;
CREATE TABLE private_data.secret (id integer PRIMARY KEY);
INSERT INTO private_data.secret VALUES (1);
CREATE ROLE analyst_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'reader';
CREATE ROLE analyst_overgrant LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'overgrant';
CREATE ROLE analyst_bypass LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION BYPASSRLS PASSWORD 'bypass';
CREATE ROLE analyst_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'owner';
CREATE ROLE analyst_column_writer LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'column';
CREATE ROLE analyst_sequence_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'sequence';
CREATE ROLE app_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD 'migrator';
CREATE ROLE unsafe_group NOLOGIN SUPERUSER;
GRANT USAGE ON SCHEMA private_data TO analyst_overgrant;
GRANT SELECT ON private_data.secret TO analyst_overgrant;
CREATE TABLE analytics.owned (id integer PRIMARY KEY);
ALTER TABLE analytics.owned OWNER TO analyst_owner;
GRANT UPDATE (name) ON analytics.events TO analyst_column_writer;
CREATE SEQUENCE analytics.agent_sequence;
GRANT USAGE ON SEQUENCE analytics.agent_sequence TO analyst_sequence_user;
GRANT USAGE, CREATE ON SCHEMA analytics TO app_migrator;
CREATE ROLE analyst_unsafe LOGIN SUPERUSER PASSWORD 'unsafe';
SQL
docker cp setup/readonly_role.sql "$container:/tmp/readonly_role.sql"
if docker exec "$container" psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -v db_name=wrong_database -v schema_name=analytics -v role_name=should_not_exist \
  -v login_role=analyst_reader -v owner_role=app_migrator -f /tmp/readonly_role.sql; then
  echo "readonly_role.sql accepted a database name other than the connected database" >&2
  exit 1
fi
docker exec "$container" psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -v db_name=postgres -v schema_name=analytics -v role_name=analyst_group \
  -v login_role=analyst_reader -v owner_role=app_migrator -f /tmp/readonly_role.sql
docker exec -i "$container" psql -v ON_ERROR_STOP=1 -U postgres -d postgres <<'SQL'
GRANT analyst_group TO analyst_overgrant;
GRANT analyst_group TO analyst_bypass;
GRANT analyst_group TO analyst_owner;
GRANT analyst_group TO analyst_column_writer;
GRANT analyst_group TO analyst_sequence_user;
SET ROLE app_migrator;
CREATE TABLE analytics.future_events (id integer PRIMARY KEY);
INSERT INTO analytics.future_events VALUES (1);
SQL
if docker exec "$container" psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -v db_name=postgres -v schema_name=analytics -v role_name=unsafe_group \
  -v login_role=analyst_reader -v owner_role=app_migrator -f /tmp/readonly_role.sql; then
  echo "readonly_role.sql accepted an unsafe existing role" >&2
  exit 1
fi

cat >"$service_file" <<EOF
[analyst]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_reader
password=reader

[unsafe]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_unsafe
password=unsafe

[overgrant]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_overgrant
password=overgrant

[bypass]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_bypass
password=bypass

[owner]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_owner
password=owner

[column_writer]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_column_writer
password=column

[sequence_user]
host=127.0.0.1
port=$port
dbname=postgres
user=analyst_sequence_user
password=sequence
EOF

PGSERVICEFILE="$service_file" ANALYST_TEST_SERVICE=analyst \
  "$uv_bin" run --no-project --with 'psycopg[binary]>=3.2,<4' python tests/test_postgres_integration.py
