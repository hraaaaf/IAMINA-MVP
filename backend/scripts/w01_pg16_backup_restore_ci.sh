#!/usr/bin/env bash
# W01-G6 CI-only backup and restore; synthetic disposable PG16 via localhost.
set -euo pipefail
if [[ "$GITHUB_ACTIONS" != "true" || "$CI" != "true" ]]; then
  echo "W01-G6 BLOCK: CI only" >&2
  exit 2
fi
if [[ "$DATABASE_URL" != "postgresql://postgres:postgres@127.0.0.1:5432/iamina_w01_ci" ]]; then
  echo "W01-G6 BLOCK: unexpected database URL" >&2
  exit 2
fi

source_db=iamina_w01_ci
restore_db=iamina_w01_restore
scratch="$(mktemp -d)"
chmod 755 "$scratch"
trap 'rm -rf "$scratch"' EXIT

pg() {
  docker run --rm --network host --user 0:0 \
    -e PGPASSWORD=postgres -e PGHOST=127.0.0.1 -e PGPORT=5432 -e PGUSER=postgres \
    -v "$scratch:/backup" postgres:16-alpine "$@"
}

version="$(pg psql -d "$source_db" -X -A -t -v ON_ERROR_STOP=1 -c 'SHOW server_version_num')"
[[ "$version" == 16* ]] || { echo "W01-G6 BLOCK: PostgreSQL !=16" >&2; exit 2; }
already="$(pg psql -d postgres -X -A -t -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM pg_database WHERE datname = '$restore_db'")"
[[ "$already" == 0 ]] || { echo "W01-G6 BLOCK: restore target already exists" >&2; exit 2; }

pg psql -d "$source_db" -X -v ON_ERROR_STOP=1 -c \
  "CREATE TABLE public.w01_synthetic_restore_probe (marker text PRIMARY KEY)" >/dev/null
pg psql -d "$source_db" -X -v ON_ERROR_STOP=1 -c \
  "INSERT INTO public.w01_synthetic_restore_probe VALUES ('W01_FAKE_DATA_ONLY')" >/dev/null
before="$(pg psql -d "$source_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT count(*) FROM public.django_migrations")"
[[ "$before" -gt 0 ]] || { echo "W01-G6 BLOCK: missing Django migrations" >&2; exit 2; }

pg pg_dump -d "$source_db" --format=custom --no-owner --no-acl -f /backup/schema.dump
pg createdb "$restore_db"
pg pg_restore -d "$restore_db" --exit-on-error --no-owner --no-acl /backup/schema.dump

after="$(pg psql -d "$restore_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT count(*) FROM public.django_migrations")"
marker="$(pg psql -d "$restore_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT marker FROM public.w01_synthetic_restore_probe")"
[[ "$after" == "$before" && "$marker" == W01_FAKE_DATA_ONLY ]] || {
  echo "W01-G6 FAIL: restore mismatch" >&2; exit 1;
}
pg psql -d "$restore_db" -X -v ON_ERROR_STOP=1 -c \
  "BEGIN; INSERT INTO public.w01_synthetic_restore_probe VALUES ('DO_NOT_PERSIST'); ROLLBACK;" >/dev/null
rolled="$(pg psql -d "$restore_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT count(*) FROM public.w01_synthetic_restore_probe")"
untouched="$(pg psql -d "$source_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT count(*) FROM public.w01_synthetic_restore_probe")"
[[ "$rolled" == 1 && "$untouched" == 1 ]] || {
  echo "W01-G6 FAIL: rollback/source isolation" >&2; exit 1;
}
DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/$restore_db" \
  python manage.py migrate --check --noinput

# Actual Django schema migration reversal on the RESTORED disposable DB, not source.
# 0034 adds five fields; reversing from 0035 to 0033 must remove them,
# and migrating forwards again must restore them. Refuse if any clinical rows exist.
sandbox_url="postgresql://postgres:postgres@127.0.0.1:5432/$restore_db"
clinical_rows="$(pg psql -d "$restore_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT (SELECT count(*) FROM public.diabetes_diabetesprofile) + (SELECT count(*) FROM public.diabetes_logentry)")"
[[ "$clinical_rows" == 0 ]] || {
  echo "W01-G6 BLOCK: refusing migration rollback with clinical rows" >&2
  exit 2
}
fields="'treatment_declaration_state','treatment_declarations','treatment_declaration_version','treatment_declaration_source','treatment_declaration_updated_at'"
column_count() {
  pg psql -d "$1" -X -A -t -v ON_ERROR_STOP=1 \
    -c "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='diabetes_diabetesprofile' AND column_name IN ($fields)"
}
[[ "$(column_count "$restore_db")" == 5 ]] || {
  echo "W01-G6 BLOCK: expected five migration-0034 fields" >&2
  exit 2
}
DATABASE_URL="$sandbox_url" python manage.py migrate diabetes 0033_logentry_meal_episode_id --noinput
[[ "$(column_count "$restore_db")" == 0 ]] || {
  echo "W01-G6 FAIL: Django 0034 downgrade did not remove five synthetic schema fields" >&2
  exit 1
}
DATABASE_URL="$sandbox_url" python manage.py migrate diabetes --noinput
[[ "$(column_count "$restore_db")" == 5 ]] || {
  echo "W01-G6 FAIL: forward migration did not restore five fields" >&2
  exit 1
}
DATABASE_URL="$sandbox_url" python manage.py migrate --check --noinput
[[ "$(column_count "$source_db")" == 5 ]] || {
  echo "W01-G6 FAIL: source schema was unexpectedly altered" >&2
  exit 1
}
final_marker="$(pg psql -d "$restore_db" -X -A -t -v ON_ERROR_STOP=1 -c \
  "SELECT marker FROM public.w01_synthetic_restore_probe")"
[[ "$final_marker" == W01_FAKE_DATA_ONLY ]] || {
  echo "W01-G6 FAIL: synthetic canary changed during migration rollback" >&2
  exit 1
}
echo "PASS W01-G6 disposable PG16 Django migration 0034 DOWN to 0033 and UP to 0035; source unchanged."
echo "PASS W01-G6 disposable PG16: migrated schema dump/restore, synthetic marker, transaction rollback."
echo "LIMIT: no real hosted Neon backup, production migration downgrade or patient-production release proof."
