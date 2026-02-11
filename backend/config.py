import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FrontWall"
    app_version: str = "0.1.0"

    secret_key: str = ""
    admin_port: int = 8000
    shield_port: int = 8080
    log_level: str = "info"

    data_dir: Path = Path("/app/data")
    cache_dir: Path = Path("/app/data/cache")
    db_url: str = "sqlite+aiosqlite:///app/data/frontwall.db"

    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: str = "strict"
    cookie_domain: str | None = None

    crawler_max_concurrency: int = 5
    crawler_delay_seconds: float = 0.5
    crawler_timeout_seconds: int = 30
    crawler_max_pages: int = 10000

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    max_request_size_bytes: int = 1_048_576

    model_config = {"env_prefix": "WS_"}

    def setup_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    import secrets
    data_dir = os.environ.get("WS_DATA_DIR", str(Path(__file__).parent.parent / "data"))
    defaults: dict = {}
    data_path = Path(data_dir)
    defaults["data_dir"] = data_path
    defaults["cache_dir"] = data_path / "cache"
    defaults["db_url"] = f"sqlite+aiosqlite:///{data_path / 'frontwall.db'}"

    instance = Settings(**defaults)

    if not instance.secret_key:
        secret_file = data_path / ".secret_key"
        if secret_file.exists():
            instance.secret_key = secret_file.read_text().strip()
        else:
            data_path.mkdir(parents=True, exist_ok=True)
            generated = secrets.token_urlsafe(64)
            secret_file.write_text(generated)
            secret_file.chmod(0o600)
            instance.secret_key = generated

    return instance


settings = get_settings()
