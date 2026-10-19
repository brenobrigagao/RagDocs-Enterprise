from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings

db_url = str(settings.database_url).replace("postgresql://", "postgresql+psycopg://")

engine = create_engine(
    db_url,
    pool_pre_ping=True,  
    pool_size=10,        
    max_overflow=20,     
    pool_recycle=1800,  
    echo=getattr(settings, "sql_echo", False),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    yield from get_db()