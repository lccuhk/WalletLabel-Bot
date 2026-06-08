"""
数据库配置
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from pathlib import Path

from config import settings

data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)
labels_dir = data_dir / "labels"
labels_dir.mkdir(exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.LOG_LEVEL == "DEBUG"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import user, address_cache
    Base.metadata.create_all(bind=engine)
