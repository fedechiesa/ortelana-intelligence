#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=reader_password="$GRAFANA_DB_PASSWORD" --set=app_password="$APP_DATABASE_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE ortelana LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L', :'app_password') \gexec
ALTER DATABASE ortelana OWNER TO ortelana;
GRANT USAGE, CREATE ON SCHEMA public TO ortelana;
SELECT format('CREATE ROLE grafana_reader LOGIN PASSWORD %L', :'reader_password') \gexec
GRANT CONNECT ON DATABASE ortelana TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE ortelana IN SCHEMA public GRANT SELECT ON TABLES TO grafana_reader;
CREATE DATABASE ortelana_test OWNER ortelana;
SQL
