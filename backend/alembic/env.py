from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config import settings
from src.db.metadata import target_metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def include_object(object_, name, type_, reflected, compare_to):
    """Keep autogenerate additive and safe for the migration-first legacy schema.

    Several mature tables have indexes/checks expressed in historical migrations
    rather than ORM classes. Never interpret that as permission to remove them.
    New tables and new columns declared in metadata are still detected.
    """
    if reflected and compare_to is None:
        return False
    if type_ in {"index", "unique_constraint", "foreign_key_constraint", "check_constraint"}:
        return False
    if type_ == "column" and compare_to is not None:
        return False
    return True

def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=False,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=False,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
