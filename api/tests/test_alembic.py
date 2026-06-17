from pathlib import Path
from typing import Final

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from api.app.settings import get_settings

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]


def test_upgrade_head_records_baseline_revision_on_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path: Path = tmp_path / "migrate.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()

    config: Config = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    get_settings.cache_clear()

    engine: Engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        revision: str | None = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar()
    engine.dispose()

    assert revision == "0001_baseline"
