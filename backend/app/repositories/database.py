from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def make_database(url: str):
    options: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 20}
    else:
        options["connect_args"] = {"connect_timeout": 5, "options": "-c statement_timeout=15000"}
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return engine, sessionmaker(engine, expire_on_commit=False)
