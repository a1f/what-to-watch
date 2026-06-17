from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from api.app.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Single lazily-built engine so importing the app never opens a connection."""
    return create_engine(get_settings().database_url.get_secret_value())


def check_connection(engine: Engine) -> bool:
    """Whether a trivial read-only probe against the database succeeds."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True
