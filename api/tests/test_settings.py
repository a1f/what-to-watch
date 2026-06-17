import pytest

from api.app.settings import Settings, get_settings


def test_database_url_is_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/wtw")
    get_settings.cache_clear()

    settings: Settings = get_settings()

    assert (
        settings.database_url.get_secret_value()
        == "postgresql+psycopg://u:p@db:5432/wtw"
    )
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (
            "postgresql://postgres:postgres@localhost:5432/wtw",
            "postgresql+psycopg://postgres:postgres@localhost:5432/wtw",
        ),
        (
            "postgres://postgres:postgres@localhost:5432/wtw",
            "postgresql+psycopg://postgres:postgres@localhost:5432/wtw",
        ),
        ("sqlite:///./local.db", "sqlite:///./local.db"),
    ],
)
def test_database_url_uses_psycopg_driver_for_postgres_schemes(
    configured: str, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", configured)
    get_settings.cache_clear()

    settings: Settings = get_settings()

    assert settings.database_url.get_secret_value() == expected
    get_settings.cache_clear()
