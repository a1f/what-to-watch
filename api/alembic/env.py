from alembic import context
from sqlalchemy import engine_from_config, pool

from api.app.settings import get_settings

# The URL comes from application settings, never from alembic.ini, so migrations
# and the running app always agree on which database they target.
config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url.get_secret_value())

# No ORM models yet (the baseline defines no tables); autogenerate is wired later.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
