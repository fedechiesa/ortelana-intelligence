from alembic import context
from app.core.config import Settings
from app.repositories.models import Base
from sqlalchemy import create_engine, pool

config = context.config
url = Settings().database_url
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 5} if url.startswith("postgresql") else {},
    )
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
