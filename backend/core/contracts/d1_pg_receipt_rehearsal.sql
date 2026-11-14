-- D1 PostgreSQL 16 CI-ONLY schema. Never apply to patient/production DB.
-- There is deliberately NO Django migration, URL, background task or role grant.
-- This is a disposable laboratory for signed-receipt verification and replay.
CREATE SCHEMA IF NOT EXISTS d1_receipt_ci;

CREATE TABLE IF NOT EXISTS d1_receipt_ci.public_keys (
    kid text PRIMARY KEY,
    public_raw bytea NOT NULL CHECK (octet_length(public_raw) = 32),
    status text NOT NULL CHECK (status IN ('active', 'verify', 'revoked')),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS d1_receipt_ci_one_active
  ON d1_receipt_ci.public_keys(status) WHERE status='active';

CREATE TABLE IF NOT EXISTS d1_receipt_ci.nonces_consumed (
    issuer text NOT NULL CHECK (issuer='iamina-d1-ci-synthetic-only'),
    nonce text NOT NULL CHECK (nonce ~ '^[0-9a-f]{32}$'),
    kid text NOT NULL REFERENCES d1_receipt_ci.public_keys(kid),
    consumed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (issuer, nonce)
);

CREATE TABLE IF NOT EXISTS d1_receipt_ci.audit_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event text NOT NULL CHECK (
      event IN ('SYNTHETIC_KEY_ACTIVATED',
                'SYNTHETIC_KEY_REVOKED',
                'SYNTHETIC_RECEIPT_CONSUMED')
    ),
    kid text NOT NULL,
    nonce_sha256 text,
    happened_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT d1_audit_nonce_hash_shape
      CHECK (nonce_sha256 IS NULL OR nonce_sha256 ~ '^[0-9a-f]{64}$')
);

-- Ordinary UPDATE/DELETE are forbidden even for the CI DB owner.
-- Schema owners can still disable triggers: production needs separate roles,
-- append-only privileges, separate tamper-evident audit, PITR and monitoring.
CREATE OR REPLACE FUNCTION d1_receipt_ci.deny_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'D1_CI_APPEND_ONLY_REQUIRED';
END $$;

DROP TRIGGER IF EXISTS d1_nonces_append_only ON d1_receipt_ci.nonces_consumed;
CREATE TRIGGER d1_nonces_append_only
  BEFORE UPDATE OR DELETE ON d1_receipt_ci.nonces_consumed
  FOR EACH ROW EXECUTE FUNCTION d1_receipt_ci.deny_mutation();

DROP TRIGGER IF EXISTS d1_audit_append_only ON d1_receipt_ci.audit_events;
CREATE TRIGGER d1_audit_append_only
  BEFORE UPDATE OR DELETE ON d1_receipt_ci.audit_events
  FOR EACH ROW EXECUTE FUNCTION d1_receipt_ci.deny_mutation();
