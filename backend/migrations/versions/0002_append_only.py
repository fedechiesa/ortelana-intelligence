"""Enforce immutable decisions, audit and policy versions on PostgreSQL."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
            CREATE FUNCTION prevent_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              RAISE EXCEPTION 'Audit, decisions, reviews and policies are append-only';
            END;
            $$;
        """)
        for table in ("decisions", "audit_events", "policies", "reviews"):
            op.execute(
                f"CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
            )


def downgrade():
    raise RuntimeError("Destructive downgrade disabled")
