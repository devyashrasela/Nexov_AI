"""SQLAlchemy engine and session setup."""

from collections.abc import Generator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import DATABASE_URL, DB_SSL_CA

Base = declarative_base()


def _mysql_url_and_options(url: str) -> tuple[str, dict]:
    """Adapt an Aiven mysql:// URI to SQLAlchemy's PyMySQL dialect."""
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key.lower() != "ssl-mode"]
    rewritten = urlunsplit(
        ("mysql+pymysql", parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
    ssl_options = {"ca": DB_SSL_CA} if DB_SSL_CA else {}
    return rewritten, {"ssl": ssl_options}


if DATABASE_URL:
    engine_url, connect_args = _mysql_url_and_options(DATABASE_URL)
    engine = create_engine(
        engine_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=280,
    )
else:
    engine = create_engine(
        "sqlite:///clinic.db",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
