"""Protect evidence snapshots and enforce committed decisions at transaction boundaries."""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("""
        CREATE FUNCTION protect_execution_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.request::jsonb IS DISTINCT FROM NEW.request::jsonb
             OR OLD.policy::jsonb IS DISTINCT FROM NEW.policy::jsonb
             OR OLD.dataset_id IS DISTINCT FROM NEW.dataset_id
             OR OLD.thread_id IS DISTINCT FROM NEW.thread_id
             OR OLD.idempotency_key IS DISTINCT FROM NEW.idempotency_key
             OR OLD.request_hash IS DISTINCT FROM NEW.request_hash THEN
            RAISE EXCEPTION 'Execution input and policy snapshots are immutable';
          END IF;
          IF OLD.result::jsonb <> '{}'::jsonb AND
             (OLD.result::jsonb IS DISTINCT FROM NEW.result::jsonb
              OR OLD.business_status IS DISTINCT FROM NEW.business_status) THEN
            RAISE EXCEPTION 'Persisted commercial evidence is immutable';
          END IF;
          IF OLD.approval_status IN ('APPROVED','REJECTED')
             AND OLD.approval_status <> NEW.approval_status THEN
            RAISE EXCEPTION 'A definitive decision cannot change';
          END IF;
          RETURN NEW;
        END;
        $$;
        CREATE TRIGGER immutable_evidence BEFORE UPDATE ON executions
          FOR EACH ROW EXECUTE FUNCTION protect_execution_evidence();
    """)
    op.execute("""
        CREATE FUNCTION require_committed_decision() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE approval text; risk text; human_decision text;
        BEGIN
          SELECT approval_status,business_status INTO approval,risk FROM executions WHERE id=NEW.id;
          IF approval IN ('APPROVED','REJECTED') THEN
            SELECT decision INTO human_decision FROM decisions WHERE execution_id=NEW.id;
            IF risk IS DISTINCT FROM 'CRITICO' OR human_decision IS NULL
              OR (approval='APPROVED' AND human_decision <> 'APROBADO')
              OR (approval='REJECTED' AND human_decision <> 'RECHAZADO') THEN
              RAISE EXCEPTION 'A matching committed critical review decision is required';
            END IF;
          END IF;
          IF risk='CRITICO' AND approval='NOT_REQUIRED' THEN
            RAISE EXCEPTION 'Critical recommendations require human review';
          END IF;
          RETURN NULL;
        END;
        $$;
        CREATE CONSTRAINT TRIGGER committed_human_authority
          AFTER INSERT OR UPDATE ON executions DEFERRABLE INITIALLY DEFERRED
          FOR EACH ROW EXECUTE FUNCTION require_committed_decision();
    """)


def downgrade():
    raise RuntimeError("Destructive downgrade disabled")
